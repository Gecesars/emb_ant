param([int]$PipelinePid,[string]$Caso='a00')
$ErrorActionPreference='Stop'
$repo='D:/dev/EMBRAER/emb_ant'
$root=Join-Path 'D:/dev/EMBRAER/P2S13/R11_Fabricavel_Radome' $Caso
$env:P2S13_ROOT=$root
$rfPython='C:/Users/geral/AppData/Local/Programs/Python/Python312/python.exe'
$pdfPython='C:/Users/geral/.codex/tools/pdf/.venv/Scripts/python.exe'
function Estado($s) { @{estado=$s;hora=(Get-Date).ToString('o');pid=$PID;caso=$Caso} | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $root 'posprocessamento.json') }
function Rodar($exe,$argsList) {
 & $exe @argsList
 if($LASTEXITCODE -ne 0) {throw "Falha em $exe, codigo $LASTEXITCODE"}
}
try {
 Estado 'AGUARDANDO_PIPELINE'
 $p=Get-CimInstance Win32_Process -Filter "ProcessId=$PipelinePid"
 if($p) {
  if($p.CommandLine -notlike '*r11_pipeline.ps1*') {throw 'PID nao pertence a fila R11'}
  Wait-Process -Id $PipelinePid
 }
 $q=Get-Content -Raw (Join-Path $root 'pipeline.json') | ConvertFrom-Json
 if($q.estado -ne 'CONCLUIDO_AGUARDA_AUDITORIA') {throw 'Fila nao concluiu: '+$q.estado}
 Estado 'AUDITANDO'
 Rodar $rfPython @((Join-Path $repo 'projetos/P2S13/automacao/r11_analisar.py'))
 Estado 'GERANDO_RELATORIO_PARA_REVISAO'
 Rodar 'node' @('C:/Users/geral/.codex/skills/pdf/container_tools/mark_artifact_operation_started.mjs','--operation-kind','create','--expected-output-count','1','--output-format','pdf')
 Rodar $pdfPython @((Join-Path $repo 'projetos/P2S13/automacao/r11_relatorio.py'))
 Rodar $pdfPython @((Join-Path $repo 'projetos/P2S13/automacao/r11_renderizar_relatorio.py'))
 Estado 'AGUARDA_REVISAO_VISUAL_E_DECISAO_RF'
} catch {
 Estado ('FALHA: '+$_.Exception.Message)
 throw
}
