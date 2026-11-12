param([string]$Caso='c01')
$ErrorActionPreference='Stop'
$base='D:/dev/EMBRAER/P2S13/R15_Casamento_C09'
$root=Join-Path $base $Caso
$py='C:/Users/geral/AppData/Local/Programs/Python/Python312/python.exe'
$env:P2S13_R15_CASE=$root;$env:P2S13_DIV3_ROOT="$root/divisor"
Remove-Item Env:P2S13_GUIA -ErrorAction SilentlyContinue
function State($s){@{estado=$s;hora=(Get-Date).ToString('o');pipeline_pid=$PID;caso=$Caso}|ConvertTo-Json|Set-Content "$root/pipeline.json" -Encoding utf8}
try{
 if(Test-Path "$root/divisor/Divisor_Duplo3.aedt"){throw 'Nativo existente: nao duplicar'}
 while(Get-Process hf3d,G3dMesher -ErrorAction SilentlyContinue){State 'AGUARDANDO_OUTRO_FEM';Start-Sleep -Seconds 15}
 State 'HFSS_DIVISOR'
 $p=Start-Process 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe' -ArgumentList @('-ng','-LogFile',"$root/hfss_aedt.log",'-RunScriptAndExit',(Join-Path $PSScriptRoot 'r15_hfss.py')) -WindowStyle Hidden -PassThru
 $p.Id|Set-Content "$root/hfss.pid";$p.WaitForExit()
 $v=Get-Content -Raw "$root/divisor/estado.json"|ConvertFrom-Json
 if($v.estado -ne 'CONCLUIDO_AGUARDA_ANALISE'){throw 'HFSS nao exportado'}
 State 'AUDITAR_E_RECOMPOR'
 & $py (Join-Path $PSScriptRoot 'r15_circuito.py') *> "$root/circuito.log"
 if($LASTEXITCODE -ne 0){throw 'Auditoria ou circuito falhou'}
 State 'NEXXIM_CONFIRMACAO'
 & $py (Join-Path $PSScriptRoot 'r15_nexxim.py') *> "$root/nexxim.log"
 if($LASTEXITCODE -ne 0){throw 'Nexxim requer verificacao'}
 State 'CONCLUIDO_REVISAR'
}catch{State ('FALHA: '+$_.Exception.Message);throw}
