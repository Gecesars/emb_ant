# Candidato preliminar de 290 / 132 / 133 mm

**Não é aceite final.** Dados obtidos com a primeira malha convergida da PCB e as duas distribuidoras completas resolvidas em separado. A malha local refinada da antena estava em cálculo na publicação deste checkpoint.

`resultado.json` contém as métricas da configuração de 133 mm; `comparacao_comprimentos.json` registra o caso anterior de 135 mm, reprovado no VSWR convencional B, e o candidato selecionado. O sinal `criterios_numericos_atendidos` refere-se aos números dessa malha e não substitui a auditoria final de convergência e estabilidade.

`nexxim.s2p` e `verificacao_nexxim.json` conferem o circuito independente. `componentes` contém exatamente as matrizes usadas no circuito nativo, com linhas ideais de fase sem atenuação. `fontes.json` registra os SHA-256 das matrizes originais, incluindo o controle que remove a atenuação dos acessos da bobina. As PCBs e a bobina mantêm suas perdas. As duas entradas são 0,5 W / 0°, em 50 ohms.

O resultado é somente de 5,17 GHz. Não representa varredura de banda da antena. Os dados de 17 frequências dos divisores ficam nas pastas adjacentes.
