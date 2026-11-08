$ErrorActionPreference='Stop'
$root='D:/dev/EMBRAER/P1H/R07_Banda17'
$env:P1H_R07=$root
$py='C:/Users/geral/AppData/Local/Programs/Python/Python312/python.exe'
$aedt='C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe'
function Estado([string]$etapa,$detalhe) {
    @{processo=$PID;instante=(Get-Date -Format o);etapa=$etapa;detalhe=$detalhe;novos_passes_adaptativos=0;limite_usuario=6;delta_s_fonte=.004} |
        ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$root/qualificacao.json" -Encoding utf8
}
function Python([string]$script,[string[]]$argumentos=@()) {
    & $py (Join-Path $PSScriptRoot $script) @argumentos >> "$root/qualificacao_fixa.log" 2>&1
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
    if(Test-Path -LiteralPath "$root/pipeline_fixa_iniciado.json") {throw 'Fila fixa ja iniciada; nao duplicar.'}
    $running=Get-CimInstance Win32_Process | Where-Object {$_.Name -match '^ansysedt.exe$|^hf3d.exe$|^HFSSCOMENGINE.exe$'}
    if($running) {throw 'Existe processo AEDT/solver; confirmar antes de iniciar outro.'}
    @{processo=$PID;inicio=(Get-Date -Format o)} | ConvertTo-Json | Set-Content -LiteralPath "$root/pipeline_fixa_iniciado.json" -Encoding utf8
    Python 'validar_malha_fixa.py' @($root)
    Nativo 'resolver_controle_fixo.py' 'controle_fixo_aedt.log' 'antena/controle_fixo.log' 'CONTROLE_FIXO_RESOLVIDO'
    Python 'validar_malha_fixa.py' @($root,'--apos-solve')
    $env:P1H_R07_ETAPA='centro'
    Nativo 'exportar_campos.py' 'campos_centro_aedt.log' 'antena/campos_centro.log' 'CAMPOS_CENTRO_OK'
    Python 'analisar.py' @($root,'centro')
    Nativo 'resolver_banda.py' 'banda_aedt.log' 'antena/banda.log' 'BANDA17_RESOLVIDA_EXPORTAR_CAMPOS'
    Python 'validar_malha_fixa.py' @($root,'--apos-solve')
    $env:P1H_R07_ETAPA='banda'
    Nativo 'exportar_campos.py' 'campos_banda_aedt.log' 'antena/campos_banda.log' 'CAMPOS_BANDA_OK'
    Python 'analisar.py' @($root,'banda')
    Estado 'verificando_circuito_Nexxim' '17 frequencias, matriz completa e cabos ideais'
    Python 'circuito_aedt.py' @($root)
    Estado 'calculos_concluidos_revisar' 'Conferir RF17pontos, origem da malha, auditoria, graficos e relatorio.'
} catch {
    Estado 'requer_verificacao' $_.Exception.Message
    $_ | Out-String | Add-Content -LiteralPath "$root/qualificacao_fixa.log"
    exit 1
}
