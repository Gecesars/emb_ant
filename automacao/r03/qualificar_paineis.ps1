param([Parameter(Mandatory)][string]$DiretorioP1H,[int]$AguardarRede=0,[int]$AguardarCompactas=0)
$ErrorActionPreference='Stop'
$repo=(Resolve-Path "$PSScriptRoot/../..").Path
$native='C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe'
$env:OPENBLAS_NUM_THREADS='1'
$log="$DiretorioP1H/R03_Estudo/qualificacao_paineis.txt"
foreach ($numero in @($AguardarRede,$AguardarCompactas)) {
    if ($numero -le 0) { continue }
    $job=Get-Process -Id $numero -ErrorAction SilentlyContinue
    if ($job) { $job.WaitForExit() }
}
$cases=@(
    @{Pasta='R02_FEM';Nome='P1H_R02';Resultado='r02'},
    @{Pasta='R02_Separadas';Nome='P1H_R02_10Separadas';Resultado='r02_separadas'}
)
function Resolver([string]$LogNativo) {
    $script="$repo/automacao/r01/resolver.py"
    $proc=Start-Process $native -WindowStyle Hidden -ArgumentList @('-ng','-LogFile',('"' + $LogNativo + '"'),
        '-RunScriptAndExit',('"' + $script + '"')) -PassThru
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format s) $env:P1H_NOME centro=$env:P1H_SOMENTE_CENTRO PID $($proc.Id)"
    $proc.WaitForExit()
}
foreach ($case in $cases) {
    $env:P1H_R01="$DiretorioP1H/$($case.Pasta)"
    $env:P1H_NOME=$case.Nome
    $env:P1H_ITERATIVO='1'
    $env:P1H_ORDEM='0'
    $env:P1H_SOMENTE_CENTRO='1'
    $base="$env:P1H_R01/estudo"
    $dest="$repo/resultados/$($case.Resultado)"
    if (!(Test-Path "$base/Centro_H_5170.csv")) { Resolver "$base/aedt_centro.log" }
    & py -3.12 "$repo/automacao/r01/medir.py" $base $dest --centro
    if ($LASTEXITCODE) { throw "Centro sem validação em $base" }
    $metric=Import-Csv "$dest/metricas_Centro.csv"
    if ($metric.atende_H -eq 'True' -and $metric.atende_ganho -eq 'True') {
        $env:P1H_SOMENTE_CENTRO='0'
        $env:P1H_ITERATIVO='0'
        Resolver "$base/aedt_banda.log"
        & py -3.12 "$repo/automacao/r01/medir.py" $base $dest
        if ($LASTEXITCODE) { throw "Banda incompleta em $base" }
    } else {
        Add-Content -LiteralPath $log -Value "$(Get-Date -Format s) $($case.Nome) reprova requisito de toda a banda no centro. Ganho $($metric.ganho_frontal_dBi), H $($metric.H_graus)"
    }
}
Add-Content -LiteralPath $log -Value "$(Get-Date -Format s) Paineis processados. Conferir dados e relatório."
