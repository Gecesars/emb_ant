param([switch]$Retomar14,[switch]$RetomarLimite4,[int]$AguardarAedt=0)
$ErrorActionPreference='Stop'
$taskRoot='D:/dev/EMBRAER/P2M21/R04_Centro_Classic'
$env:P2M21_UNIFORME=$taskRoot
$env:P2M21_ETAPA='centro'
$taskPython='C:/Users/geral/AppData/Local/Programs/Python/Python312/python.exe'
function Estado([string]$phase,$detail) {
    $taskConfig=Get-Content -LiteralPath "$taskRoot/configuracao.json" -Raw | ConvertFrom-Json
    @{estado=$phase;detalhe=$detail;instante=(Get-Date -Format o);processo_pipeline=$PID;frequencia_GHz=5.17;max_passes=$taskConfig.max_passes;delta_s=.04;sweeps=0;nucleos=14} |
      ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$taskRoot/qualificacao.json" -Encoding utf8
}
function Verificar([string]$phase) {
    $ErrorActionPreference='Continue'
    & $taskPython (Join-Path $PSScriptRoot 'centro_automatico_verificar.py') $phase 2>&1 | Out-File -LiteralPath "$taskRoot/pipeline.log" -Append -Encoding utf8
    $taskCode=$LASTEXITCODE;$ErrorActionPreference='Stop'
    if($taskCode -ne 0) {throw "Auditoria falhou em $phase; ver pipeline.log"}
}
try {
    if($Retomar14 -or $RetomarLimite4) {
        $taskTransition=if($RetomarLimite4){'4passes'}else{'14'}
        if(Test-Path -LiteralPath "$taskRoot/retomada${taskTransition}_iniciada.json") {throw 'Retomada ja iniciada; nao duplicar.'}
        $taskExpected=if($RetomarLimite4){239344}else{223588}
        if($AguardarAedt -ne $taskExpected) {throw 'PID original nao corresponde a transicao registrada.'}
        $oldTask=Get-CimInstance Win32_Process -Filter "ProcessId=$AguardarAedt"
        if($oldTask -and ($oldTask.Name -ne 'ansysedt.exe' -or $oldTask.CommandLine -notlike '*R04_Centro_Classic/centro*')) {throw 'Identidade do AEDT anterior inesperada.'}
        @{processo=$PID;instante=(Get-Date -Format o);aedt_anterior=$AguardarAedt} | ConvertTo-Json | Set-Content -LiteralPath "$taskRoot/retomada${taskTransition}_iniciada.json" -Encoding utf8
        Estado 'AGUARDANDO_PARADA_LIMPA_PARA_CONFIGURAR' @{aedt_anterior=$AguardarAedt;preservar_malha=$true;transicao=$taskTransition}
        if($oldTask) {Wait-Process -Id $AguardarAedt -ErrorAction SilentlyContinue}
        $snapshot=Join-Path $taskRoot ('transicao_'+$taskTransition)
        New-Item -ItemType Directory -Path $snapshot -Force | Out-Null
        Copy-Item -LiteralPath "$taskRoot/antena/P2M21_Ganho_Diagrama.aedt" -Destination "$snapshot/P2M21_Ganho_Diagrama_antes_retomada.aedt"
        & $taskPython (Join-Path $PSScriptRoot 'uniforme_verificar.py') monitor | Out-File -LiteralPath "$snapshot/historico_antes_retomada.json" -Encoding utf8
        if($LASTEXITCODE -ne 0){throw 'Historico anterior a retomada nao pode ser auditado.'}
        if($RetomarLimite4){
            $taskLimitScript=Join-Path $PSScriptRoot 'centro_limite_preparar.py'
            $taskLimit=Start-Process -FilePath 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe' -WindowStyle Hidden -PassThru -ArgumentList @('-ng','-LogFile',('"'+$taskRoot+'/limite_preparacao_aedt.log"'),'-RunScriptAndExit',('"'+$taskLimitScript+'"'))
            $taskLimit.WaitForExit()
            if($taskLimit.ExitCode -ne 0 -or (Get-Content -LiteralPath "$taskRoot/limite_preparacao.log" -Tail 1) -ne 'LIMITE_QUATRO_APLICADO'){throw 'Ajuste para quatro passes falhou.'}
        }
    } elseif(Test-Path -LiteralPath "$taskRoot/pipeline_iniciado.json") {throw 'Fila de centro ja iniciada; nao duplicar.'}
    Verificar 'preparacao'
    @{processo=$PID;instante=(Get-Date -Format o)} | ConvertTo-Json | Set-Content -LiteralPath "$taskRoot/pipeline_iniciado.json" -Encoding utf8
    $taskScript=Join-Path $PSScriptRoot 'uniforme_resolver.py'
    $taskLog=if($RetomarLimite4){'centro_4passes_aedt.log'}elseif($Retomar14){'centro_14nucleos_aedt.log'}else{'centro_aedt.log'}
    $taskProcess=Start-Process -FilePath 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe' -WindowStyle Hidden -PassThru -ArgumentList @('-ng','-LogFile',('"'+$taskRoot+'/'+$taskLog+'"'),'-RunScriptAndExit',('"'+$taskScript+'"'))
    Estado 'CENTRO_EM_EXECUCAO' @{processo_aedt=$taskProcess.Id;sem_refinamento_inicial=$true;base='Mixed Order';retomada14=[bool]$Retomar14;retomada4passes=[bool]$RetomarLimite4}
    $taskProcess.WaitForExit()
    if($taskProcess.ExitCode -ne 0 -or (Get-Content -LiteralPath "$taskRoot/antena/centro.log" -Tail 1) -ne 'CENTRO_UNIFORME_OK') {throw 'Calculo central nao terminou normalmente.'}
    Verificar 'centro'
    Estado 'CENTRO_CONCLUIDO_REVISAR' 'Somente 5.17GHz; revisar ganho e diagramas. Nenhum sweep.'
} catch {
    Estado 'REQUER_VERIFICACAO' $_.Exception.Message
    $_ | Out-String | Out-File -LiteralPath "$taskRoot/pipeline.log" -Append -Encoding utf8
    exit 1
}
