$ErrorActionPreference='Stop'
$root='D:/dev/EMBRAER/P2S13/R03_Continuacao_M00'
$env:P2S13_ROOT=$root
function State([string]$s){[pscustomobject]@{estado=$s;pipeline_pid=$PID;atualizado=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content "$root/pipeline.json" -Encoding utf8}
function Native([string]$stage){
    if(Get-Process hf3d,G3dMesher -ErrorAction SilentlyContinue){throw 'Outro solver ativo'}
    $env:P2S13_ETAPA=$stage
    $p=Start-Process 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe' -ArgumentList @('-ng','-LogFile',"$root/${stage}_aedt.log",'-RunScriptAndExit',(Join-Path $PSScriptRoot 'continuar2_aedt.py')) -WindowStyle Hidden -PassThru
    [pscustomobject]@{pid=$p.Id;etapa=$stage;inicio=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content "$root/processo_$stage.json" -Encoding utf8
    $p.WaitForExit();if($p.ExitCode -ne 0){throw "AEDT $stage terminou com $($p.ExitCode)"}
}
try{
    if(Test-Path "$root/convergencia.txt"){throw 'Continuacao finalizada; nao duplicar'}
    if(Test-Path "$root/preparacao_auditada.json"){throw 'Preparacao existente; consultar estado antes de retomar'}
    State 'AJUSTANDO_LIMITE_SEM_RESET';Native 'preparar'
    & python (Join-Path $PSScriptRoot 'continuar2_auditar.py') preparar *> "$root/auditoria_preparacao.log"
    if($LASTEXITCODE -ne 0){throw 'Preparacao nao preservou setup/malha; nao iniciar solver'}
    State 'RESOLVENDO_PASSES7_E8';Native 'centro'
    $state=Get-Content -Raw "$root/qualificacao.json"|ConvertFrom-Json
    if($state.estado -ne 'SOLVE_EXPORTADO_AGUARDA_AUDITORIA'){throw 'Campos nao exportados'}
    & python (Join-Path $PSScriptRoot 'continuar2_auditar.py') final *> "$root/auditoria_continuidade.log"
    if($LASTEXITCODE -ne 0){throw 'Historico/continuidade nao conferem'}
    State 'ANALISANDO'
    & python (Join-Path $PSScriptRoot 'analisar.py') *> "$root/analise.log"
    if($LASTEXITCODE -ne 0){throw 'Analise falhou; conferir analise.log'}
    State 'CONCLUIDO_AGUARDA_COMPARACAO'
}catch{
    [pscustomobject]@{estado='REQUER_VERIFICACAO';erro=$_.ToString();pipeline_pid=$PID;atualizado=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content "$root/pipeline.json" -Encoding utf8
    throw
}
