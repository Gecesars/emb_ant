param([string]$Caso='dn100_c01')
$ErrorActionPreference='Stop'
$root="D:/dev/EMBRAER/P2S13/R16_Tubo_PVC/$Caso"
$py='C:/Users/geral/AppData/Local/Programs/Python/Python312/python.exe'
$env:P2S13_R16_CASE=$root;$env:P2S13_ROOT="$root/divisor";$env:P2S13_DIV3_ROOT="$root/divisor"
function State($s){@{estado=$s;hora=(Get-Date).ToString('o');pipeline_pid=$PID}|ConvertTo-Json|Set-Content "$root/pipeline.json" -Encoding utf8}
function Aedt($script,$log){
 $p=Start-Process 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe' -ArgumentList @('-ng','-LogFile',"$root/$log",'-RunScriptAndExit',(Join-Path $PSScriptRoot $script)) -WindowStyle Hidden -PassThru
 $p.Id|Set-Content "$root/aedt_atual.pid";$p.WaitForExit()
 if($p.ExitCode -ne 0){throw "AEDT $script codigo $($p.ExitCode)"}
}
try{
 if(Test-Path "$root/divisor/Divisor_Duplo3.aedt"){throw 'Nao duplicar nativo existente'}
 while(Get-Process hf3d,G3dMesher -ErrorAction SilentlyContinue){State 'AGUARDANDO_OUTRO_FEM';Start-Sleep -Seconds 15}
 State 'CRIAR_DIVISOR';Aedt 'r16_ajuste_criar.py' 'criar_aedt.log'
 State 'ACRESCENTAR_TUBO';Aedt 'r16_adicionar_tubo.py' 'tubo_aedt.log'
 State 'HFSS_DIVISOR';Aedt 'r16_divisor_resolver.py' 'divisor_aedt.log'
 if(-not(Test-Path "$root/divisor/divisor.s8p")){throw 'S8 nao exportado'}
 State 'CIRCUITO'; & $py (Join-Path $PSScriptRoot 'r16_circuito.py') *> "$root/circuito.log"
 if($LASTEXITCODE -ne 0){throw 'Auditoria/circuito requer verificacao'}
 State 'NEXXIM'; & $py (Join-Path $PSScriptRoot 'r16_nexxim.py') *> "$root/nexxim.log"
 if($LASTEXITCODE -ne 0){throw 'Nexxim requer verificacao'}
 State 'CONCLUIDO_REVISAR'
}catch{State ('FALHA: '+$_.Exception.Message);throw}
