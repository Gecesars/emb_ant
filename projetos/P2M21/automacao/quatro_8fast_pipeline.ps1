param([ValidateSet('preparar','centro','fast')][string]$RetomarEm)
$ErrorActionPreference='Stop'
$taskRoot='D:/dev/EMBRAER/P2M21/R12_Quatro_8Passes_Fast'
$env:P2M21_8FAST=$taskRoot
$taskPython='C:/Users/geral/AppData/Local/Programs/Python/Python312/python.exe'
$taskAedt='C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe'
if ((Test-Path -LiteralPath (Join-Path $taskRoot 'pipeline_iniciado.json')) -and -not $RetomarEm) {throw 'Fila ja iniciada; nao duplicar'}
if($RetomarEm){
 $old=Get-Content -LiteralPath (Join-Path $taskRoot 'pipeline_iniciado.json') -Raw | ConvertFrom-Json
 if(Get-Process -Id $old.pid -ErrorAction SilentlyContinue){throw 'Processo da fila anterior ainda existe; conferir antes de retomar'}
 if($RetomarEm -eq 'preparar' -and (Test-Path -LiteralPath (Join-Path $taskRoot 'antena/convergencia.txt'))){throw 'Centro novo ja exportado; nao reconfigurar'}
 if($RetomarEm -eq 'centro' -and (Test-Path -LiteralPath (Join-Path $taskRoot 'antena/convergencia.txt'))){throw 'Centro novo ja exportado; nao repetir'}
 if($RetomarEm -eq 'fast' -and (Test-Path -LiteralPath (Join-Path $taskRoot 'antena/banda_fast.s2p'))){throw 'Fast ja exportado; nao repetir'}
}
if (Get-Process hf3d,G3dMesher -ErrorAction SilentlyContinue) {throw 'Solver existente; serializar'}
@{pid=$PID;inicio=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRoot 'pipeline_iniciado.json') -Encoding utf8
try {
 $stages=@('preparar','centro','fast')
 if($RetomarEm){$stages=$stages[[array]::IndexOf($stages,$RetomarEm)..2]}
 foreach($stage in $stages) {
  $env:P2M21_8FAST_ETAPA=$stage
  $argsList=@('-ng','-LogFile',(Join-Path $taskRoot ($stage+'_aedt.log')),'-RunScriptAndExit',(Join-Path $PSScriptRoot 'quatro_8fast_aedt.py'))
  $proc=Start-Process -FilePath $taskAedt -ArgumentList $argsList -WindowStyle Hidden -PassThru
  @{etapa=$stage;pid=$proc.Id;inicio=(Get-Date).ToString('o');argumentos=$argsList} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskRoot ($stage+'_processo.json')) -Encoding utf8
  Write-Output "$stage PID $($proc.Id)";$proc.WaitForExit()
  if($proc.ExitCode -ne 0 -or (Test-Path -LiteralPath (Join-Path $taskRoot ('falha_'+$stage+'.json')))){throw "Falha AEDT na etapa $stage"}
  & $taskPython (Join-Path $PSScriptRoot 'quatro_8fast_auditar.py') $stage
  if($LASTEXITCODE -ne 0){throw "Auditoria falhou na etapa $stage"}
 }
 Write-Output 'CONTINUACAO_E_FAST_CONCLUIDOS'
} catch {
 @{estado='REQUER_VERIFICACAO';etapa=$stage;erro=$_.Exception.Message;atualizado=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRoot 'qualificacao.json') -Encoding utf8
 throw
}
