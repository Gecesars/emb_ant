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
