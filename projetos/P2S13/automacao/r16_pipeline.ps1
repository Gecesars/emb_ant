param([string]$Caso='dn100')
$ErrorActionPreference='Stop'
$root="D:/dev/EMBRAER/P2S13/R16_Tubo_PVC/$Caso"
$py='C:/Users/geral/AppData/Local/Programs/Python/Python312/python.exe'
$env:P2S13_R16_CASE=$root
function State($s){@{estado=$s;hora=(Get-Date).ToString('o');pipeline_pid=$PID}|ConvertTo-Json|Set-Content "$root/pipeline.json" -Encoding utf8}
function Aedt($script,$log){
 $p=Start-Process 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe' -ArgumentList @('-ng','-LogFile',"$root/$log",'-RunScriptAndExit',(Join-Path $PSScriptRoot $script)) -WindowStyle Hidden -PassThru
 $p.Id|Set-Content "$root/aedt_atual.pid";$p.WaitForExit()
 if($p.ExitCode -ne 0){throw "AEDT $script terminou com codigo $($p.ExitCode)"}
}
try{
 foreach($block in @('antena','divisor')){
   $env:P2S13_ROOT="$root/$block"
   if(-not(Test-Path "$root/$block/tubo_criado.json")){throw "Tubo nao preparado em $block"}
   if(Test-Path "$root/$block/convergencia.txt"){throw "Resultado existente em ${block}: nao duplicar"}
   while(Get-Process hf3d,G3dMesher -ErrorAction SilentlyContinue){State "AGUARDANDO_OUTRO_FEM_$block";Start-Sleep -Seconds 15}
   State "HFSS_$block"
   if($block -eq 'antena'){
     Aedt 'r14_antena_resolver.py' 'antena_aedt.log'
     if(-not(Test-Path "$root/antena/centro.s6p")){throw 'S6 nao exportado'}
   }else{
     Aedt 'r16_divisor_resolver.py' 'divisor_aedt.log'
     if(-not(Test-Path "$root/divisor/divisor.s8p")){throw 'S8 nao exportado'}
   }
 }
 State 'AUDITORIA_E_CIRCUITO'
 & $py (Join-Path $PSScriptRoot 'r16_circuito.py') *> "$root/circuito.log"
 if($LASTEXITCODE -ne 0){throw 'Auditoria/circuito requer verificacao'}
 State 'NEXXIM'
 & $py (Join-Path $PSScriptRoot 'r16_nexxim.py') *> "$root/nexxim.log"
 if($LASTEXITCODE -ne 0){throw 'Nexxim requer verificacao'}
 State 'CONCLUIDO_REVISAR'
}catch{State ('FALHA: '+$_.Exception.Message);throw}
