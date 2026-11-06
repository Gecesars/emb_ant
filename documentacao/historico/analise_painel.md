# P1H | Painel finito e distribuição de duas polarizações

**Atende nos nove pontos simulados.** Com as duas entradas de 50 Ω a 0,5 W e 0° cada, o modelo dá 97,38° H, 7,00° V e 16,17 dBi em +Z a 5,17 GHz. O mínimo é 16,05 dBi a 5,09 GHz, com margem de 0,05 dB frente a 16 dBi. A meta horizontal é 81°–99° e a maior diferença vertical em relação a 7° é 0,04°.

## Aberturas e ganho realizado

| MHz | H direta | H na entrada do sistema | V direta | V na entrada do sistema | Ganho direto | Ganho na entrada do sistema |
|---:|---:|---:|---:|---:|---:|---:|
| 5090 | 97,80° | 97,76° | 7,12° | 7,04° | 16,49 dBi | 16,05 dBi |
| 5110 | 97,69° | 97,66° | 7,09° | 7,02° | 16,49 dBi | 16,07 dBi |
| 5130 | 97,59° | 97,57° | 7,06° | 7,01° | 16,50 dBi | 16,10 dBi |
| 5150 | 97,49° | 97,48° | 7,04° | 7,00° | 16,50 dBi | 16,14 dBi |
| 5170 | 97,39° | 97,38° | 7,01° | 7,00° | 16,51 dBi | 16,17 dBi |
| 5190 | 97,28° | 97,29° | 6,99° | 7,00° | 16,51 dBi | 16,20 dBi |
| 5210 | 97,18° | 97,20° | 6,96° | 7,00° | 16,51 dBi | 16,23 dBi |
| 5230 | 97,07° | 97,10° | 6,93° | 7,00° | 16,51 dBi | 16,26 dBi |
| 5250 | 96,96° | 97,00° | 6,90° | 6,99° | 16,51 dBi | 16,27 dBi |

O HFSS exportou cortes assinados de θ a cada 0,25°. A largura corresponde aos dois cruzamentos interpolados a −3 dB do pico de cada corte. Com frente em +Z e coluna em X, H é YZ (φ = 90°) e V é XZ (φ = 0°). O ganho é total realizado em θ = 0°. O valor se refere à excitação coerente das duas polarizações.

## Modelo do painel e distribuição

O FEM do painel inclui oito cópias físicas do elemento P1H/RO4350B, espaçadas de 52,60 mm em X, em uma única região aberta. Cada posição possui um refletor PEC individual de 48,3125 × 36 mm. O cobre das trilhas, as sondas e o dielétrico das antenas seguem o projeto de referência. Os centros extremos distam 368,20 mm. O modelo direto usa 62,5 mW em fase por porta, equivalentes a 1 W total. O fator de arranjo está desativado.

O maior acoplamento entre posições distintas foi -25,39 dB a 5,17 GHz. O pior coeficiente de reflexão ativo nessa frequência, com alimentação direta uniforme, foi -16,46 dB. Os dois valores incluem as condições dos 16 terminais.

A placa selecionada mede 34 × 67 mm. São dois divisores radiais 1:8 em microstrip, um para A e outro para B, com plano de terra comum na face inferior. Os ramos nominais de aproximadamente 141,4 Ω têm 0,153 mm de largura e 10,12 mm entre a borda da ilha central e o degrau para a trilha de 50 Ω (1,893 mm). O raio dos centros de saída é 13,25 mm. A divisão radial dispensa resistores de isolação e permite interação entre saídas da mesma polarização. Essa interação entra pela matriz completa de 18 portas.

Use PTFE ZYF300CA-C, núcleo de 0,76 mm, Dk 2,94, tan δ 0,0016 e cobre de 35 µm por face. O divisor se conecta ao RO4350B das antenas por interfaces de 50 Ω. As trilhas de RF estão expostas na abertura de máscara. O FEM representa cobre de condutividade finita com rugosidade nominal de 0,5 µm. A fabricação especifica ENIG. A camada final de níquel/ouro, a máscara adjacente e as tolerâncias de fabricação são pendências para correlação com o protótipo. [Oferta JLCPCB](https://jlcpcb.com/pcb-fabrication/high-frequency-pcb) · [Ficha do laminado](https://rs.jlcpcb.com/static/file/ptfe-teflon-datasheet.pdf)

Os 16 cabos UT-141C têm 195 mm nominais de coaxial cada. No circuito, 192 mm são linha distribuída de 50 Ω e os outros 3 mm estão nos dois modelos FEM de terminação. A atenuação típica foi interpolada localmente entre 27,6 dB/100 pés a 5 GHz e 41,6 dB/100 pés a 10 GHz. A capacitância publicada de 95,2 pF/m define a velocidade de fase. Os 18 lançamentos da placa usam pino, dielétrico do coaxial, blindagem, ilha metalizada e solda SAC305 nominal. [Ficha UT-141C](https://www.micro-coax.com/wp-content/uploads/2024/12/micro-coax-ut-141c-datasheet.pdf) · [Propriedades SAC305](https://documents.indium.com/qdynamo/download.php?docid=5418)

Na ponta da antena, a junta proposta faz a redução entre o UT-141C e a sonda existente de 0,726 mm de diâmetro central. O modelo tem uma ponte condutora anular de 0,25 mm de extensão e um trecho adicional de sonda de 0,75 mm. A espessura dos filetes é nominal. Isso preserva os planos das duas portas do elemento. A instalação deve conservar essa terminação, inclusive o contato elétrico da blindagem com a sonda. Um cabo soldado diretamente a uma PCB com furação ou sonda redesenhada exige atualizar o modelo.

## Potência e verificação numérica

A 5,17 GHz, com 1 W incidente somado nas entradas, o sistema devolve 12,9 mW às fontes. A placa consome ou irradia fora do painel 34,6 mW, as linhas dos cabos dissipam 39,6 mW, e as juntas removem 0,6 mW. As portas do painel aceitam 912,3 mW líquidos. A dispersão entre as 16 excitações incidentes é 0,14 dB em amplitude e 4,38° em fase. As duas entradas externas estão em fase. As cargas acopladas e os distribuidores determinam as fases efetivas no painel.

A diferença de ganho entre os planos de referência é 0,34 dB no centro e 0,23 a 0,44 dB nos nove pontos. O primeiro layout Wilkinson, avaliado com 210 mm de UT-141C por saída e as duas entradas em fase, obteve 14,02 dBi no centro.

O HFSS 2024 R2 convergiu em 6 passes para o painel (ΔS = 0,01433), 9 para o divisor soldado (ΔS = 0,01058) e 6 para a junta (ΔS = 0,00143). O sweep discreto inclui nove pontos de 20 MHz. A interconexão das matrizes complexas usa 50 Ω e inclui múltiplas reflexões. Uma segunda montagem das portas no scikit-rf reproduziu a matriz final com diferença absoluta máxima de 5.20e-17. Para cada frequência, o HFSS recombinou os campos das 16 portas com as ondas incidentes resultantes. O ganho foi referido a 1 W nas duas entradas externas pela razão entre a potência incidente no painel e a potência incidente no sistema.

A co-simulação inclui o acoplamento entre radiadores e entre os circuitos impressos na placa de distribuição. O espalhamento externo da placa, da caixa e das superfícies externas dos cabos sobre a antena depende da posição física final. Os resultados são nominais de simulação. Os valores nas frequências intermediárias e o ganho do protótipo dependem de verificação.

[Painel HFSS](../../hfss/historico/P1H_8X_FEM.aedt) · [Divisor HFSS](../../hfss/historico/Radial_Soldado_2x8.aedt) · [Junta HFSS](../../hfss/alimentacao/Junta_UT141_P1H.aedt) · [Placa editável](../../kicad/historico/Divisor_2x8/Radial_Soldado_2x8.kicad_pcb) · [Mapa de ligação](../../fabricacao/historico/ligacao_dos_cabos.csv) · [Gerber e furação](../../fabricacao/historico/Gerber_Radial_PTFE_2x8.zip) · [Diagramas](../../resultados/historico/8x/diagramas_5170.png) · [Tabela](../../resultados/historico/8x/resultados.csv) · [Potências](../../resultados/historico/8x/balanco.csv) · [S de duas entradas](../../resultados/historico/8x/painel_duas_entradas.s2p)
