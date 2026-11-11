param([Parameter(Mandatory=$true)][int]$AguardarPID)
$ErrorActionPreference='Stop'
$study='D:/dev/EMBRAER/P2S13/R04_Dobras_Ajustadas'
if(Test-Path "$study/interrupcao.json"){throw 'Campanha4+2 interrompida pelo usuario; nao retomar'}
function Gate([string]$name){
    $r=Get-Content -Raw "$study/$name/resultado.json"|ConvertFrom-Json
    if($r.major -ne 0 -or !$r.verificacoes.passividade -or !$r.verificacoes.eficiencia_e_balanco){throw "Falha fisica em $name; investigar antes de continuar"}
    if(Get-Process hf3d,G3dMesher -ErrorAction SilentlyContinue){throw 'Solver ainda ativo'}
}
try{
    $p=Get-CimInstance Win32_Process -Filter "ProcessId=$AguardarPID"
    if($p){
        if($p.CommandLine -notmatch 'dobras2_pipeline.ps1.*d01_b20_a120'){throw 'PID nao pertence ao segundo caso'}
        Wait-Process -Id $AguardarPID
    }
    Gate 'd01_b20_a120'
    foreach($name in @('d02_b20_a150','d03_b3_a45')){
        & pwsh -NoProfile -File (Join-Path $PSScriptRoot 'dobras2_pipeline.ps1') -Variante $name
        if($LASTEXITCODE -ne 0){throw "Pipeline falhou: $name"}
        Gate $name
    }
    [pscustomobject]@{estado='FILA_CONCLUIDA';fim=(Get-Date).ToString('o');pid=$PID}|ConvertTo-Json|Set-Content "$study/fila.json" -Encoding utf8
}catch{
    [pscustomobject]@{estado='REQUER_VERIFICACAO';erro=$_.ToString();pid=$PID}|ConvertTo-Json|Set-Content "$study/fila.json" -Encoding utf8
    throw
}
