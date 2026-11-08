# R07 — verificação em 17 frequências

**Em execução, sem conclusão de banda.** Pedido de 8/11/2026: verificar a PCB contínua de dez elementos com os dois divisores compactos em 5,09–5,25 GHz, a cada 10 MHz. Os requisitos em cada um dos 17 pontos são ganho frontal realizado total ≥16 dBi, abertura horizontal a −3 dB entre81° e99°, VSWR<1,5 em ambas as entradas, tanto simultaneamente ativas quanto com a outra entrada casada. Excitação: 0,5 W/0° em cada entrada.

As três PCBs continuam calculadas separadamente. O circuito combina a matriz S20 da antena com S18/S12 das distribuidoras, bobinas e campos complexos de cada porta. Os cabos têm somente fase dependente da frequência, sem atenuação; os conectores N são ideais. As perdas de cobre, dielétricos e ENIG nominais das PCBs continuam incluídas. Geometria e comprimentos físicos290/132/133mm permanecem iguais à R06.

## Cálculo e limites pedidos

- Novo projeto local: `D:/dev/EMBRAER/P1H/R07_Banda17/antena/PCB_R07.aedt`. A origem R06 foi preservada.
- Novo ciclo adaptativo em5,17GHz: máximo6passes, ΔS≤0,02, dois passes consecutivos, mínimo2. Nove amostras de campo mantêm controle adicional de0,02dB. O limite de passes sozinho não aprova o cálculo.
- Importação da malha R06 pelo recurso MeshLink, sem resolver ou alterar o projeto fonte. Não se trata de gerar uma malha grosseira do zero. A R06 histórica teve23passes e permanece identificada como tal.
- Depois da convergência e comparação do centro, varredura **discreta** de17frequências na malha adaptada, salvando campos radiados. A varredura não representa17adaptações independentes. Não haverá extrapolação do S20 ou dos campos de5,17GHz para as outras frequências.
- A diferença do centro frente à R06 deve permanecer em até0,05dB de ganho,0,5° horizontal,0,1° vertical e0,05 de VSWR. Falha interrompe a fila para investigação, sem relaxar tolerâncias.
- Os divisores e os cupons das bobinas já possuem17pontos reais e são reutilizados. A fase das linhas ideais e a solução de múltiplas reflexões são recalculadas em cada frequência.
- Cada ponto é conferido por recomposição da alimentação uniforme, passividade, reciprocidade e balanço de potência. A matriz final17pontos será comparada com o Ansys Circuit/Nexxim.

Não se conclui desempenho entre as amostras nem validação experimental a partir desta campanha.

## Reprodução e estado

Os scripts estão em [automacao/r07](../../automacao/r07). O arquivo local `qualificacao.json` registra o processo e a etapa; `antena/centro.log`, `centro_aedt.log`, `antena/banda.log` e `qualificacao.log` são registros de execução. A fila `continuar.ps1` está vinculada ao cálculo de centro já iniciado e **não deve ser lançada novamente**. Ela para se uma auditoria ou operação falhar.

Fluxo: adaptativo→auditoria real de convergência→40campos do centro→comparação R06→17soluções discretas→680campos complexos→circuito em17pontos→Nexxim→revisão do relatório. Há42arquivos de corte por frequência:40por porta e2uniformes.

O programa de circuito foi generalizado para receber a frequência explicitamente. A [verificação de software](verificacao_software.json) reproduziu os valores R06 exatamente, preservou sua auditoria, confirmou os17pontos dos divisores e rejeitou a tentativa de usar o S20 de centro em outra frequência. Isso verifica o processamento; **não é resultado RF de banda**.

## Entregas anteriores preservadas

A R06 permanece qualificada somente em5,17GHz:17,3593dBi,H96,0643°,VSWR máximo1,2474. [Relatório R06](../r06/P1H_R06_Relatorio.pdf) e [mecânica R06](../../freecad/mecanica_R06/README.md). A cotação JLC de7/11 continua histórica e não foi refeita porque as PCBs não mudaram. Nenhum email de checkpointR07 foi enviado.

Malhas, diretórios`.aedtresults`, campos volumétricos, logs grandes e locks permanecem fora do Git.
