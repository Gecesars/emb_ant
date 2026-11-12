$ErrorActionPreference='Stop'
$root='D:/dev/EMBRAER/P2S13/R14_Compacto_Simetrico_SemRadome/c00'
$py='C:/Users/geral/AppData/Local/Programs/Python/Python312/python.exe'
function State($s){@{estado=$s;hora=(Get-Date).ToString('o');pid=$PID}|ConvertTo-Json|Set-Content "$root/pos_pipeline.json" -Encoding utf8}
try{
 State 'AGUARDANDO_EM_SEPARADO'
 while($true){
  $p=Get-Content -Raw "$root/em_pipeline.json"|ConvertFrom-Json
  if($p.estado -like 'FALHA*'){throw $p.estado}
  if($p.estado -eq 'EM_CONCLUIDO_AGUARDA_CIRCUITO_NEXXIM'){break}
  if(-not(Get-Process -Id $p.pipeline_pid -ErrorAction SilentlyContinue)){throw 'EM encerrou sem estado final'}
  Start-Sleep -Seconds 10
 }
 # Nesta etapa nao ha novo solve FEM. Outra tarefa HFSS do usuario nao deve
 # bloquear a conexao de oito pequenos blocos Touchstone no Nexxim.
 while((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory -lt 2097152){
  State 'AGUARDANDO_MEMORIA_PARA_CIRCUITO'
  Start-Sleep -Seconds 20
 }
 State 'AUDITAR_E_INTERLIGAR'
 & $py (Join-Path $PSScriptRoot 'r14_circuito.py') *> "$root/circuito.log"
 if($LASTEXITCODE -ne 0){throw 'Auditoria ou interligacao falhou'}
 State 'NEXXIM'
 & $py (Join-Path $PSScriptRoot 'r14_nexxim.py') *> "$root/nexxim.log"
 if($LASTEXITCODE -ne 0){throw 'Nexxim requer verificacao'}
 State 'CONCLUIDO_REVISAR_RESULTADOS'
}catch{State ('FALHA: '+$_.Exception.Message);throw}
