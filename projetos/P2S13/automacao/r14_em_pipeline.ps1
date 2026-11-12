$ErrorActionPreference='Stop'
$root='D:/dev/EMBRAER/P2S13/R14_Compacto_Simetrico_SemRadome/c00'
$py='C:/Users/geral/AppData/Local/Programs/Python/Python312/python.exe'
$env:P2S13_DIV3_ROOT="$root/divisor"
function State($s){@{estado=$s;hora=(Get-Date).ToString('o');pipeline_pid=$PID}|ConvertTo-Json|Set-Content "$root/em_pipeline.json" -Encoding utf8}
try{
 if(Test-Path "$root/divisor/Divisor_Duplo3.aedt"){throw 'Divisor preexistente; nao duplicar'}
 foreach($step in @('divisor','antena_criar','antena_resolver')){
  if(Get-Process hf3d,G3dMesher -ErrorAction SilentlyContinue){throw 'Outro solver ativo'}
  $env:P2S13_ROOT="$root/antena"
  $script=@{divisor='r14_divisor_hfss.py';antena_criar='r14_antena_criar_hfss.py';antena_resolver='r14_antena_resolver.py'}[$step]
  State $step.ToUpper()
  $p=Start-Process 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe' -ArgumentList @('-ng','-LogFile',"$root/em_$step.log",'-RunScriptAndExit',(Join-Path $PSScriptRoot $script)) -WindowStyle Hidden -PassThru
  $p.Id|Set-Content "$root/em_$step.pid";$p.WaitForExit()
  if($step -eq 'divisor'){
   $v=Get-Content -Raw "$root/divisor/estado.json"|ConvertFrom-Json
   if($v.estado -ne 'CONCLUIDO_AGUARDA_ANALISE'){throw 'Divisor nao exportado'}
  }elseif($step -eq 'antena_criar'){
   $v=Get-Content -Raw "$root/antena/hfss_validacao.json"|ConvertFrom-Json
   if($v.validacao -ne 1 -or $v.erros.Count -gt 0){throw 'Antena nao validada'}
  }else{
   $v=Get-Content -Raw "$root/antena/qualificacao.json"|ConvertFrom-Json
   if($v.estado -ne 'SOLVE_EXPORTADO_AGUARDA_AUDITORIA'){throw 'Antena nao exportada'}
  }
 }
 State 'EM_CONCLUIDO_AGUARDA_CIRCUITO_NEXXIM'
}catch{State ('FALHA: '+$_.Exception.Message);throw}
