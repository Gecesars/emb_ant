param([Parameter(Mandatory=$true)][string]$Destino,
    [string]$Aedt="C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe")
$ErrorActionPreference="Stop"
$repo=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$base=[IO.Path]::GetFullPath($Destino)
if (($base -eq $repo) -or $base.StartsWith($repo+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {throw "Escolha uma pasta externa ao checkout."}
if ((Test-Path -LiteralPath $base) -and (Get-ChildItem -LiteralPath $base -Force)) {throw "A pasta de execução deve estar vazia."}
if (-not (Test-Path -LiteralPath $Aedt -PathType Leaf)) {throw "Informe o executável com -Aedt."}
$null=New-Item -ItemType Directory -Path $base -Force
Get-ChildItem -LiteralPath "$PSScriptRoot/P1H" | Copy-Item -Destination $base -Recurse
$study=Join-Path $base "Comparacao_PCB"
Copy-Item -LiteralPath "$repo/fabricacao/montagem/comprimento_selecionado.json" -Destination "$base/Divisor_10X_PTFE"
function Etapa([string]$Script,[string]$Log,[string]$Marca) {
    $out=[IO.Path]::ChangeExtension($Script,"aedt.log")
    $job=Start-Process -FilePath $Aedt -ArgumentList @("-ng","-LogFile",('"' + $out + '"'),"-RunScriptAndExit",('"' + $Script + '"')) -WindowStyle Hidden -PassThru -Wait
    if ($job.ExitCode -ne 0 -or !(Test-Path -LiteralPath $Log) -or ((Get-Content -LiteralPath $Log -Tail 1) -notlike $Marca)) {throw "Falha em $Script. Consulte $out e $Log."}
}
Etapa "$study/Divisor/construir_radial.py" "$study/Divisor/hfss_placa.log" "PCB_READY"
Etapa "$study/Divisor/resolver_radial.py" "$study/Divisor/solucao_placa.log" "PCB_FEM_COMPLETO"
Etapa "$study/Junta/simular_junta.py" "$study/Junta/solucao.log" "FIM"
foreach ($case in @("Continua","Separadas")) {
    $env:P1H_PCB=$case
    $dir=Join-Path $study $case
    $null=New-Item -Path $dir -ItemType Directory
    Copy-Item -LiteralPath "$repo/hfss/antenas/P1H_AB_em_fase.aedt" -Destination "$dir/P1H_$case.aedt"
    Etapa "$study/modelar.py" "$dir/modelo.log" "MODELO_OK"
    Etapa "$study/refinar.py" "$dir/refino.log" "REFINO_OK 100"
    Etapa "$study/resolver.py" "$dir/solucao.log" "FEM_OK"
    & "$study/posprocessar.ps1" -Caso $case -Aedt $Aedt
}
py -3.12 "$study/relatorio.py"
if ($LASTEXITCODE -ne 0) {throw "Falha ao gerar o relatório."}
