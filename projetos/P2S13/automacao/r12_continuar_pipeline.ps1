$ErrorActionPreference='Stop'
$root='D:/dev/EMBRAER/P2S13/R12_Continuacao8'
$env:P2S13_ROOT=$root
$py='C:/Users/geral/AppData/Local/Programs/Python/Python312/python.exe'
function State([string]$s){@{estado=$s;pipeline_pid=$PID;atualizado=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content "$root/pipeline.json" -Encoding utf8}
function Native([string]$stage){
    if(Get-Process hf3d,G3dMesher -ErrorAction SilentlyContinue){throw 'Outro solver ativo'}
    $env:P2S13_ETAPA=$stage
    $p=Start-Process 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe' -ArgumentList @('-ng','-LogFile',"$root/${stage}_aedt.log",'-RunScriptAndExit',(Join-Path $PSScriptRoot 'r12_continuar_aedt.py')) -WindowStyle Hidden -PassThru
    @{pid=$p.Id;etapa=$stage;inicio=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content "$root/processo_$stage.json" -Encoding utf8
    $p.WaitForExit()
}
try{
    if(Test-Path "$root/convergencia.txt"){throw 'Continuacao ja exportada; nao duplicar'}
    if(Test-Path "$root/preparacao_auditada.json"){throw 'Preparacao existente; verificar antes de retomar'}
    State 'AJUSTANDO_LIMITE_SEM_RESET';Native 'preparar'
    & $py (Join-Path $PSScriptRoot 'r12_continuar_auditar.py') preparar *> "$root/auditoria_preparacao.log"
    if($LASTEXITCODE -ne 0){throw 'Preparacao nao preservou setup/malha; nao iniciar solver'}
    State 'RESOLVENDO_PASSES7_E8';Native 'centro'
    $s=Get-Content -Raw "$root/qualificacao.json"|ConvertFrom-Json
    if($s.estado -ne 'SOLVE_EXPORTADO_AGUARDA_AUDITORIA'){throw 'Campos nao exportados'}
    & $py (Join-Path $PSScriptRoot 'r12_continuar_auditar.py') final *> "$root/auditoria_continuidade.log"
    if($LASTEXITCODE -ne 0){throw 'Historico/continuidade nao conferem'}
    State 'ANALISANDO'
    & $py (Join-Path $PSScriptRoot 'r12_continuar_analisar.py') *> "$root/analise.log"
    if($LASTEXITCODE -ne 0){throw 'Analise falhou; conferir analise.log'}
    State 'CONCLUIDO_AGUARDA_COMPARACAO'
}catch{
    @{estado='REQUER_VERIFICACAO';erro=$_.ToString();pipeline_pid=$PID;atualizado=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content "$root/pipeline.json" -Encoding utf8
    throw
}
