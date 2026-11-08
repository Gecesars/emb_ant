# R07 — verificação em 17 frequências

**Em execução, sem conclusão de banda.** Pedido de 8/11/2026: verificar a PCB contínua de dez elementos com os dois divisores compactos em 5,09–5,25 GHz, a cada 10 MHz. Os requisitos em cada um dos 17 pontos são ganho frontal realizado total ≥16 dBi, abertura horizontal a −3 dB entre81° e99°, VSWR<1,5 em ambas as entradas, tanto simultaneamente ativas quanto com a outra entrada casada. Excitação: 0,5 W/0° em cada entrada.

As três PCBs continuam calculadas separadamente. O circuito combina a matriz S20 da antena com S18/S12 das distribuidoras, bobinas e campos complexos de cada porta. Os cabos têm somente fase dependente da frequência, sem atenuação; os conectores N são ideais. As perdas de cobre, dielétricos e ENIG nominais das PCBs continuam incluídas. Geometria e comprimentos físicos290/132/133mm permanecem iguais à R06.

## Recuperação após falta de memória

Em8/11 às13:47, o segundo passe do adaptativo R07 encerrou com `SOLVER_OUT_OF_MEMORY`. O primeiro passe havia calculado6.670.990tetraedros, sem reparos Major/Minor, mas não constituía convergência. Os metadados capturados antes da falha e os logs foram preservados; a tentativa não qualifica ganho nem banda. Não se repetiu a ampliação de malha que falhou. Nenhuma configuração global de memória, licença ou aplicativo do usuário foi alterada.

A recuperação usa o projeto **PCB_R07_SWEEP.aedt**, com importação da malha R06 validada e **nenhuma nova adaptação**. `MaximumPasses=0` é o modo documentado do HFSS para executar somente a varredura. A convergência permanece identificada como propriedade da fonte R06 histórica:23passes, ΔS finais0,00315575/0,00136256, controle de campo0,0100888/0,0068655dB e zero Major no escopo final. Não se atribui essa convergência à tentativa R07 interrompida. [Documentação Ansys2024R2](https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v242/en/Subsystems/HFSS/Content/HFSS/SettingtheMaximumNumberofPasses.htm).

O controle discreto em5,17GHz foi iniciado às14:40. A comparação com R06 mantém os limites de estabilidade abaixo e precede a varredura dos17pontos. O valor ΔS0,02 está registrado no setup, mas não é calculado em uma varredura sem adaptação; o critério da fonte é mais estrito,0,004. O limite de seis passes continua valendo para qualquer **novo** ciclo adaptativo que venha a ser necessário.

## Cálculo e limites pedidos

- Projeto atual: `D:/dev/EMBRAER/P1H/R07_Banda17/antena/PCB_R07_SWEEP.aedt`. A fonte R06 foi preservada e conferida por SHA256. Modelo, portas/fronteiras, operações de malha e esfera de campo distante são idênticos em bytes nas respectivas seções nativas.
- Tentativa histórica R07: máximo6passes, ΔS≤0,02, dois passes consecutivos, mínimo2, nove amostras de campo0,02dB. Interrompida por falta de memória no passe2. O limite de passes sozinho não aprova cálculo algum.
- Importação da malha R06 pelo recurso MeshLink, sem resolver ou alterar o projeto fonte. Não se trata de gerar uma malha grosseira do zero. A R06 histórica teve23passes e permanece identificada como tal.
- Depois da auditoria da fonte e comparação do controle central, varredura **discreta** de17frequências na malha importada, salvando campos radiados. A varredura não representa17adaptações independentes. Não haverá extrapolação do S20 ou dos campos de5,17GHz para as outras frequências.
- A diferença do centro frente à R06 deve permanecer em até0,05dB de ganho,0,5° horizontal,0,1° vertical e0,05 de VSWR. Falha interrompe a fila para investigação, sem relaxar tolerâncias.
- Os divisores e os cupons das bobinas já possuem17pontos reais e são reutilizados. A fase das linhas ideais e a solução de múltiplas reflexões são recalculadas em cada frequência.
- Cada ponto é conferido por recomposição da alimentação uniforme, passividade, reciprocidade e balanço de potência. A matriz final17pontos será comparada com o Ansys Circuit/Nexxim.

Não se conclui desempenho entre as amostras nem validação experimental a partir desta campanha.

## Reprodução e estado

Os scripts estão em [automacao/r07](../../automacao/r07). O arquivo local `qualificacao.json` registra o processo e a etapa. A fila atual é **continuar_fixa.ps1**; logs `controle_fixo_aedt.log`, `antena/controle_fixo.log` e `qualificacao_fixa.log`. A fila anterior `continuar.ps1` e seus processos terminaram após a falha; **não reiniciá-la**. Não duplicar a fila atual. Ela para se uma auditoria ou operação falhar.

Fluxo atual: auditoria real da fonte e identidade física→controle discreto5170→auditoria da malha importada→40campos do centro→comparação R06→17soluções discretas→680campos complexos→circuito em17pontos→Nexxim→revisão do relatório. Há42arquivos de corte por frequência:40por porta e2uniformes.

A reprodução exata com malha fixa requer os resultados R06 locais, excluídos do Git conforme solicitado. O projeto fonte e os scripts permanecem versionados; `ForceSourceToSolve=False` impede uma readaptação automática da fonte. Não confundir um projeto nativo salvo com um pacote de solução de campo restaurável sem esses resultados.

O programa de circuito foi generalizado para receber a frequência explicitamente. A [verificação de software](verificacao_software.json) reproduziu os valores R06 exatamente, preservou sua auditoria, confirmou os17pontos dos divisores e rejeitou a tentativa de usar o S20 de centro em outra frequência. Isso verifica o processamento; **não é resultado RF de banda**.

## Entregas anteriores preservadas

A R06 permanece qualificada somente em5,17GHz:17,3593dBi,H96,0643°,VSWR máximo1,2474. [Relatório R06](../r06/P1H_R06_Relatorio.pdf) e [mecânica R06](../../freecad/mecanica_R06/README.md). A cotação JLC de7/11 continua histórica e não foi refeita porque as PCBs não mudaram. Nenhum email de checkpointR07 foi enviado.

Malhas, diretórios`.aedtresults`, campos volumétricos, logs grandes e locks permanecem fora do Git.
