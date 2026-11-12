param([int]$AguardarDivisor=0,[string]$Caso='a00')
$ErrorActionPreference='Stop'
$base='D:/dev/EMBRAER/P2S13/R11_Fabricavel_Radome'
$repo='D:/dev/EMBRAER/emb_ant'
$root=Join-Path $base $Caso
$env:P2S13_ROOT=$root
$aedt='C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe'
function Estado($s) { @{estado=$s;hora=(Get-Date).ToString('o');caso=$Caso;pipeline_pid=$PID} | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $root 'pipeline.json') }
try {
 if($AguardarDivisor -gt 0) {
   Estado 'AGUARDANDO_DIVISOR'
   $running=Get-CimInstance Win32_Process -Filter "ProcessId=$AguardarDivisor"
   if($running) { if($running.CommandLine -notlike '*r11_divisor_hfss.py*') {throw 'PID nao pertence ao divisor R11'}; Wait-Process -Id $AguardarDivisor }
   $status=Get-Content -Raw (Join-Path $base 'd00/estado.json') | ConvertFrom-Json
   if($status.estado -ne 'CONCLUIDO_AGUARDA_ANALISE') {throw 'Divisor sem exportacao concluida'}
 }
 foreach($step in @('criar_hfss','resolver')) {
   Estado $step.ToUpper()
   $script=Join-Path $repo "projetos/P2S13/automacao/r11_conjunto_$step.py"
   $log=Join-Path $root "$step`_aedt.log"
   $proc=Start-Process -FilePath $aedt -ArgumentList '-ng','-LogFile',$log,'-RunScriptAndExit',$script -WindowStyle Hidden -PassThru
   $proc.Id | Set-Content (Join-Path $root "$step.pid")
   $proc.WaitForExit()
   if($step -eq 'criar_hfss') {
      $v=Get-Content -Raw (Join-Path $root 'hfss_validacao.json') | ConvertFrom-Json
      if($v.validacao -ne 1 -or $v.erros.Count -gt 0) {throw 'Modelo HFSS reprovado'}
   } else {
      $q=Get-Content -Raw (Join-Path $root 'qualificacao.json') | ConvertFrom-Json
      if($q.estado -ne 'SOLVE_EXPORTADO_AGUARDA_AUDITORIA') {throw 'Solver nao concluiu exportacao'}
   }
 }
 Estado 'CONCLUIDO_AGUARDA_AUDITORIA'
} catch {
 Estado ('FALHA: '+$_.Exception.Message)
 throw
}
