param(
    [Parameter(Mandatory)][string]$DiretorioP1H,
    [int]$AguardarPainel = 0,
    [int]$AguardarCupons = 0
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path "$PSScriptRoot/../..").Path
$estudo = Join-Path (Resolve-Path $DiretorioP1H) R03_Estudo
$env:P1H_R03 = $estudo
$env:OPENBLAS_NUM_THREADS = '1'
$aedt = 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe'
$log = Join-Path $estudo fila.txt

function Registrar([string]$Texto) {
    Add-Content -LiteralPath $log -Value ((Get-Date -Format s) + ' ' + $Texto)
}
function ExecutarAedt([string]$Script,[string]$LogNativo) {
    $processo = Start-Process -FilePath $aedt -WindowStyle Hidden -PassThru -ArgumentList @(
        '-ng','-LogFile',('"' + $LogNativo + '"'),'-RunScriptAndExit',('"' + $Script + '"'))
    Registrar "Executando $Script em $LogNativo PID $($processo.Id)"
    $processo.WaitForExit()
    if ($processo.ExitCode) { Registrar "AEDT retornou $($processo.ExitCode) em $LogNativo" }
}
function AguardarAedt([int]$Numero) {
    if ($Numero -gt 0) {
        $job = Get-Process -Id $Numero -ErrorAction SilentlyContinue
        if ($job -and $job.ProcessName -eq 'ansysedt') { $job.WaitForExit() }
    }
}
function PublicarMetricas([string]$Pasta,[string]$Identificador) {
    if (Test-Path "$Pasta/centro.s2p") {
        & py -3.12 "$repo/automacao/r01/medir.py" $Pasta "$repo/resultados/$Identificador" --centro
    }
    if ((Test-Path "$Pasta/solucao.log") -and ((Get-Content "$Pasta/solucao.log" -Tail 1) -eq 'FEM_OK')) {
        & py -3.12 "$repo/automacao/r01/medir.py" $Pasta "$repo/resultados/$Identificador"
    }
}
function Rede([string]$Material) {
    $env:P1H_MATERIAIS = $Material
    $env:P1H_CALCULAR_REDE = '1'
    ExecutarAedt "$PSScriptRoot/rede_hfss.py" "$estudo/$Material/rede_hfss/aedt_rede.log"
    & py -3.12 "$PSScriptRoot/medir_rede.py" $estudo
    Registrar ("Rede "+$Material+" "+(Get-Content "$estudo/$Material/rede_hfss/calculo.log" -Tail 1))
}
function Painel([string]$Pasta,[string]$Nome,[string]$Identificador) {
    $env:P1H_R01 = $Pasta
    $env:P1H_NOME = $Nome
    $env:P1H_ITERATIVO = '1'
    $env:P1H_ORDEM = '0'
    $base = Join-Path $Pasta estudo
    if (!(Test-Path "$base/$Nome.aedt")) { throw "Painel ausente em $Pasta" }
    if (!(Test-Path "$base/solucao.log") -or ((Get-Content "$base/solucao.log" -Tail 1) -ne 'FEM_OK')) {
        ExecutarAedt "$repo/automacao/r01/resolver.py" "$base/aedt_fem.log"
    }
    PublicarMetricas $base $Identificador
    Registrar ("Painel "+$Nome+" "+(Get-Content "$base/solucao.log" -Tail 1))
}

Registrar 'Aguardando a solução anterior. Uma rede ou painel grande por vez.'
AguardarAedt $AguardarPainel
PublicarMetricas "$DiretorioP1H/R01_Flex/estudo" 'r01'
Rede 'ZYF300CA-C'
Rede 'ZYF255DA'
AguardarAedt $AguardarCupons
ExecutarAedt "$PSScriptRoot/cupons_hfss.py" "$estudo/cupons_refinamento.log"
& py -3.12 "$PSScriptRoot/extrair_cupons.py" $estudo
Painel "$estudo/painel_C" 'P1H_R03_Alongada' 'r03'
Painel "$DiretorioP1H/R02_FEM" 'P1H_R02' 'r02'
Painel "$DiretorioP1H/R02_Separadas" 'P1H_R02_10Separadas' 'r02_separadas'
Rede 'ZYF265D'
Rede 'ZYF300CA-P'
if ((Get-Content "$DiretorioP1H/R01_Flex/estudo/solucao.log" -Tail 1) -ne 'FEM_OK') {
    # Manter a ordem de base que gerou o ponto de centro convergido da R01.
    $env:P1H_R01 = "$DiretorioP1H/R01_Flex"
    $env:P1H_NOME = 'P1H_R01'
    $env:P1H_ITERATIVO = '0'
    ExecutarAedt "$repo/automacao/r01/resolver.py" "$env:P1H_R01/estudo/aedt_retomada.log"
    PublicarMetricas "$env:P1H_R01/estudo" 'r01'
}
Registrar 'Fila terminada. Conferir convergência, exportações e relatório.'
