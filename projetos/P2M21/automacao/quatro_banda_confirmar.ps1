param([Parameter(Mandatory=$true)][string]$Pasta)
$ErrorActionPreference='Stop'
$r13Folder=(Resolve-Path -LiteralPath $Pasta).Path
if(-not $r13Folder.StartsWith('D:\dev\EMBRAER\P2M21\R13_Casamento_Banda\',[StringComparison]::OrdinalIgnoreCase)){throw 'Fora do R13'}
if(Get-Process hf3d,G3dMesher -ErrorAction SilentlyContinue){throw 'Outro solve ativo'}
foreach($name in @('P2M21_4_elementos.aedt.lock','banda_fast.s2p','confirmacao_pipeline.json')){
 if(Test-Path -LiteralPath (Join-Path $r13Folder $name)){throw "Estado existente: $name; verificar antes de continuar"}
}
$r13Read={param($name) Get-Content -LiteralPath (Join-Path $r13Folder $name) -Raw | ConvertFrom-Json}
$r13Result=& $r13Read 'resultado.json'
$r13Gate=& $r13Read 'diagrama_comparado.json'
$r13Band=& $r13Read 'triagem3_auditada.json'
if(-not $r13Result.convergiu -or -not $r13Result.fisica_ok){throw 'Centro nao qualificado fisicamente'}
if($r13Band.pontos -ne 3 -or -not $r13Band.ativos_ate_meta){throw 'A triagem ainda nao atende a meta ativa'}
$r13Failures=@($r13Gate.verificacoes.PSObject.Properties | Where-Object {-not $_.Value} | ForEach-Object {$_.Name})
if(@($r13Failures | Where-Object {$_ -notlike 'apontamento_*'}).Count){throw 'Criterios centrais adicionais reprovados'}
$env:P2M21_BANDA=$r13Folder
$env:P2M21_BANDA_TIPO='Fast'
$env:P2M21_BANDA_CALIBRACAO_REJEITADA='0'
$env:P2M21_BANDA_DIAGNOSTICO=if($r13Failures.Count){'1'}else{'0'}
$r13Python='C:/Users/geral/AppData/Local/Programs/Python/Python312/python.exe'
$r13Aedt='C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe'
@{estado='FAST_INICIADO';pid=$PID;inicio=(Get-Date).ToString('o');ressalvas=$r13Failures} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $r13Folder 'confirmacao_pipeline.json') -Encoding utf8
try {
 $r13Args=@('-ng','-LogFile',(Join-Path $r13Folder 'confirmacao_fast_aedt.log'),'-RunScriptAndExit',(Join-Path $PSScriptRoot 'quatro_banda_fast.py'))
 $r13Proc=Start-Process -FilePath $r13Aedt -ArgumentList $r13Args -WindowStyle Hidden -PassThru
 @{pid=$r13Proc.Id;inicio=(Get-Date).ToString('o');argumentos=$r13Args} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $r13Folder 'confirmacao_processo.json') -Encoding utf8
 Write-Output "Fast PID $($r13Proc.Id)"
 $r13Proc.WaitForExit()
 if($r13Proc.ExitCode -ne 0 -or (Test-Path -LiteralPath (Join-Path $r13Folder 'falha_fast.json'))){throw 'Falha no Fast'}
 & $r13Python (Join-Path $PSScriptRoot 'quatro_banda_avaliar.py') fast $r13Folder
 if($LASTEXITCODE -ne 0){throw 'Falha na auditoria Fast'}
 @{estado='FAST_AUDITADO_REVISAR';fim=(Get-Date).ToString('o');ressalvas=$r13Failures} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $r13Folder 'confirmacao_pipeline.json') -Encoding utf8
} catch {
 @{estado='REQUER_VERIFICACAO';erro=$_.Exception.Message} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $r13Folder 'confirmacao_pipeline.json') -Encoding utf8
 throw
}
