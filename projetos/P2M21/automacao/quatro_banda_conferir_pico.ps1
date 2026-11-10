param([Parameter(Mandatory=$true)][string]$Pasta)
$ErrorActionPreference='Stop'
$r13PeakFolder=(Resolve-Path -LiteralPath $Pasta).Path
if(-not $r13PeakFolder.StartsWith('D:\dev\EMBRAER\P2M21\R13_Casamento_Banda\',[StringComparison]::OrdinalIgnoreCase)){throw 'Fora do R13'}
if(Get-Process hf3d,G3dMesher -ErrorAction SilentlyContinue){throw 'Outro solve ativo'}
foreach($name in @('P2M21_4_elementos.aedt.lock','pico_fast.s2p','pico_pipeline.json')){
 if(Test-Path -LiteralPath (Join-Path $r13PeakFolder $name)){throw "Estado existente: $name"}
}
$r13PeakResult=Get-Content -LiteralPath (Join-Path $r13PeakFolder 'resultado.json') -Raw | ConvertFrom-Json
$r13PeakBand=Get-Content -LiteralPath (Join-Path $r13PeakFolder 'banda_auditada.json') -Raw | ConvertFrom-Json
if(-not $r13PeakResult.convergiu -or -not $r13PeakResult.fisica_ok -or $r13PeakResult.passes -gt 6){throw 'Centro sem qualificacao'}
if(-not $r13PeakBand.banda_completa -or -not $r13PeakBand.sem_adaptacao_adicional){throw 'Fast nao auditado'}
$r13Worst=@($r13PeakBand.extremos | Where-Object {$_.condicao -like 'ativo_*'} | Sort-Object maximo -Descending)[0]
$r13PeakFreq=[double]$r13Worst.frequencia_max_GHz
if(@(5.09,5.17,5.25) -contains $r13PeakFreq){
 @{estado='PIOR_FREQUENCIA_JA_CONFERIDA_EM_DISCRETE3';frequencia_GHz=$r13PeakFreq;motivo='O pico Fast coincide com uma frequencia da triagem real existente. Nenhuma nova solucao.'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $r13PeakFolder 'pico_dispensa.json') -Encoding utf8
 Write-Output 'Pico ja incluido na conferencia Discrete3';exit 0
}
$r13PeakHash=(Get-FileHash -LiteralPath (Join-Path $r13PeakFolder 'banda_fast.s2p') -Algorithm SHA256).Hash.ToLowerInvariant()
$r13PeakPlan=@{frequencia_GHz=$r13PeakFreq;condicao=$r13Worst.condicao;VSWR_Fast=$r13Worst.maximo;sha256_banda_fast=$r13PeakHash;criterio='Conferir o pior VSWR ativo Fast em uma frequencia intermediaria; sem nova adaptacao nem campos fora do centro.'}
# IronPython json.open usa UTF-8 sem BOM neste fluxo.
[IO.File]::WriteAllText((Join-Path $r13PeakFolder 'pico_planejado.json'),($r13PeakPlan | ConvertTo-Json),[Text.UTF8Encoding]::new($false))
$env:P2M21_BANDA=$r13PeakFolder
$r13PeakPython='C:/Users/geral/AppData/Local/Programs/Python/Python312/python.exe'
$r13PeakAedt='C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe'
@{estado='DISCRETE_PICO_INICIADO';pid=$PID;inicio=(Get-Date).ToString('o');frequencia_GHz=$r13PeakFreq} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $r13PeakFolder 'pico_pipeline.json') -Encoding utf8
try {
 $r13PeakArgs=@('-ng','-LogFile',(Join-Path $r13PeakFolder 'pico_aedt.log'),'-RunScriptAndExit',(Join-Path $PSScriptRoot 'quatro_banda_pico.py'))
 $r13PeakProcess=Start-Process -FilePath $r13PeakAedt -ArgumentList $r13PeakArgs -WindowStyle Hidden -PassThru
 @{pid=$r13PeakProcess.Id;inicio=(Get-Date).ToString('o');argumentos=$r13PeakArgs} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $r13PeakFolder 'pico_processo.json') -Encoding utf8
 Write-Output "Pico $r13PeakFreq GHz, PID $($r13PeakProcess.Id)"
 $r13PeakProcess.WaitForExit()
 if($r13PeakProcess.ExitCode -ne 0 -or (Test-Path -LiteralPath (Join-Path $r13PeakFolder 'falha_pico.json'))){throw 'Falha na solucao discreta do pico'}
 & $r13PeakPython (Join-Path $PSScriptRoot 'quatro_banda_avaliar.py') pico $r13PeakFolder
 if($LASTEXITCODE -ne 0){throw 'Falha na auditoria do pico'}
 @{estado='PICO_AUDITADO_REVISAR';fim=(Get-Date).ToString('o');frequencia_GHz=$r13PeakFreq} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $r13PeakFolder 'pico_pipeline.json') -Encoding utf8
} catch {
 @{estado='REQUER_VERIFICACAO';erro=$_.Exception.Message} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $r13PeakFolder 'pico_pipeline.json') -Encoding utf8
 throw
}
