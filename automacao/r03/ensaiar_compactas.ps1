param([Parameter(Mandatory)][string]$Estudo,[int]$AguardarCupons=0)
$ErrorActionPreference='Stop'
$repo=(Resolve-Path "$PSScriptRoot/../..").Path
$native='C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe'
$env:OPENBLAS_NUM_THREADS='1'
& py -3.12 "$PSScriptRoot/compactas.py" $Estudo --preparar
if ($LASTEXITCODE) { throw 'Falha na síntese ou conferência das redes compactas' }
if ($AguardarCupons -gt 0) {
    $job=Get-Process -Id $AguardarCupons -ErrorAction SilentlyContinue
    if ($job -and $job.ProcessName -eq 'ansysedt') { $job.WaitForExit() }
}
foreach ($material in @('ZYF255DA','ZYF265D','ZYF300CA-P')) {
    foreach ($stage in @(2,5)) {
        $base="$Estudo/$material/compacta/1x$stage"
        $env:P1H_RADIAL_DIR=$base
        foreach ($step in @('construir','resolver')) {
            if ($step -eq 'construir') {
                if (Test-Path "$base/*.aedt") { continue }
                $script="$repo/automacao/P1H/Divisor_10X_PTFE/construir_radial.py"
            } else {
                if ((Test-Path "$base/solver.log") -and ((Get-Content "$base/solver.log" -Tail 1) -eq 'FEM_OK')) { continue }
                # Estes cupons de 6/12 portas têm malha muito menor que o painel de antenas.
                # Esperar quando a reserva de memória virtual disponível cair abaixo de 12 GiB.
                while ((Get-CimInstance Win32_OperatingSystem).FreeVirtualMemory -lt 12582912) { Start-Sleep 60 }
                $script="$repo/automacao/r02/resolver_divisor.py"
            }
            $proc=Start-Process $native -WindowStyle Hidden -ArgumentList @('-ng','-LogFile',('"' + "$base/$step.log" + '"'),
                '-RunScriptAndExit',('"' + $script + '"')) -PassThru
            Add-Content -LiteralPath "$Estudo/compactas_fila.txt" -Value "$(Get-Date -Format s) $material 1x$stage $step PID $($proc.Id)"
            $proc.WaitForExit()
        }
    }
    & py -3.12 "$PSScriptRoot/compactas.py" $Estudo
    if ($LASTEXITCODE) { throw 'Verificar convergência e reciprocidade das redes compactas' }
}
