# P1H | Comparação das colunas em X

**Atende nos nove pontos com dez elementos.** A 5,17 GHz, a coluna de dez elementos e sua rede física deram 97,82° H, 5,61° V e 16,94 dBi frontais. O ganho mínimo foi 16,58 dBi a 5,09 GHz. A margem nominal para perdas adicionais antes do limite de 16 dBi é 0,58 dB.

## Comparação a 5,17 GHz

| Elementos | Portas do painel | Distância entre centros extremos | H com rede | V com rede | Ganho direto no painel | Ganho nas duas entradas |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 16 | 368,2 mm | 97,38° | 7,00° | 16,51 dBi | 16,17 dBi |
| 9 | 18 | 420,8 mm | 97,43° | 6,25° | 17,02 dBi | 16,56 dBi |
| 10 | 20 | 473,4 mm | 97,82° | 5,61° | 17,47 dBi | 16,94 dBi |

A dez elementos o aumento de ganho frente à solução de oito é 0,77 dB no centro, incluindo a mudança de divisor e comprimento dos cabos. A opção de nove foi simulada no centro. As opções de oito e dez foram simuladas nos nove pontos da banda.

## Dez elementos na banda

| Frequência | H (YZ) | V (XZ) | Ganho direto | Ganho nas entradas | Margem sobre 16 dBi |
|---:|---:|---:|---:|---:|---:|
| 5,09 GHz | 98,17° | 5,63° | 17,45 dBi | 16,58 dBi | 0,58 dB |
| 5,11 GHz | 98,08° | 5,62° | 17,46 dBi | 16,68 dBi | 0,68 dB |
| 5,13 GHz | 98,00° | 5,61° | 17,47 dBi | 16,78 dBi | 0,78 dB |
| 5,15 GHz | 97,91° | 5,61° | 17,47 dBi | 16,87 dBi | 0,87 dB |
| 5,17 GHz | 97,82° | 5,61° | 17,47 dBi | 16,94 dBi | 0,94 dB |
| 5,19 GHz | 97,74° | 5,61° | 17,48 dBi | 16,98 dBi | 0,98 dB |
| 5,21 GHz | 97,64° | 5,60° | 17,48 dBi | 16,96 dBi | 0,96 dB |
| 5,23 GHz | 97,55° | 5,58° | 17,48 dBi | 16,89 dBi | 0,89 dB |
| 5,25 GHz | 97,44° | 5,55° | 17,47 dBi | 16,78 dBi | 0,78 dB |

## Condições da comparação

O HFSS 2024 R2 resolveu cada painel como um único domínio eletromagnético. Foram incluídos todos os radiadores, as duas portas de cada um, seus acoplamentos e os refletores individuais de 48,3125 × 36 mm do estudo anterior. Os refletores foram modelados como condutores perfeitos (PEC). As trilhas dos radiadores têm condutividade finita. O passo permaneceu em 52,60 mm. A vertical de instalação é X e a frente é +Z. O estudo direto usou excitações uniformes em fase, normalizadas a 1 W incidente somado. A comparação final usou 0,5 W e 0° em cada entrada externa de 50 Ω, uma entrada por polarização. Os valores de ganho são o ganho realizado total em +Z. As larguras são os cruzamentos interpolados de −3 dB em relação ao pico de cada corte. O passo de amostragem angular foi 0,25°.

No painel de dez, o maior termo entre posições diferentes a 5,17 GHz foi -25,38 dB entre E016_PA5 e E016_PA6. Com alimentação direta uniforme, o pior coeficiente de reflexão ativo foi -16,43 dB. Com a rede, a dispersão entre as vinte ondas incidentes chegou a 0,48 dB e 4,36° no centro. O cálculo inclui as reflexões múltiplas, a interação entre saídas e os pesos efetivos de cada radiador. O HFSS recombinou os campos para esses pesos em cada frequência.

## Divisores e montagem

Cada coluna recebeu dois divisores radiais independentes sobre um único substrato de PTFE ZYF300CA-C. A placa das antenas conserva o RO4350B original. A ligação entre os dois materiais é coaxial, em 50 Ω. A JLCPCB lista o ZYF300CA-C com Dk 2,94 e tan δ 0,0016, em placas de duas camadas e cobre externo de 1 oz. [JLCPCB](https://jlcpcb.com/pt/news/rogers-ptfe-high-frequency-pcb-available) · [Ficha do laminado](https://rs.jlcpcb.com/static/file/ptfe-teflon-datasheet.pdf)

| Coluna | Placa | Núcleo | Ramos de transformação | Cabos iguais por saída |
|---:|---:|---:|---|---:|
| 8 | 34 × 67 mm | 0,76 mm | 141,4 Ω · 0,153 × 10,12 mm | 195 mm |
| 9 | 39 × 78 mm | 1,52 mm | 150 Ω · 0,275 × 10,037 mm | 234 mm |
| 10 | 39 × 78 mm | 1,52 mm | 158,1 Ω · 0,220 × 10,076 mm | 254 mm |

Na placa de dez, as trilhas de 50 Ω têm 3,866 mm de largura. Cada grupo inclui uma entrada e dez saídas. As duas entradas no centro das estrelas são independentes. A1 e B1 vão ao elemento em −236,7 mm. A10 e B10 vão ao elemento em +236,7 mm. O vão entre refletores mede 4,2875 mm e o comprimento de ponta a ponta dos refletores da coluna de dez é de 521,7125 mm. O mapa de ligação associa todos os conectores e portas do HFSS.

Os cabos são UT-141C de 50 Ω com condutor central de 0,9195 mm e blindagem externa de 3,581 mm. A atenuação típica foi interpolada entre 27,6 e 41,6 dB/100 pés a 5 e 10 GHz. Os modelos FEM das terminações incluem, no total, 3 mm de coaxial por caminho. Os outros 251 mm da versão de dez elementos entram como linha distribuída. A placa tem furação PTH de 1 mm, transição do pino, aterramento da blindagem e filetes nominais de SAC305. No lado da antena foi modelada uma junta redutora que preserva a sonda de 0,726 mm do P1H. O valor de resistividade da solda foi 13,2 µΩ·cm. [UT-141C](https://www.micro-coax.com/wp-content/uploads/2024/12/micro-coax-ut-141c-datasheet.pdf) · [SAC305](https://documents.indium.com/qdynamo/download.php?docid=5418)

Com 1 W incidente nas duas entradas, a rede de dez devolve 38,2 mW às fontes a 5,17 GHz. A placa dissipa ou irradia fora do painel 39,6 mW, os trechos distribuídos de cabo dissipam 49,8 mW e as juntas removem 0,6 mW. Os radiadores aceitam 871,8 mW líquidos. A transmissão entre as duas entradas do conjunto terminado nos radiadores foi -24,90 dB.

Para nove elementos, aumentar os cabos de 225 para 234 mm elevou o ganho no centro de 15,83 para 16,56 dBi. O comprimento altera a fase da reflexão que o painel apresenta aos divisores. Foram comparados comprimentos iguais de 220 a 240 mm no centro da banda.

Para dez elementos, foram avaliados comprimentos iguais de 240 a 260 mm, com variação comum de ±1 mm. O comprimento de 254 mm foi escolhido pelo menor ganho da banda, levando em conta essa variação. Com 245 mm, o menor ganho nominal calculado foi 16,16 dBi. Com todos os cabos variando juntos entre 253 e 255 mm, em passos de 0,25 mm, o pior ganho simulado foi 16,49 dBi. Diferenças individuais de fase entre cabos precisam ser verificadas após a soldagem.

## Verificação e limites

| Solução | Passes adaptativos | ΔS final |
|---|---:|---:|
| Painel com 8 | 6 | 0,01433 |
| Painel com 9 | 6 | 0,01433 |
| Painel com 10 | 6 | 0,01277 |
| Divisor 2 × 1:8 | 9 | 0,01058 |
| Divisor 2 × 1:9 | 8 | 0,01261 |
| Divisor 2 × 1:10 | 8 | 0,01087 |
| Transição coaxial | 6 | 0,00143 |

Uma segunda interconexão independente das matrizes S no scikit-rf confirmou a matriz de duas entradas. O KiCad reabriu a placa e registrou zero violações de DRC e zero pads desconectados. A furação exportada contém 22 furos metalizados de 1 mm, alinhados às 22 portas. O contorno é de 39 × 78 mm. Os Gerbers são para protótipo.

A co-simulação representa o painel finito, a placa de distribuição, as terminações e a propagação dentro dos cabos. A caixa, o radome, os suportes e o efeito da posição física da placa e das superfícies externas dos cabos sobre o diagrama dependem da montagem final. O modelo usa cobre de 35 µm com rugosidade nominal de 0,5 µm e trilhas de RF expostas. O acabamento ENIG, as tolerâncias do dielétrico, a forma real da solda e a dispersão de comprimento elétrico são fontes de diferença frente ao protótipo. O ganho foi simulado para as duas entradas simultâneas em fase.

[Painel de dez no HFSS](../../hfss/historico/P1H_10X_FEM.aedt) · [Divisor de dez no HFSS](../../hfss/historico/Divisor_2x10_PTFE.aedt) · [Layout KiCad](../../kicad/Divisor_2x10/Divisor_2x10_PTFE.kicad_pcb) · [Gerber e furação](../../fabricacao/gerbers/Gerber_Divisor_PTFE_2x10.zip) · [Mapa dos cabos](../../fabricacao/montagem/ligacao_dos_cabos.csv) · [Resultados por frequência](../../resultados/historico/10x/resultados.csv) · [Comparação dos diagramas](../../resultados/historico/diagramas_8_9_10.png) · [Touchstone de duas entradas](../../resultados/historico/10x/painel_duas_entradas.s2p)
