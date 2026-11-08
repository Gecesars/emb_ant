# R06 · reprodução do método separado

O estudo de trabalho fica em `D:/dev/EMBRAER/P1H/R06_sem_cabos`. HFSS/AEDT 2024 R2, FreeCAD 1.1 e Python 3.12 com NumPy, SciPy, scikit-rf e PyAEDT. O gerador PDF usa o ambiente da skill PDF com ReportLab.

1. `pcb_cad.py` e `divisores_cad.py` extraem as PCBs completas e criam as terminações locais. Variáveis `P1H_R06` e `P1H_CAD_BASE` indicam o destino e os STEP por material do cobre sólido R05.
2. `pcb_hfss.py` resolve a PCB completa com vinte portas e nove amostras de convergência de campo. `divisores_hfss.py` resolve as duas distribuidoras completas, de dezoito e doze portas, com varredura discreta de 17 frequências. Serializar os cálculos grandes.
3. `auditar_convergencia.py` confere os arquivos nativos EMConvData/ExprCache. O estado intermediário `IsConverged=true` sozinho não basta; exigir dois passes em S e campo.
4. `extrair_campos.py` exporta os vinte padrões complexos H/V após convergência. `refinar_pcb.py` prepara a verificação local dos pequenos fragmentos de cobre e das soldas. Antes de executá-lo, preservar os S/parâmetros, campos exportados e histórico da malha inicial.
5. `analisar_divisores.py` verifica passividade, reciprocidade, frequência e convergência, e caracteriza as redes com saídas casadas. `circuito.py` monta as matrizes completas, resolve as reflexões e recompõe os campos, com balanço de potência e controle de alimentação uniforme.
6. `circuito_aedt.py` cria e resolve o mesmo circuito no Nexxim e compara a matriz de duas portas com o cálculo independente. Usa os componentes Touchstone reais gerados pela etapa anterior. `validar_nexxim.py` conferiu a API e a ordem das portas contra um cupom S2 real, com erro máximo de 7,51 × 10⁻¹⁵. O arquivo `.aedtz` do circuito inclui os arquivos externos e exclui resultados de solver.
7. `auditar_malha.py` extrai apenas os cabeçalhos do g3derr e conta corpos distintos, sem copiar triângulos. `comparar_malhas.py` aplica a mesma rede às malhas inicial e refinada. `qualificar.ps1` coordena a sequência e interrompe em caso de falha; ler `qualificacao.json` antes de iniciar qualquer nova instância. O watcher `fila_divisores.ps1` já serializa as duas distribuidoras.
8. `graficos.py`, `diagrama_rede.py`, `imagens_freecad.py` e `relatorio.py` geram as figuras e o relatório. A opção `--rascunho` explicita as métricas ainda pendentes; o relatório final exige convergência, estabilidade da malha e aceite. `verificar_fabricacao.py` consolida DRC e hashes dos Gerbers.
9. Após a revisão visual do PDF final, `empacotar.py` copia somente os nativos e as evidências necessárias e confere os SHA-256. O pós-processamento pode usar `resultados/r06` como raiz: os cupons da bobina e do controle acompanham o pacote.

Os cabos não são simulados junto à antena. Suas linhas ideais têm módulo unitário. N é uma interface ideal. As bobinas usam os cupons R05 já resolvidos; a comparação inclui o cupom bruto e a remoção simétrica da atenuação dos acessos, mantendo a fase. O resultado final é de **5,17 GHz**; a PCB não deve ser congelada para declarar ganho de banda.

As malhas `.aedtresults`, `*.g3derr`, campos volumétricos e temporários ficam apenas no diretório de trabalho. O PDF final deve ser renderizado e revisado em todas as páginas antes da entrega.

## Ajuste de fase e recuperação de 7/11

`configuracao_circuito.json` define os comprimentos físicos `[entrada, enlace, ramal]`, em mm. A seleção atual é `[290, 132, 133]`; a configuração acompanha o pacote. `explorar_fase.py` varia as linhas ideais com matrizes de um ponto e não inicia nova simulação eletromagnética. Preservar a distinção entre seleção com a primeira malha e aceite com a refinada.

`circuito.py` atribui os nomes das portas após construir cada `skrf.Network`, pois o argumento no construtor não os conserva nesta versão. O exportador reimporta as matrizes e confere nomes e números. `circuito_aedt.py --subdir circuito_preliminar_133` permite confrontar um candidato sem sobrescrever o circuito final.

`retomar_divisor.py` foi usado após confirmar a falha de licença e o encerramento dos processos próprios. Abre o projeto salvo, preserva e exporta o centro e retoma a varredura; não altera a configuração global de licença. `qualificar.ps1 -AposBaseline` retoma depois de uma baseline preservada e exige ausência de refinamento já iniciado. Não usar para iniciar outro cálculo enquanto o pipeline atual estiver ativo.

Na GUI FreeCAD, `atualizar_imagens.py` sincroniza apenas o clone visual próprio, compara os 275 objetos externos ao chicote e confere igualdade de todas as formas com o CAD selecionado. Os envelopes usam `optimalBoundingBox(False, False)` para não depender da triangulação de tela. `preparar_mecanica.py` copia nativos e chapa preservada para a pasta de trabalho `mecanica`, cria a lista dos 26 cabos e a rastreabilidade. `desenho_fabricacao.py` gera as três pranchas A3 com os comprimentos selecionados. R05 permanece como histórico.

## Continuação para estabilidade da abertura horizontal

`apertar_convergencia.py` continua o setup existente com ΔS 0,004 e campo 0,02 dB, mínimo 13 e máximo 24 passes, sem resetar a malha ou a geometria. Os dados de 11 passes ficam em `antena_refinada1`. `continuar_qualificacao.ps1` coordena essa etapa e o pós-processamento, interrompendo em qualquer reprovação.

`auditar_convergencia.py` lê os critérios efetivamente salvos no nativo e usa o menor entre eles e os critérios originais. `auditar_malha.py` aceita `malha_execucao.json` com início ISO, filtra os metadados TimeStamp dos blocos e mantém as contagens históricas. Isso evita atribuir à malha atual avisos acumulados de outra execução. `comparar_malhas.py --referencia antena_refinada1` mantém todas as tolerâncias e confronta duas etapas com a mesma discretização superficial, refinadas globalmente em sequência.

A edição de critérios reatribuiu os TraceID do cache, mas o solver continuou no passe 12. `cache_continuacao.json` identifica a auditoria preservada por SHA-256. O auditor recupera apenas campos ausentes dos passes anteriores e exige igualdade de número de tetraedros em cada passe; os passes novos vêm do cache nativo atual.

O AEDT também conserva EMConvData da configuração anterior. O auditor seleciona o histórico cujos ΔS alvo, máximo e mínimo de passes coincidem com o setup salvo no nativo; não usa o antigo `IsConverged=true` para aprovar a continuação. A seleção foi verificada com cópias dos metadados reais V444/V617, sem alterar arquivos do solver ativo.


`continuar_qualificacao.ps1 -EstabilidadeFinal` usa `validar_estabilidade.py` e a referência congelada `antena_estrita21`. Mantém ΔS 0,004, campo 0,02 dB, refinamento de 15% e a mesma malha; exige mínimo 23 e máximo 25 passes. O setup é atualizado pela API nativa, pois a serialização do contexto de campo do PyAEDT não foi aceita nesta release. Não reexecutar enquanto `estabilidade_final.log` existir sem examinar o estado. A execução de 21 passes e a comparação anterior reprovada são preservadas.

Essa tentativa falhou por `SOLVER_OUT_OF_MEMORY` no passe 22, às 23:45 de 7/11. A recuperação usa `continuar_qualificacao.ps1 -EstabilidadeFinal -RecuperarMemoria`: restaura o nativo de 21 passes (SHA conferido) com os resultados locais preservados e reduz apenas o crescimento da malha para 5% por passe. Mantém mínimo 23 / máximo 25, ΔS 0,004, nove campos 0,02 dB por dois passes, geometria, solver iterativo e todas as tolerâncias de estabilidade.

`testar_edicao_parcial.py` foi executado em uma cópia sem solver. Confirmou que a edição parcial preserva todas as propriedades do setup, exceto mínimo/máximo de passes e percentual de refinamento, incluindo os nove TraceID 672–680. `recuperar_memoria.py` repete essa comparação exata antes de analisar. É necessário salvar **e fechar** o projeto antes de conferir o arquivo gravado; a primeira leitura antes de fechar ainda mostrava o conteúdo anterior e o guard encerrou sem solver. A tentativa, os logs e o setup anterior estão preservados localmente em `recuperacao_memoria_20261108`. A recuperação iniciada em 8/11 às 00:03 tem logs próprios e não autoriza outra instância em paralelo.

Na conferência de 01:04, o passe 22 concluiu e o 23 estava em cálculo. O crescimento efetivo foi de cerca de 14,6% por passe, apesar de `PercentRefinement=5`; registrar os tetraedros observados, sem inferir economia de memória a partir do parâmetro nominal. `auditar_convergencia.audit(project, write=False)` permite monitorar sem sobrescrever a auditoria de trabalho. O auditor exige explicitamente o mínimo de passes, pois `IsConverged=true` já aparecia no 22, antes do mínimo 23. Esse caso real foi verificado em modo somente de leitura e permaneceu corretamente reprovado.
