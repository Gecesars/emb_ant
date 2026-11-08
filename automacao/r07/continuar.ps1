param([Parameter(Mandatory=$true)][int]$CentroProcesso)
$ErrorActionPreference='Stop'
$root='D:/dev/EMBRAER/P1H/R07_Banda17'
$env:P1H_R07=$root
$py='C:/Users/geral/AppData/Local/Programs/Python/Python312/python.exe'
$aedt='C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe'
function Estado([string]$etapa,$detalhe) {
    @{processo=$PID;instante=(Get-Date -Format o);etapa=$etapa;detalhe=$detalhe;max_passes=6;delta_s=.02} |
        ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$root/qualificacao.json" -Encoding utf8
}
function Python([string]$script,[string[]]$argumentos=@()) {
    & $py (Join-Path $PSScriptRoot $script) @argumentos >> "$root/qualificacao.log" 2>&1
    if ($LASTEXITCODE -ne 0) {throw "Falha em $script, codigo $LASTEXITCODE"}
}
function Nativo([string]$script,[string]$log,[string]$estadoLog,[string]$ok) {
    $p=Start-Process -FilePath $aedt -WindowStyle Hidden -PassThru -ArgumentList @('-ng','-LogFile',('"'+$root+'/'+$log+'"'),'-RunScriptAndExit',('"'+(Join-Path $PSScriptRoot $script)+'"'))
    Estado $script @{processo_aedt=$p.Id;fase=$env:P1H_R07_ETAPA}
    $p.WaitForExit()
    if ($p.ExitCode -ne 0) {throw "Falha AEDT em $script, codigo $($p.ExitCode)"}
    if ((Get-Content -LiteralPath (Join-Path $root $estadoLog) -Tail 1) -ne $ok) {throw "Saida incompleta em $script"}
}
try {
    if(Test-Path -LiteralPath "$root/pipeline_iniciado.json") {throw 'Pipeline R07 ja iniciado; nao duplicar.'}
    $centro=Get-CimInstance Win32_Process -Filter "ProcessId=$CentroProcesso"
    if($centro -and ($centro.Name -ne 'ansysedt.exe' -or $centro.CommandLine -notmatch 'automacao[/\\]r07[/\\]resolver_centro.py')) {
        throw 'PID de centro nao pertence ao R07.'
    }
    @{processo=$PID;centro=$CentroProcesso;inicio=(Get-Date -Format o)} | ConvertTo-Json | Set-Content -LiteralPath "$root/pipeline_iniciado.json" -Encoding utf8
    Estado 'aguardando_centro' @{processo_aedt=$CentroProcesso}
    if($centro) {Wait-Process -Id $CentroProcesso -ErrorAction SilentlyContinue}
    if((Get-Content -LiteralPath "$root/antena/centro.log" -Tail 1) -ne 'CENTRO_R07_RESOLVIDO_AUDITAR') {throw 'Centro nao terminou normalmente.'}
    Python 'auditar.py' @($root)
    $env:P1H_R07_ETAPA='centro'
    Nativo 'exportar_campos.py' 'campos_centro_aedt.log' 'antena/campos_centro.log' 'CAMPOS_CENTRO_OK'
    Python 'analisar.py' @($root,'centro')
    Nativo 'resolver_banda.py' 'banda_aedt.log' 'antena/banda.log' 'BANDA17_RESOLVIDA_EXPORTAR_CAMPOS'
    Python 'auditar.py' @($root)
    $env:P1H_R07_ETAPA='banda'
    Nativo 'exportar_campos.py' 'campos_banda_aedt.log' 'antena/campos_banda.log' 'CAMPOS_BANDA_OK'
    Python 'analisar.py' @($root,'banda')
    Estado 'verificando_circuito_Nexxim' '17 frequencias, matriz completa e cabos ideais'
    Python 'circuito_aedt.py' @($root)
    Estado 'calculos_concluidos_revisar' 'Conferir RF17pontos, auditoria da malha, graficos e relatorio antes da entrega.'
} catch {
    Estado 'requer_verificacao' $_.Exception.Message
    $_ | Out-String | Add-Content -LiteralPath "$root/qualificacao.log"
    exit 1
}
