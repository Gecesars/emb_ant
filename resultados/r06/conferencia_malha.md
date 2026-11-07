# Conferência da malha refinada de 11 passes

Em 7/11 às 19:12, o HFSS concluiu a malha com refinamento local dos fragmentos de cobre e das soldas. Foram 11 passes, 1.580.950 tetraedros; os últimos ΔS foram 0,00740689 / 0,00680733 e as maiores mudanças de campo 0,0367667 / 0,0303877 dB. O setup cumpriu ΔS ≤ 0,008 e campo ≤ 0,05 dB por dois passes.

Com os mesmos divisores, bobinas e linhas de 290 / 132 / 133 mm, o circuito apresentou **17,3447 dBi, H = 94,3761°, V = 5,6193°**, VSWR ativo **1,22727 / 1,15010** e convencional **1,20474 / 1,23735**. Todos os valores atendem às metas, porém a mudança horizontal de **−0,82976°** em relação à malha inicial excedeu o limite interno de estabilidade de 0,5°. O ganho mudou −0,00304 dB e os VSWR menos de 0,012.

Por isso o resultado ainda não foi liberado. A continuação mantém a malha, o setup e a geometria, com critérios mais rigorosos: **ΔS ≤ 0,004, campo ≤ 0,02 dB, dois passes**, mínimo 13 e máximo 24. O solver retomou no passe 12. A comparação de estabilidade usará esta malha de 11 passes e a continuação, com os mesmos limites de 0,05 dB em ganho, 0,5° H, 0,1° V e 0,05 em ambos os VSWR; não houve relaxamento de tolerâncias.

## Histórico de reparos no g3derr

O arquivo nativo agrega 59 blocos de metadados de execuções diferentes. Os 18 avisos repetidos de Major no corpo 4550 têm **TimeStamp de 16:49:21**, anterior ao refinamento. A execução refinada começou às **18:36:29**; a malha superficial de **18:38:17** indica somente dois corpos Minor, 4550 e 7234. **Não há Major na execução refinada.**

O auditor passou a respeitar os TimeStamp de cada bloco, usando o início documentado em `malha_execucao.json`. Ele conserva a contagem histórica e não remove dados do solver. `antena_refinada1/malha.json` contém a auditoria filtrada, e `malha_agregada.json` preserva a contagem anterior sem filtro. O arquivo `circuito/comparacao_malha_inicial_refinada1.json` é o diagnóstico original, que ainda contém `reparo_major_final: 1`; esse campo foi posteriormente identificado como contagem histórica. A reprovação por diferença de H continua válida independentemente dessa correção.

Os dados convergidos, quarenta campos complexos e matrizes S desta etapa estão preservados. A ausência de Major, isoladamente, não aprova RF; falta confirmar a estabilidade com a continuação mais rigorosa, verificar o circuito Nexxim final e revisar o relatório.
