param([int]$CriacaoPID)
$ErrorActionPreference='Stop'
$root='D:/dev/EMBRAER/P2M21/R14_Oito_Celulas'
function State([string]$Status){
    [pscustomobject]@{estado=$Status;atualizado=(Get-Date).ToString('o');pipeline_pid=$PID} | ConvertTo-Json | Set-Content "$root/pipeline.json" -Encoding utf8
}
try{
    State 'AGUARDANDO_CRIACAO_HFSS'
    if($CriacaoPID){
        $p=Get-CimInstance Win32_Process -Filter "ProcessId=$CriacaoPID"
        if($p){
            if($p.Name -ne 'ansysedt.exe' -or $p.CommandLine -notmatch 'oito_celulas_hfss.py'){throw 'PID nao pertence a criacao R14'}
            Wait-Process -Id $CriacaoPID
        }
    }
    $v=Get-Content -Raw "$root/hfss_validacao.json" | ConvertFrom-Json
    if($v.validacao -ne 1 -or $v.erros.Count -ne 0 -or $v.portas -ne 16){throw 'HFSS nao validado'}
    if(Test-Path "$root/convergencia.txt"){throw 'Resultado existe; nao duplicar'}
    if(Get-Process hf3d,G3dMesher -ErrorAction SilentlyContinue){throw 'Outro solve ativo; serializar'}
    State 'RESOLVENDO_CENTRO'
    $script=Join-Path $PSScriptRoot 'oito_celulas_resolver.py'
    $p=Start-Process -FilePath 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe' -ArgumentList @('-ng','-LogFile',"$root/centro_aedt.log",'-RunScriptAndExit',$script) -WindowStyle Hidden -PassThru
    [pscustomobject]@{pid=$p.Id;script=$script;inicio=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content "$root/resolver_processo.json" -Encoding utf8
    $p.WaitForExit()
    if($p.ExitCode -ne 0){throw "AEDT codigo $($p.ExitCode)"}
    State 'AUDITANDO'
    & python (Join-Path $PSScriptRoot 'oito_celulas_analisar.py') *> "$root/analise.log"
    if($LASTEXITCODE -ne 0){throw 'Falha na auditoria; consultar analise.log'}
    State 'CONCLUIDO_AGUARDA_REVISAO'
}catch{
    [pscustomobject]@{estado='REQUER_VERIFICACAO';erro=$_.ToString();atualizado=(Get-Date).ToString('o');pipeline_pid=$PID} | ConvertTo-Json | Set-Content "$root/pipeline.json" -Encoding utf8
    throw
}
