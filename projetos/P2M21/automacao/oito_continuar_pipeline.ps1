$ErrorActionPreference='Stop'
$root='D:/dev/EMBRAER/P2M21/R15_Oito_Celulas_8passes'
function State([string]$s){[pscustomobject]@{estado=$s;pipeline_pid=$PID;atualizado=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content "$root/pipeline.json" -Encoding utf8}
try{
    foreach($stage in @('preparar','centro')){
        if(Get-Process hf3d,G3dMesher -ErrorAction SilentlyContinue){throw 'Outro solve ativo'}
        State $stage
        $env:P2M21_OITO_ETAPA=$stage
        $script=Join-Path $PSScriptRoot 'oito_continuar_aedt.py'
        $p=Start-Process 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe' -ArgumentList @('-ng','-LogFile',"$root/${stage}_aedt.log",'-RunScriptAndExit',$script) -WindowStyle Hidden -PassThru
        [pscustomobject]@{pid=$p.Id;script=$script;etapa=$stage;inicio=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content "$root/processo_$stage.json" -Encoding utf8
        $p.WaitForExit()
        if($p.ExitCode -ne 0){throw "AEDT exit $($p.ExitCode)"}
        & python (Join-Path $PSScriptRoot 'oito_continuar_auditar.py') $stage *> "$root/auditoria_$stage.log"
        if($LASTEXITCODE -ne 0){throw "Falha auditoria $stage"}
    }
    State 'ANALISANDO'
    $env:P2M21_OITO_ROOT=$root
    & python (Join-Path $PSScriptRoot 'oito_celulas_analisar.py') *> "$root/analise.log"
    if($LASTEXITCODE -ne 0){throw 'Falha analise'}
    State 'CONCLUIDO_AGUARDA_REVISAO'
}catch{
    [pscustomobject]@{estado='REQUER_VERIFICACAO';erro=$_.ToString();pipeline_pid=$PID;atualizado=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content "$root/pipeline.json" -Encoding utf8
    throw
}
