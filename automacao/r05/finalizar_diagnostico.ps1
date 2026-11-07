param(
    [Parameter(Mandatory)][string]$Diretorio,
    [Parameter(Mandatory)][int]$ProcessoSolver
)
$ErrorActionPreference = 'Stop'
$solver = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessoSolver"
if ($solver -and $solver.CommandLine -like '*antena_direta_hfss.py*') {
    (Get-Process -Id $ProcessoSolver).WaitForExit()
}
$env:P1H_R05 = $Diretorio
$script = Join-Path $PSScriptRoot 'extrair_20portas.py'
$native = 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe'
$log = Join-Path $Diretorio 'antena_direta/padroes_aedt.log'
$process = Start-Process -FilePath $native -WindowStyle Hidden -PassThru -ArgumentList @(
    '-ng', '-LogFile', ('"' + $log + '"'), '-RunScriptAndExit', ('"' + $script + '"')
)
$process.WaitForExit()
