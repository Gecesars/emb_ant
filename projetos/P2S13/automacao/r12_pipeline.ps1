param([switch]$RetomarPreparado)
$ErrorActionPreference='Stop'
$root='D:/dev/EMBRAER/P2S13/R12_Curvilinear_Simplificado'
$repo='D:/dev/EMBRAER/emb_ant'
$env:P2S13_ROOT=$root
$aedt='C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe'
$python='C:/Users/geral/AppData/Local/Programs/Python/Python312/python.exe'
function Estado($s) { @{estado=$s;hora=(Get-Date).ToString('o');pipeline_pid=$PID} | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $root 'pipeline.json') }
function ConfirmarSetup {
 $v=Get-Content -Raw (Join-Path $root 'hfss_validacao.json') | ConvertFrom-Json
 if($v.validacao -ne 1 -or $v.erros.Count -gt 0) {throw 'Validacao HFSS reprovada'}
 $nativePath=Join-Path $root 'P2S13_Curvilinear.aedt'
 $n=Get-Content -Raw $nativePath
 $curv=[regex]::Match($n,"(?s)\`$begin 'GlobalCurvilinear'(.*?)\`$end 'GlobalCurvilinear'").Groups[1].Value
 if($curv -notmatch 'Apply=true') {throw 'Curvilinear nao confirmado no nativo'}
 foreach($expected in @("DrivenSolverType='Direct Solver'",'BasisOrder=1','MaximumPasses=6','MaxDeltaS=0.05','DoLambdaRefine=false')) {
   if(-not $n.Contains($expected)) {throw ('Setup divergente: '+$expected)}
 }
 $hasher=[System.Security.Cryptography.SHA256]::Create();$stream=[System.IO.File]::OpenRead($nativePath)
 try {$nativeHash=[System.BitConverter]::ToString($hasher.ComputeHash($stream)).Replace('-','').ToLower()} finally {$stream.Dispose();$hasher.Dispose()}
 @{curvilinear=$true;solver='Direct Solver';basis_order=1;max_passes=6;delta_s=.05;nucleos=14;fonte='Nativo salvo e fechado';native_sha256=$nativeHash} | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $root 'setup_confirmado.json')
}
try {
 $cad=Get-Content -Raw (Join-Path $root 'cad/simplificacao.json') | ConvertFrom-Json
 if(-not $cad.aprovado -or $cad.corpos_depois -ne 123) {throw 'CAD nao aprovado'}
 $steps=@('criar_hfss','resolver')
 if($RetomarPreparado) {ConfirmarSetup;$steps=@('resolver')}
 foreach($step in $steps) {
  Estado $step.ToUpper()
  $script=Join-Path $repo "projetos/P2S13/automacao/r12_$step.py"
  $log=Join-Path $root "$step`_aedt.log"
  $p=Start-Process -FilePath $aedt -ArgumentList '-ng','-LogFile',$log,'-RunScriptAndExit',$script -WindowStyle Hidden -PassThru
  $p.Id | Set-Content (Join-Path $root "$step.pid")
  $p.WaitForExit()
  if($step -eq 'criar_hfss') {
    ConfirmarSetup
  } else {
    $q=Get-Content -Raw (Join-Path $root 'qualificacao.json') | ConvertFrom-Json
    if($q.estado -ne 'SOLVE_EXPORTADO_AGUARDA_AUDITORIA') {throw 'Solver nao concluiu exportacao'}
  }
 }
 Estado 'AUDITORIA'
 & $python (Join-Path $repo 'projetos/P2S13/automacao/r12_analisar.py') | Set-Content -Encoding utf8 (Join-Path $root 'auditoria.log')
 if($LASTEXITCODE -ne 0) {throw 'Auditoria falhou'}
 $r=Get-Content -Raw (Join-Path $root 'resultado.json') | ConvertFrom-Json
 if($r.validacao_nominal) {Estado 'CONCLUIDO_METAS_NOMINAIS'} else {Estado 'CONCLUIDO_REQUER_VERIFICACAO'}
} catch {
 Estado ('FALHA: '+$_.Exception.Message)
 throw
}
