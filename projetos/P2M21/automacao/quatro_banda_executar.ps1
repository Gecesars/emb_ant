param([Parameter(Mandatory=$true)][string]$Pasta,[switch]$Triagem,[switch]$TriagemDiagnostica)
$ErrorActionPreference='Stop'
$r13Folder=(Resolve-Path -LiteralPath $Pasta).Path
if(-not $r13Folder.StartsWith('D:\dev\EMBRAER\P2M21\R13_Casamento_Banda\',[StringComparison]::OrdinalIgnoreCase)){throw 'Fora do R13'}
if(Test-Path -LiteralPath (Join-Path $r13Folder 'pipeline.json')){throw 'Fila existente; verificar sem repetir'}
if(Get-Process hf3d,G3dMesher -ErrorAction SilentlyContinue){throw 'Outro solve ativo'}
$r13Python='C:/Users/geral/AppData/Local/Programs/Python/Python312/python.exe'
$r13Aedt='C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe'
$env:P2M21_BANDA=$r13Folder
$env:P2M21_BANDA_TIPO=if($Triagem){'Discrete'}else{'Fast'}
if($TriagemDiagnostica -and -not $Triagem){throw 'Diagnostico permitido apenas na triagem discreta'}
$env:P2M21_BANDA_DIAGNOSTICO='0'
$env:P2M21_BANDA_CALIBRACAO_REJEITADA='0'
@{estado='INICIADO';pid=$PID;inicio=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $r13Folder 'pipeline.json') -Encoding utf8
try {
 foreach($stage in @('criar_hfss','resolver','fast')) {
  if($stage -eq 'fast') {
   & node 'C:/Users/geral/.codex/skills/pdf/container_tools/mark_artifact_operation_started.mjs' --operation-kind create --expected-output-count 1 --output-format pdf
   if($LASTEXITCODE -ne 0){throw 'Marcador de artefato PDF falhou antes da geracao'}
   & $r13Python (Join-Path $PSScriptRoot 'quatro_banda_avaliar.py') centro $r13Folder
   if($LASTEXITCODE -ne 0){throw 'Auditoria central falhou'}
   $r13Gate=Get-Content -LiteralPath (Join-Path $r13Folder 'diagrama_comparado.json') -Raw | ConvertFrom-Json
   if(-not $r13Gate.permitir_fast){
    $r13Failures=@($r13Gate.verificacoes.PSObject.Properties | Where-Object {-not $_.Value} | ForEach-Object {$_.Name})
    $r13DiagnosticOk=$TriagemDiagnostica -and @($r13Failures | Where-Object {$_ -notlike 'apontamento_*'}).Count -eq 0
    if(-not $r13DiagnosticOk){Write-Output 'CENTRO_REPROVADO_PARA_FAST';break}
    $env:P2M21_BANDA_DIAGNOSTICO='1'
    Write-Output 'TRIAGEM_DIAGNOSTICA_SEM_LIBERACAO_DO_DIAGRAMA'
   }
   $r13Script=Join-Path $PSScriptRoot 'quatro_banda_fast.py'
  } else {$r13Script=Join-Path $r13Folder ($stage+'.py')}
  $r13Args=@('-ng','-LogFile',(Join-Path $r13Folder ($stage+'_aedt.log')),'-RunScriptAndExit',$r13Script)
  $r13Proc=Start-Process -FilePath $r13Aedt -ArgumentList $r13Args -WindowStyle Hidden -PassThru
  @{etapa=$stage;pid=$r13Proc.Id;inicio=(Get-Date).ToString('o');argumentos=$r13Args} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $r13Folder ($stage+'_processo.json')) -Encoding utf8
  Write-Output "$stage PID $($r13Proc.Id)";$r13Proc.WaitForExit()
  if($r13Proc.ExitCode -ne 0 -or (Test-Path -LiteralPath (Join-Path $r13Folder 'falha.json')) -or (Test-Path -LiteralPath (Join-Path $r13Folder 'falha_fast.json')) -or (Test-Path -LiteralPath (Join-Path $r13Folder 'falha_triagem3.json'))){throw "Falha na etapa $stage"}
  if($stage -eq 'criar_hfss'){$v=Get-Content -LiteralPath (Join-Path $r13Folder 'hfss_validacao.json') -Raw | ConvertFrom-Json;if($v.validacao -ne 1 -or $v.erros.Count){throw 'Modelo invalido'}}
  if($stage -eq 'fast'){& $r13Python (Join-Path $PSScriptRoot 'quatro_banda_avaliar.py') fast $r13Folder;if($LASTEXITCODE -ne 0){throw 'Auditoria Fast falhou'}}
 }
 @{estado='ETAPAS_CONCLUIDAS_REVISAR';fim=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $r13Folder 'pipeline.json') -Encoding utf8
} catch {
 @{estado='REQUER_VERIFICACAO';etapa=$stage;erro=$_.Exception.Message} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $r13Folder 'pipeline.json') -Encoding utf8
 throw
}
