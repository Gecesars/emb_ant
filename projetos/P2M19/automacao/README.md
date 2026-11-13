# Automação local da P2M19

A continuação solicitada após o lote usa `R05_72mm_ref146_8passes`: uma cópia integral da R04 fechada, com malha e campos nativos preservados. `preparar_continuacao8.py` cria essa cópia uma única vez; `continuacao8_resolver.py` altera por API somente mínimo/máximo para oito passes, compara os blocos físicos e preserva os nove identificadores de campo. `continuacao8_continuar.ps1` executa apenas os passes 7/8 e a análise, sem recriar CAD, malha inicial ou sweep. Não repetir o preparador nem o solver sobre uma execução existente.

Consulta da continuação: `python projetos/P2M19/automacao/monitorar_continuacao8.py`. O acompanhamento ocorre neste trabalho; não há agendamento recorrente nem autorização implícita para passes além de oito. `finalizar_continuacao8.py` compara o histórico preservado e gera a documentação; a opção `--empacotar` exige revisão visual dos quatro gráficos e exclui resultados nativos volumétricos e malhas do Git.

O estudo de 13/11/2026 usa uma fila **finita**, executada neste computador. Não é um agendamento recorrente do Codex. Os casos são resolvidos em sequência para respeitar a memória disponível:

1. R02: colunas a 72 mm, refletor de 178 mm, para comparação direta com a R01 de 88 mm.
2. R03: colunas a 72 mm, refletor de 162 mm.
3. R04: colunas a 72 mm, refletor de 146 mm.

Todos mantêm 16 níveis, oito placas C12, 16 entradas iguais de 0,0625 W / 0°, 14 núcleos, 5,17 GHz, no máximo seis passes e alvo ΔS de 0,05. Não há sweep. O limite é aplicado separadamente a cada nova geometria; não há continuação adaptativa automática de um caso concluído.

`fila_refletores.py` acompanha uma execução já existente somente após conferir o PID e sua linha de comando. Antes de iniciar o próximo caso, verifica configurações, hashes dos scripts, CAD, ausência de outro solver, memória e disco. Erros de execução, reparos Major ou inconsistência física interrompem a fila. A falta de convergência é registrada e o resultado permanece exploratório; não é convertido em aprovação.

Estado e logs: `D:/dev/EMBRAER/P2M19/Campanha_72mm_20261113`. Para consultar sem alterar os projetos:

```powershell
python D:/dev/EMBRAER/emb_ant/projetos/P2M19/automacao/monitorar_estudos.py
```

Criar o arquivo `PARAR_APOS_CASO` na pasta da campanha impede o início do próximo caso, preservando a solução em andamento. Não iniciar outro controlador, excluir marcadores nem repetir `executar_estudo.ps1` sem examinar os processos e os logs. Uma falha de análise ou exportação deve ser corrigida usando a solução existente, sem repetir o cálculo.

Após o lote, `comparar_estudos.py` gera tabelas e gráficos. `empacotar_estudos.py` exige revisão visual registrada e copia nativos, S16, campos distantes e evidências; exclui malhas, resultados volumétricos e locks. A verificação do índice Git usa:

```powershell
python D:/dev/EMBRAER/emb_ant/projetos/P2M19/automacao/verificar_pacote.py --pacote estudo_72mm
```

A comparação com a R01 deve indicar sua falta de convergência. Ganho total coerente não caracteriza ganho por entrada MIMO nem inclui a futura rede externa de distribuição.
