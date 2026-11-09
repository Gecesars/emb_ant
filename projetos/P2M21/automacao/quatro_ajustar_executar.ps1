param([Parameter(Mandatory=$true)][string]$Pasta)
$ErrorActionPreference = 'Stop'
$destino = (Resolve-Path -LiteralPath $Pasta).Path
if (-not $destino.StartsWith('D:\dev\EMBRAER\P2M21\R11_Divisor_Ajustes\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Pasta fora do estudo R11.' }
if (Test-Path -LiteralPath (Join-Path $destino 'convergencia.txt')) { throw 'Resultado existente: nao repetir.' }
if (Get-Process hf3d,G3dMesher -ErrorAction SilentlyContinue) { throw 'Outro solver ativo: serializar.' }
$aedt = 'C:\Program Files\AnsysEM\v242\Win64\ansysedt.exe'
foreach ($etapa in @('criar_hfss','resolver')) {
    $script = Join-Path $destino ($etapa+'.py')
    $registro = Join-Path $destino ($etapa+'_aedt.log')
    $proc = Start-Process -FilePath $aedt -ArgumentList @('-ng','-LogFile',$registro,'-RunScriptAndExit',$script) -WindowStyle Hidden -PassThru
    [pscustomobject]@{etapa=$etapa;pid=$proc.Id;inicio=(Get-Date).ToString('o');argumentos=@('-ng','-LogFile',$registro,'-RunScriptAndExit',$script)} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $destino ($etapa+'_processo.json')) -Encoding utf8
    Write-Output "$etapa PID $($proc.Id)"
    $proc.WaitForExit()
    if ($proc.ExitCode -ne 0) { throw "$etapa saiu com codigo $($proc.ExitCode)." }
    if ($etapa -eq 'criar_hfss') {
        $validacao=Get-Content -Raw -LiteralPath (Join-Path $destino 'hfss_validacao.json') | ConvertFrom-Json
        if ($validacao.validacao -ne 1 -or $validacao.erros.Count -ne 0) { throw 'Validacao HFSS falhou.' }
    } else {
        $estado=Get-Content -Raw -LiteralPath (Join-Path $destino 'qualificacao.json') | ConvertFrom-Json
        if ($estado.estado -ne 'SOLVE_EXPORTADO_AGUARDA_AUDITORIA') { throw 'Exportacao incompleta.' }
    }
}
Write-Output 'SOLVE_E_EXPORTACAO_CONCLUIDOS'
