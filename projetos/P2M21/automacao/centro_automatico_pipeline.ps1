$ErrorActionPreference='Stop'
$taskRoot='D:/dev/EMBRAER/P2M21/R04_Centro_Classic'
$env:P2M21_UNIFORME=$taskRoot
$env:P2M21_ETAPA='centro'
$taskPython='C:/Users/geral/AppData/Local/Programs/Python/Python312/python.exe'
function Estado([string]$phase,$detail) {
    @{estado=$phase;detalhe=$detail;instante=(Get-Date -Format o);processo_pipeline=$PID;frequencia_GHz=5.17;max_passes=6;delta_s=.04;sweeps=0} |
      ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$taskRoot/qualificacao.json" -Encoding utf8
}
function Verificar([string]$phase) {
    $ErrorActionPreference='Continue'
    & $taskPython (Join-Path $PSScriptRoot 'centro_automatico_verificar.py') $phase 2>&1 | Out-File -LiteralPath "$taskRoot/pipeline.log" -Append -Encoding utf8
    $taskCode=$LASTEXITCODE;$ErrorActionPreference='Stop'
    if($taskCode -ne 0) {throw "Auditoria falhou em $phase; ver pipeline.log"}
}
try {
    if(Test-Path -LiteralPath "$taskRoot/pipeline_iniciado.json") {throw 'Fila de centro ja iniciada; nao duplicar.'}
    Verificar 'preparacao'
    @{processo=$PID;instante=(Get-Date -Format o)} | ConvertTo-Json | Set-Content -LiteralPath "$taskRoot/pipeline_iniciado.json" -Encoding utf8
    $taskScript=Join-Path $PSScriptRoot 'uniforme_resolver.py'
    $taskProcess=Start-Process -FilePath 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe' -WindowStyle Hidden -PassThru -ArgumentList @('-ng','-LogFile',('"'+$taskRoot+'/centro_aedt.log"'),'-RunScriptAndExit',('"'+$taskScript+'"'))
    Estado 'CENTRO_EM_EXECUCAO' @{processo_aedt=$taskProcess.Id;sem_refinamento_inicial=$true;base='Mixed Order'}
    $taskProcess.WaitForExit()
    if($taskProcess.ExitCode -ne 0 -or (Get-Content -LiteralPath "$taskRoot/antena/centro.log" -Tail 1) -ne 'CENTRO_UNIFORME_OK') {throw 'Calculo central nao terminou normalmente.'}
    Verificar 'centro'
    Estado 'CENTRO_CONCLUIDO_REVISAR' 'Somente 5.17GHz; revisar ganho e diagramas. Nenhum sweep.'
} catch {
    Estado 'REQUER_VERIFICACAO' $_.Exception.Message
    $_ | Out-String | Out-File -LiteralPath "$taskRoot/pipeline.log" -Append -Encoding utf8
    exit 1
}
