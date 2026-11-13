$ErrorActionPreference='Stop'
$root='D:/dev/EMBRAER/P2M19/R01_16x2_88mm'
function State([string]$value) {
    [pscustomobject]@{estado=$value;pipeline_pid=$PID;atualizado=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content "$root/pipeline.json" -Encoding utf8
}
function Native([string]$script,[string]$stage) {
    if(Get-Process hf3d,G3dMesher -ErrorAction SilentlyContinue){throw 'Outro solver ativo; não executar em paralelo'}
    $p=Start-Process 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe' -ArgumentList @('-ng','-LogFile',"$root/${stage}_aedt.log",'-RunScriptAndExit',(Join-Path $PSScriptRoot $script)) -WindowStyle Hidden -PassThru
    [pscustomobject]@{pid=$p.Id;script=$script;inicio=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content "$root/processo_$stage.json" -Encoding utf8
    $p.WaitForExit()
    if($p.ExitCode -ne 0){throw "AEDT $stage encerrou com código $($p.ExitCode)"}
}
try {
    if(Test-Path "$root/convergencia.txt"){throw 'Resultado existente; não duplicar execução'}
    $cad=Get-Content -Raw "$root/cad/intersecoes.json" | ConvertFrom-Json
    if(!$cad.aprovado){throw 'CAD não aprovado'}
    State 'CRIANDO_HFSS'
    Native 'criar_hfss.py' 'criacao'
    $valid=Get-Content -Raw "$root/hfss_validacao.json" | ConvertFrom-Json
    if($valid.validacao -ne 1 -or $valid.erros.Count -ne 0 -or $valid.portas -ne 16){throw 'Modelo HFSS não validado'}
    State 'RESOLVENDO_CENTRO_6PASSES'
    Native 'resolver.py' 'centro'
    State 'ANALISANDO'
    & python (Join-Path $PSScriptRoot 'analisar.py') *> "$root/analise.log"
    if($LASTEXITCODE -ne 0){throw 'Falha na auditoria; verificar analise.log'}
    State 'CONCLUIDO_AGUARDA_REVISAO'
} catch {
    [pscustomobject]@{estado='REQUER_VERIFICACAO';erro=$_.ToString();pipeline_pid=$PID;atualizado=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content "$root/pipeline.json" -Encoding utf8
    throw
}
