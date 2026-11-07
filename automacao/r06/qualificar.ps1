param([Parameter(Mandatory)][int]$AntenaId, [Parameter(Mandatory)][int]$FilaDivisoresId, [switch]$AposBaseline)
$ErrorActionPreference='Stop'
$root='D:/dev/EMBRAER/P1H/R06_sem_cabos'
$py='C:/Users/geral/AppData/Local/Programs/Python/Python312/python.exe'
$aedt='C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe'
$env:P1H_R06=$root
function Estado([string]$etapa,[object]$detalhe) {
    @{etapa=$etapa;detalhe=$detalhe;instante=(Get-Date).ToString('o');processo=$PID} |
        ConvertTo-Json -Depth 5 | Set-Content -LiteralPath "$root/qualificacao.json"
}
function Esperar([int]$idAlvo,[string]$identidade) {
    $p=Get-CimInstance Win32_Process -Filter "ProcessId=$idAlvo"
    if ($p) {
        if ($p.CommandLine -notmatch $identidade) { throw "Identidade inesperada: $idAlvo" }
        (Get-Process -Id $idAlvo).WaitForExit()
    }
}
function Python([string]$script,[string[]]$argumentos=@()) {
    & $py (Join-Path $PSScriptRoot $script) @argumentos >> "$root/qualificacao.log" 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Falha em $script, codigo $LASTEXITCODE" }
}
function Nativo([string]$script,[string]$nomeLog) {
    $p=Start-Process -FilePath $aedt -WindowStyle Hidden -PassThru -ArgumentList @('-ng','-LogFile',('"'+$root+'/'+$nomeLog+'"'),'-RunScriptAndExit',('"'+(Join-Path $PSScriptRoot $script)+'"'))
    Estado $script @{processo_aedt=$p.Id}
    $p.WaitForExit()
    if ($p.ExitCode -ne 0) { throw "Falha AEDT: $script, codigo $($p.ExitCode)" }
}
function Auditar {
    Python 'auditar_convergencia.py' @("$root/antena/PCB_R06.aedt")
    $audit=Get-Content -LiteralPath "$root/antena/auditoria_convergencia.json" -Raw | ConvertFrom-Json
    if (-not $audit.convergencia_aprovada) { throw 'PCB sem dois passes de convergencia S/campo.' }
}
try {
    if (-not $AposBaseline) {
    Estado 'aguardando_pcb_inicial' $AntenaId
    Esperar $AntenaId 'r06[/\\]pcb_hfss.py'
    Auditar
    Nativo 'extrair_campos.py' 'campos_inicial_aedt.log'
    if ((Get-ChildItem -LiteralPath "$root/antena/padroes" -Filter '*.csv').Count -ne 40) { throw 'Padroes iniciais incompletos.' }
    if ((Get-Content -LiteralPath "$root/antena/padroes.log" -Tail 1) -ne 'PADROES_R06_OK') { throw 'Exportacao de campos iniciais falhou.' }
    $baseline="$root/antena_malha_inicial"
    if (Test-Path -LiteralPath $baseline) { throw 'Preservar baseline ja existente; nao sobrescrever.' }
    New-Item -ItemType Directory -Path $baseline | Out-Null
    foreach($file in @('PCB_R06.aedt','antena.s20p','Centro_H.csv','Centro_V.csv','convergencia.txt','auditoria_convergencia.json','aedt.log','solucao.log','padroes.log')) {
        Copy-Item -LiteralPath "$root/antena/$file" -Destination $baseline
    }
    Copy-Item -LiteralPath "$root/antena/padroes" -Destination $baseline -Recurse
    Python 'auditar_malha.py' @("$root/antena", "$baseline/malha.json")
    } else {
        if ((Get-ChildItem -LiteralPath "$root/antena_malha_inicial/padroes" -Filter '*.csv').Count -ne 40) { throw 'Baseline preservada incompleta.' }
        if (Test-Path -LiteralPath "$root/antena/refinamento.log") { throw 'Refinamento ja iniciado; verificar antes de retomar.' }
    }
    Estado 'aguardando_divisores_para_refinar' $FilaDivisoresId
    Esperar $FilaDivisoresId 'r06[/\\](fila_divisores.ps1|retomar_divisor.py)'
    Python 'analisar_divisores.py' @($root)
    Nativo 'refinar_pcb.py' 'refinamento_aedt.log'
    if ((Get-Content -LiteralPath "$root/antena/refinamento.log" -Tail 1) -ne 'REFINAMENTO_LOCAL_CONCLUIDO_VERIFICAR') { throw 'Refinamento HFSS incompleto.' }
    Auditar
    Python 'auditar_malha.py' @("$root/antena", "$root/antena/malha.json")
    Nativo 'extrair_campos.py' 'campos_final_aedt.log'
    if ((Get-Content -LiteralPath "$root/antena/padroes.log" -Tail 1) -ne 'PADROES_R06_OK') { throw 'Exportacao de campos finais falhou.' }
    Python 'circuito.py' @($root)
    Python 'comparar_malhas.py' @($root)
    Python 'circuito_aedt.py' @($root)
    Python 'graficos.py' @($root)
    Estado 'calculos_concluidos_aguardando_revisao_relatorio' 'Conferir criterios, malha, figuras, nativos e pacote antes de entregar.'
} catch {
    Estado 'requer_verificacao' $_.Exception.Message
    $_ | Out-String | Add-Content -LiteralPath "$root/qualificacao.log"
    exit 1
}
