param([switch]$RetomarPreparado)
$ErrorActionPreference='Stop'
$taskRoot='D:/dev/EMBRAER/P2M21/R02_Malha_Uniforme17'
$env:P2M21_UNIFORME=$taskRoot
$taskPython='C:/Users/geral/AppData/Local/Programs/Python/Python312/python.exe'
$taskAedt='C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe'
function Estado([string]$stage,$detail) {
    @{estado=$stage;detalhe=$detail;processo_pipeline=$PID;instante=(Get-Date -Format o);max_passes=6;delta_s=.04} |
      ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$taskRoot/qualificacao.json" -Encoding utf8
}
function Verificar([string]$stage) {
    $ErrorActionPreference='Continue'
    & $taskPython (Join-Path $PSScriptRoot 'uniforme_verificar.py') $stage >> "$taskRoot/pipeline.log" 2>&1
    $taskCode=$LASTEXITCODE
    $ErrorActionPreference='Stop'
    if($taskCode -ne 0) {throw "Verificacao falhou: $stage (ver traceback em pipeline.log)"}
}
function Nativo([string]$script,[string]$stage,[string]$ok) {
    $env:P2M21_ETAPA=$stage
    $taskProcess=Start-Process -FilePath $taskAedt -WindowStyle Hidden -PassThru -ArgumentList @('-ng','-LogFile',('"'+$taskRoot+'/'+$stage+'_aedt.log'+'"'),'-RunScriptAndExit',('"'+(Join-Path $PSScriptRoot $script)+'"'))
    Estado $stage @{processo_aedt=$taskProcess.Id;script=$script}
    $taskProcess.WaitForExit()
    if($taskProcess.ExitCode -ne 0) {throw "AEDT falhou: $stage ($($taskProcess.ExitCode))"}
    if((Get-Content -LiteralPath "$taskRoot/antena/$stage.log" -Tail 1) -ne $ok) {throw "AEDT nao concluiu: $stage"}
}
try {
    if(Test-Path -LiteralPath "$taskRoot/pipeline_iniciado.json") {
        if(-not $RetomarPreparado) {throw 'Fila R02 uniforme ja iniciada; nao duplicar.'}
        $oldRun=Get-Content -Raw -LiteralPath "$taskRoot/pipeline_iniciado.json" | ConvertFrom-Json
        if(Get-Process -Id $oldRun.processo -ErrorAction SilentlyContinue) {throw 'Processo anterior ainda existe; verificar identidade antes de retomar.'}
        if((Get-Content -LiteralPath "$taskRoot/antena/preparacao.log" -Tail 1) -ne 'PREPARACAO_UNIFORME_OK') {throw 'Preparacao ainda nao concluida.'}
        if(Test-Path -LiteralPath "$taskRoot/antena/centro.log") {throw 'Ja houve inicio de centro; retomada preparada nao se aplica.'}
    }
    @{processo=$PID;inicio=(Get-Date -Format o)} | ConvertTo-Json | Set-Content -LiteralPath "$taskRoot/pipeline_iniciado.json" -Encoding utf8
    if(-not $RetomarPreparado) {Nativo 'uniforme_preparar.py' 'preparacao' 'PREPARACAO_UNIFORME_OK'}
    Verificar 'preparacao'
    Nativo 'uniforme_resolver.py' 'centro' 'CENTRO_UNIFORME_OK'
    Verificar 'centro'
    Nativo 'uniforme_resolver.py' 'banda' 'BANDA_UNIFORME_OK'
    Verificar 'banda'
    Estado 'CALCULOS_CONCLUIDOS_REVISAR' 'Convergencia, malha e 17 pontos verificados; revisar graficos e relatorio.'
} catch {
    Estado 'REQUER_VERIFICACAO' $_.Exception.Message
    $_ | Out-String | Add-Content -LiteralPath "$taskRoot/pipeline.log"
    exit 1
}
