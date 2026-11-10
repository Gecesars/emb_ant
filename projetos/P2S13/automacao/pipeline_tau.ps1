$ErrorActionPreference='Stop'
& (Join-Path $PSScriptRoot 'pipeline.ps1') -Variantes @('v03_b20_a60_tau','v04_b30_a60_tau') -UsarNativosPreparados
