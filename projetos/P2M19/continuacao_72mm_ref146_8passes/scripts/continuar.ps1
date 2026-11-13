param([Parameter(Mandatory=$true)][string]$Pasta)
$ErrorActionPreference='Stop'
$casePath=(Resolve-Path -LiteralPath $Pasta).Path
if(!$casePath.StartsWith('D:\dev\EMBRAER\P2M19\')){throw 'Pasta fora da campanha P2M19'}
function State([string]$value) {
    [pscustomobject]@{estado=$value;pipeline_pid=$PID;atualizado=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $casePath 'pipeline.json') -Encoding utf8
}
function Native([string]$script,[string]$stage) {
    if(Get-Process hf3d,G3dMesher -ErrorAction SilentlyContinue){throw 'Outro solver ativo; não duplicar nem executar em paralelo'}
    $scriptPath=Join-Path $casePath "scripts/$script"
    $p=Start-Process 'C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe' -ArgumentList @('-ng','-LogFile',(Join-Path $casePath "${stage}_aedt.log"),'-RunScriptAndExit',$scriptPath) -WindowStyle Hidden -PassThru
    $nativeHandle=$p.Handle
    [pscustomobject]@{pid=$p.Id;script=$script;inicio=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $casePath "processo_$stage.json") -Encoding utf8
    $p.WaitForExit()
    if($null -eq $p.ExitCode -or $p.ExitCode -ne 0){throw "AEDT $stage encerrou com codigo $($p.ExitCode)"}
}
try {
    if(Test-Path -LiteralPath (Join-Path $casePath 'processo_centro.json')){throw 'Continuacao ja iniciada; verificar antes de retomar'}
    State 'CONTINUANDO_PASSES_7_E_8'
    Native 'resolver.py' 'centro'
    State 'ANALISANDO'
    $a=Start-Process python -ArgumentList @((Join-Path $casePath 'scripts/analisar.py')) -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput (Join-Path $casePath 'analise.log') -RedirectStandardError (Join-Path $casePath 'analise_erro.log')
    [pscustomobject]@{pid=$a.Id;exit_code=$a.ExitCode;atualizado=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $casePath 'analise_exitcode.json') -Encoding utf8
    if($null -eq $a.ExitCode -or $a.ExitCode -ne 0){throw 'Falha ou codigo de saida ausente no pos-processamento; consultar analise_erro.log. Nao repetir solve.'}
    State 'CONCLUIDO_AGUARDA_REVISAO'
} catch {
    [pscustomobject]@{estado='REQUER_VERIFICACAO';erro=$_.ToString();pipeline_pid=$PID;atualizado=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $casePath 'pipeline.json') -Encoding utf8
    throw
}
