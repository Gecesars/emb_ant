# P1H com as duas portas de mesma amplitude e fase

A revisão operacional usa E016_PA:1 e E016_PB:1 a 0,5 W e 0° cada nos planos modais do HFSS. A potência incidente de referência do elemento é 1 W. As linhas de integração das duas portas seguem o mesmo sentido radial no mesmo plano z = −14,51924 mm. Os campos complexos das duas portas foram combinados pelo HFSS. Os oito elementos recebem o mesmo peso de amplitude e fase. A frente é +Z e o eixo da coluna corresponde à vertical de instalação.

## Orientação e dimensões

Com o refletor original de 48,3125 mm quadrados, a antiga coluna oblíqua de 55,5 mm de passo, recalculada com A+B, apresentou **79,96° H a 5,17 GHz**. A montagem axial em X com o refletor original tem abertura H de 81,45° pela forma do elemento. A faixa de aceitação horizontal especificada é 81°–99°, inclusiva.

Na configuração selecionada, o refletor mede **48,3125 × 36 mm (X × Y)** e os oito centros estão ao longo de X, a cada **52,60 mm**. Distância entre centros extremos de 368,20 mm. A 5,17 GHz, os centros em X deram 94,08° H e 7,00° V. Com a coluna em Y, a mesma geometria e alimentação deram 66,71° H e 7,02° V. Para a coluna em X, H é o corte YZ e V é XZ.

## Banda simulada

Ganho realizado total medido em +Z. Feixe a −3 dB do máximo de cada corte, com passo angular de 0,25°. Campos do sweep discreto AB_Campo20MHz. Para a vertical, comparar os valores medidos com a meta de 7°. O mínimo usado para ganho é 16 dBi.

| MHz | H | H dentro de 81°–99° | V | Ganho frontal |
|---:|---:|:---:|---:|---:|
| 5090 | 94,58° | sim | 7,11° | 16,36 dBi |
| 5110 | 94,46° | sim | 7,08° | 16,37 dBi |
| 5130 | 94,33° | sim | 7,05° | 16,37 dBi |
| 5150 | 94,21° | sim | 7,03° | 16,38 dBi |
| 5170 | 94,08° | sim | 7,00° | 16,38 dBi |
| 5190 | 93,96° | sim | 6,97° | 16,38 dBi |
| 5210 | 93,83° | sim | 6,94° | 16,38 dBi |
| 5230 | 93,70° | sim | 6,92° | 16,38 dBi |
| 5250 | 93,58° | sim | 6,89° | 16,38 dBi |

Para o elemento isolado em A+B, o pior coeficiente de reflexão ativo entre os 251 pontos do sweep de rede foi -22,42 dB em A e -22,77 dB em B. Foram usadas as somas complexas SAA + SAB e SBB + SBA, válidas para as ondas incidentes iguais e em fase deste ensaio.

O FEM inclui as duas portas do elemento. O HFSS sintetizou a coluna pelo fator de arranjo, com pesos de tensão unitários e fases de 0°. A validação física do painel ainda depende do acoplamento entre elementos, da rede de distribuição e das perdas e diferenças de fase nos seus caminhos.

[Projeto HFSS do elemento para recalcular os campos](../../hfss/antenas/P1H_AB_em_fase.aedt) · [Tabela numérica](../../resultados/historico/elemento/resumo_AB.csv) · [Gráfico em frequência](../../resultados/historico/elemento/banda_AB.png)
