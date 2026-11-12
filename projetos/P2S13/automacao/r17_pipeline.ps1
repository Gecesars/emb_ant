$ErrorActionPreference='Stop'
$root='D:/dev/EMBRAER/P2S13/R17_Flanges_Refletor/plano90'
$py='C:/Users/geral/AppData/Local/Programs/Python/Python312/python.exe'
$env:P2S13_ROOT="$root/antena";$env:P2S13_R16_CASE=$root
function State($s){@{estado=$s;hora=(Get-Date).ToString('o');pipeline_pid=$PID}|ConvertTo-Json|Set-Content "$root/pipeline.json" -Encoding utf8}
function Aedt($script,$log){
 $p=Start-Process 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe' -ArgumentList @('-ng','-LogFile',"$root/$log",'-RunScriptAndExit',(Join-Path $PSScriptRoot $script)) -WindowStyle Hidden -PassThru
 $p.Id|Set-Content "$root/aedt_atual.pid";$p.WaitForExit();if($p.ExitCode -ne 0){throw "Falha AEDT $script"}
}
try{
 if(Test-Path "$root/antena/convergencia.txt"){throw 'Nao duplicar solve existente'}
 while(Get-Process hf3d,G3dMesher -ErrorAction SilentlyContinue){State 'AGUARDANDO_OUTRO_FEM';Start-Sleep -Seconds 15}
 State 'REFLETOR_PLANO';Aedt 'r17_plano_hfss.py' 'geometria_aedt.log'
 State 'HFSS_ANTENA';Aedt 'r14_antena_resolver.py' 'centro_aedt.log'
 State 'CIRCUITO'; & $py (Join-Path $PSScriptRoot 'r17_circuito.py') *> "$root/circuito.log"
 if($LASTEXITCODE -ne 0){throw 'Auditoria/circuito requer verificacao'}
 State 'NEXXIM'; & $py (Join-Path $PSScriptRoot 'r16_nexxim.py') *> "$root/nexxim.log"
 if($LASTEXITCODE -ne 0){throw 'Nexxim requer verificacao'}
 & $py (Join-Path $PSScriptRoot 'r17_rastrear.py')
 if($LASTEXITCODE -ne 0){throw 'Rastreabilidade requer verificacao'}
 State 'CONCLUIDO_REVISAR'
}catch{State ('FALHA: '+$_.Exception.Message);throw}
