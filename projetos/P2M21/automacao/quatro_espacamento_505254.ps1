param(
    [string[]]$Variantes = @('v13_passo50_ajustado','v14_passo52_ajustado','v15_passo54_ajustado'),
    [string]$ArquivoEstado = 'fila_505254.json'
)
$ErrorActionPreference = 'Stop'
$taskRoot = 'D:/dev/EMBRAER/P2M21/R11_Divisor_Ajustes'
$taskPython = 'C:/Users/geral/AppData/Local/Programs/Python/Python312/python.exe'
$taskNames = $Variantes
$taskStateFile = Join-Path $taskRoot $ArquivoEstado
$taskDone = @()
try {
    foreach ($taskName in $taskNames) {
        $taskFolder = Join-Path $taskRoot $taskName
        if (Test-Path -LiteralPath (Join-Path $taskFolder 'resultado.json')) { throw "Resultado existente: $taskName; nao duplicar" }
        $taskCad = Get-Content -LiteralPath (Join-Path $taskFolder 'cad/intersecoes.json') -Raw | ConvertFrom-Json
        if (-not $taskCad.aprovado) { throw "CAD reprovado: $taskName" }
        @{estado='EM_EXECUCAO';variante=$taskName;concluidos=$taskDone;atualizado=(Get-Date).ToString('o')} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $taskStateFile -Encoding utf8
        & (Join-Path $PSScriptRoot 'quatro_ajustar_executar.ps1') -Pasta $taskFolder
        & $taskPython (Join-Path $PSScriptRoot 'quatro_ajustar_analisar.py') $taskName
        if ($LASTEXITCODE -ne 0) { throw "Auditoria falhou: $taskName" }
        $taskResult = Get-Content -LiteralPath (Join-Path $taskFolder 'resultado.json') -Raw | ConvertFrom-Json
        if (-not $taskResult.fisica_ok) { throw "Auditoria fisica reprovada: $taskName" }
        $taskDone += $taskName
        Write-Output "VARIANTE_AUDITADA $taskName"
    }
    @{estado='CASOS_CONCLUIDOS_REVISAR_RF';concluidos=$taskDone;quantidade=$taskDone.Count;atualizado=(Get-Date).ToString('o')} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $taskStateFile -Encoding utf8
} catch {
    @{estado='REQUER_VERIFICACAO';variante=$taskName;concluidos=$taskDone;erro=$_.Exception.Message;atualizado=(Get-Date).ToString('o')} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $taskStateFile -Encoding utf8
    throw
}
