# Automação local da P2M19

A continuação seguinte usa `R07_72mm_ref146_12passes` e executa apenas os passes **11 e 12**. `preparar_continuacao12.py` preserva a R06 e todos os seus resultados. A retomada primeiro limita o total a 11, exporta S16, potência e cortes H/V completos/fino desse passe, salva e fecha; depois altera somente mínimo/máximo para 12 e continua a mesma malha. Não há reconstrução de geometria ou reinício de contagem. `estabilidade_continuacao12.py` compara os passes 10/11/12, verifica a fonte de 1 W, potência e dados intermediários, e quantifica mudanças de ganho, abertura, apontamento, lóbulos, VSWR e forma normalizada dos cortes. Os diagramas do passe 11 são campos reais exportados, não interpolação. O critério de parada permanece ΔS 0,05; a estabilidade das nove sondas continua sendo monitoramento, sem alterar o limite autorizado. Consultar `monitorar_continuacao12.py` e os logs antes de qualquer intervenção.

A exportação RF do passe 11 terminou, mas houve erro de codificação do IronPython ao gravar o JSON do checkpoint. `recuperar_continuacao12.py` conferiu o nativo salvo por SHA-256, recuperou somente os metadados com Python 3 e preparou uma retomada exclusiva do passe 12. A leitura do hash no AEDT usa bytes via .NET, evitando conversão de texto. Os logs anteriores e o histórico permanecem preservados; nenhum cálculo RF foi repetido. O preparador foi corrigido para escrever o JSON antes de iniciar o HFSS. Os controladores agora também conferem o marcador de falha e a exportação final, pois o AEDT pode retornar código zero mesmo quando um script falha.

A solicitação de 14/11 acrescenta somente os passes **9 e 10** sobre a R05 de oito passes. `preparar_continuacao10.py` copia e verifica integralmente seus resultados em `R06_72mm_ref146_10passes`; a API altera somente mínimo/máximo para dez. `continuacao10_continuar.ps1` executa a retomada e o pós-processamento; `monitorar_continuacao10.py` consulta o andamento sem alterar o solver. `finalizar_continuacao10.py` verifica que o histórico 1–8 permaneceu idêntico, compara 8/10 e empacota os arquivos após revisão dos gráficos. Permanecem 14 núcleos, 5,17 GHz, 16 fontes iguais/em fase, ΔS 0,05 e nenhuma varredura. Nenhum desses scripts deve ser repetido sobre uma execução já iniciada.

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
