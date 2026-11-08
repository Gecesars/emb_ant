param([int]$DivisorPid)
$ErrorActionPreference='Stop'
$taskRoot='D:/dev/EMBRAER/P2M21/R00_Concepcao'
$identity=Get-CimInstance Win32_Process -Filter "ProcessId=$DivisorPid"
if ($identity -and $identity.CommandLine -notlike '*P2M21*resolver_divisores.py*') {throw 'Identidade de processo nao corresponde a fila P2M21'}
if ($identity) {Wait-Process -Id $DivisorPid -ErrorAction SilentlyContinue}
$state=Get-Content -Raw -LiteralPath "$taskRoot/qualificacao.json" | ConvertFrom-Json
if ($state.estado -ne 'DIVISORES_CONCLUIDOS_AGUARDANDO_AUDITORIA') {exit 2}
$scriptPath=Join-Path $PSScriptRoot 'resolver_antena_centro.py'
$p=Start-Process -FilePath 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe' -ArgumentList @('-ng','-LogFile',"`"$taskRoot/antena_centro_aedt.log`"",'-RunScriptAndExit',"`"$scriptPath`"") -WindowStyle Hidden -PassThru
@{fase='antena_centro';processo_aedt=$p.Id;max_passes=6;delta_s=.02} | ConvertTo-Json | Set-Content -LiteralPath "$taskRoot/fila.json" -Encoding utf8
Wait-Process -Id $p.Id
