param([Parameter(Mandatory)][int]$AntenaId)
$ErrorActionPreference='Stop'
$root='D:/dev/EMBRAER/P1H/R06_sem_cabos'
$p=Get-CimInstance Win32_Process -Filter "ProcessId=$AntenaId"
if ($p) {
    if ($p.Name -ne 'ansysedt.exe' -or $p.CommandLine -notmatch 'r06/pcb_hfss.py') { throw 'Processo nao corresponde a PCB R06.' }
    (Get-Process -Id $AntenaId).WaitForExit()
}
$env:P1H_R06=$root
$script=Join-Path $PSScriptRoot 'divisores_hfss.py'
$solver=Start-Process -FilePath 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe' -WindowStyle Hidden -PassThru -ArgumentList @('-ng','-LogFile',('"'+$root+'/divisores_aedt.log"'),'-RunScriptAndExit',('"'+$script+'"'))
@{estado='divisores_completos_em_calculo';processo=$solver.Id;instante=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath ($root+'/fila_divisores.json')
$solver.WaitForExit()
@{estado='divisores_encerrados_verificar_logs';processo=$solver.Id;instante=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath ($root+'/fila_divisores.json')
