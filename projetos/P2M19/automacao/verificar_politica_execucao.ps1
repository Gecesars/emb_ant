$ErrorActionPreference = 'Stop'
$politicaP2M19Path = Join-Path (Split-Path $PSScriptRoot -Parent) 'politica_execucao.json'
if (!(Test-Path -LiteralPath $politicaP2M19Path)) { throw 'Politica de execucao ausente; nao iniciar HFSS.' }
$politicaP2M19 = Get-Content -Raw -LiteralPath $politicaP2M19Path | ConvertFrom-Json
if ($politicaP2M19.simulacoes_suspensas) { throw 'SIMULACOES P2M19 SUSPENSAS PELO USUARIO. Etapa atual: rede e CAD; nenhum solver iniciado.' }
throw 'Executor historico sem guarda de memoria integrado. Para nova execucao autorizada, usar guard_memoria.py com script nativo explicitamente preparado; nao contornar a protecao.'
