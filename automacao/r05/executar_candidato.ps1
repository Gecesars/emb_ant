param(
    [Parameter(Mandatory)][string]$Diretorio,
    [int[]]$Aguardar = @(),
    [string]$Nome = 'P1H_R05_ENIG',
    [string]$Marcador = 'MODELO_ENIG_OK',
    [switch]$PreservarSetup
)
$ErrorActionPreference = 'Stop'
$registro = Join-Path $Diretorio 'estudo/fila.json'
foreach ($solverId in $Aguardar) {
    $processo = Get-CimInstance Win32_Process -Filter "ProcessId=$solverId"
    if ($processo) {
        if ($processo.Name -ne 'ansysedt.exe' -or $processo.CommandLine -notmatch '(antena_direta_hfss|enig_divisores|gerar_malha)\.py') {
            throw "O processo $solverId nao corresponde a uma etapa desta campanha."
        }
        @{ estado='aguardando'; processo=$solverId; instante=(Get-Date).ToString('o') } | ConvertTo-Json | Set-Content -LiteralPath $registro
        (Get-Process -Id $solverId).WaitForExit()
    }
}
$modelo = Get-Content -Raw -LiteralPath (Join-Path $Diretorio 'estudo/modelo.log')
if ($modelo -notmatch [regex]::Escape($Marcador)) { throw 'Modelo nao validado.' }
$env:P1H_R01 = $Diretorio
$env:P1H_NOME = $Nome
if ($PreservarSetup) {
    Remove-Item Env:P1H_ITERATIVO -ErrorAction SilentlyContinue
} else {
    $env:P1H_ITERATIVO = '1'
}
$env:P1H_ORDEM = '0'
$env:P1H_SOMENTE_CENTRO = '1'
$native = 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe'
$script = Join-Path (Split-Path $PSScriptRoot) 'r01/resolver.py'
$log = Join-Path $Diretorio 'estudo/centro_aedt.log'
$processo = Start-Process -FilePath $native -WindowStyle Hidden -PassThru -ArgumentList @(
    '-ng', '-LogFile', ('"'+$log+'"'), '-RunScriptAndExit', ('"'+$script+'"')
)
@{ estado='simulando_centro'; processo=$processo.Id; instante=(Get-Date).ToString('o') } | ConvertTo-Json | Set-Content -LiteralPath $registro
$processo.WaitForExit()
@{ estado='solver_encerrado_verificar_convergencia'; processo=$processo.Id; instante=(Get-Date).ToString('o') } | ConvertTo-Json | Set-Content -LiteralPath $registro
