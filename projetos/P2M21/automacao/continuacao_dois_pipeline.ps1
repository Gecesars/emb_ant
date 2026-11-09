$ErrorActionPreference='Stop'
$taskRoot='D:/dev/EMBRAER/P2M21/R04_Centro_Classic'
$env:P2M21_UNIFORME=$taskRoot; $env:P2M21_ETAPA='centro'
$taskPython='C:/Users/geral/AppData/Local/Programs/Python/Python312/python.exe'
function Estado([string]$state,$detail){
    @{estado=$state;detalhe=$detail;instante=(Get-Date -Format o);processo_pipeline=$PID;max_passes=6;min_passes=6;nucleos=14;frequencia_GHz=5.17;sweeps=0} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath "$taskRoot/qualificacao.json" -Encoding utf8
}
function ExecutarAedt([string]$script,[string]$log){
    $task=Start-Process -FilePath 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe' -WindowStyle Hidden -PassThru -ArgumentList @('-ng','-LogFile',('"'+$taskRoot+'/'+$log+'"'),'-RunScriptAndExit',('"'+(Join-Path $PSScriptRoot $script)+'"'))
    Estado 'CONTINUACAO_EM_EXECUCAO' @{processo_aedt=$task.Id;script=$script}
    $task.WaitForExit(); if($task.ExitCode -ne 0){throw "AEDT falhou: $script"}
}
function Verificar([string]$stage){
    $ErrorActionPreference='Continue'
    & $taskPython (Join-Path $PSScriptRoot 'continuacao_dois_verificar.py') $stage 2>&1 | Out-File -LiteralPath "$taskRoot/continuacao_pipeline.log" -Append -Encoding utf8
    $code=$LASTEXITCODE; $ErrorActionPreference='Stop'; if($code -ne 0){throw "Auditoria falhou: $stage"}
}
try{
    if(Test-Path -LiteralPath "$taskRoot/continuacao_iniciada.json"){throw 'Continuacao ja iniciada; nao duplicar.'}
    @{processo=$PID;instante=(Get-Date -Format o)} | ConvertTo-Json | Set-Content -LiteralPath "$taskRoot/continuacao_iniciada.json" -Encoding utf8
    ExecutarAedt 'continuacao_dois_preparar.py' 'continuacao_preparacao_aedt.log'
    if((Get-Content -LiteralPath "$taskRoot/continuacao_preparacao.log" -Tail 1) -ne 'CONTINUACAO_5_E_6_PREPARADA'){throw 'Preparacao incompleta'}
    Verificar 'preparacao'
    ExecutarAedt 'uniforme_resolver.py' 'centro_6passes_aedt.log'
    if((Get-Content -LiteralPath "$taskRoot/antena/centro.log" -Tail 1) -ne 'CENTRO_UNIFORME_OK'){throw 'Solver/exportacao incompletos'}
    Verificar 'centro'
    Estado 'SEIS_PASSES_CONCLUIDOS_REVISAR_E_ENVIAR' 'Gerar e revisar dois diagramas polares E/Emax, atualizar valores e enviar email autorizado.'
}catch{
    Estado 'REQUER_VERIFICACAO' $_.Exception.Message
    $_ | Out-String | Out-File -LiteralPath "$taskRoot/continuacao_pipeline.log" -Append -Encoding utf8
    exit 1
}
