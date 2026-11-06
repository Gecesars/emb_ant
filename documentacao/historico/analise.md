# Antena impressa P1H no HFSS

**Ensaio histórico com apenas a porta A ativa.** Para a alimentação operacional com A e B em fase e de igual amplitude e a tolerância horizontal de ±10%, consultar a [análise de duas portas](analise_AB.md).

## Condições do ensaio

Ansys Electronics Desktop 2024 R2, design `Synth_DipoleArray`, solução modal `Setup_Multiband : LastAdaptive`. A fonte gravada no modelo é E016_PA a 1 W e 0°, com E016_PB a 0 W. O estudo adota +Z como frente e usa ganho realizado total relativo a uma antena isotrópica. O ganho de comparação é medido na direção frontal (+Z). A abertura é medida a −3 dB relativos ao máximo de cada corte. A meta de 16 dBi foi tratada como mínimo. As aberturas-alvo são 90° H e 7° V, sem tolerâncias especificadas.

O FEM contém um elemento com quatro setores metálicos, vias e duas alimentações sobre um substrato de 28,3125 × 28,3125 × 0,76 mm. O material cadastrado tem εr = 3,66 e tan δ = 0,0037. O refletor PEC está em z = 0 e a face inferior do substrato em z = 16,61 mm. O cobre das trilhas tem condição de condutividade finita. A faixa do sweep interpolado de S é 5,09–5,25 GHz. As verificações de diagrama usaram os campos das três frequências adaptativas.

## Efeito da largura do refletor

Cada linha corresponde a um elemento físico simulado separadamente a 5,17 GHz, com altura Y do refletor fixa em 48,3125 mm. XZ e YZ são cortes que passam pela frente. ΔS é o último valor do histórico adaptativo, para um limite de 0,02. Os S-parâmetros na tabela vêm do sweep.

| Largura X (mm) | HPBW XZ | HPBW YZ | Ganho em +Z | SAA | SBA | ΔS / convergiu |
|---:|---:|---:|---:|---:|---:|---:|
| 48,3125 | 71,40° | 71,66° | 7,99 dBi | -39,81 dB | -26,09 dB | 0.019309 / sim |
| 42 | 74,44° | 70,35° | 7,87 dBi | -35,71 dB | -26,45 dB | 0.018419 / sim |
| 24 | 82,00° | 67,96° | 7,21 dBi | -22,56 dB | -22,05 dB | 0.01992 / sim |
| 18 | 85,69° | 70,10° | 6,11 dBi | -19,16 dB | -18,43 dB | 0.017896 / sim |
| 12 | 100,35° | 80,03° | 4,73 dBi | -18,16 dB | -17,86 dB | 0.0073035 / sim |

Entre as geometrias de elemento testadas, a maior abertura nos eixos principais ocorreu em XZ com o refletor de 12 mm. A abertura chegou a 100,35°, com queda do ganho frontal para 4,73 dBi. A solução de oito elementos abaixo usa o refletor original para preservar a margem de ganho.

O histórico do retângulo usava dimensões literais. O ensaio confirmou que alterar apenas `array_reflector_width` mantinha os extremos X em ±24,15625 mm. Na cópia editável, abrir **Array_Refletor → CreateRectangle** e ligar XSize e YSize às variáveis de largura e altura. Para manter o centro, ligar a posição a `(-array_reflector_width/2, -array_reflector_height/2, array_reflector_z)`. Alterar a largura nas propriedades do design e conferir os extremos X, que devem ser ±largura/2. O espaçamento do refletor e as escalas do radiador também aparecem nas variáveis, mas as primitivas originais foram gravadas com dimensões literais. Uma alteração de altura precisa manter continuidade em pinos, vias e blindagens.

## Posição da coluna e orientação da instalação

O HFSS aplicou o fator de arranjo nativo aos campos FEM do elemento **original**, com oito centros a cada 55,5 mm, todas as fases em zero. A distância entre os centros extremos é 388,5 mm. Os pesos de tensão, simétricos, são 0,750 / 0,872 / 0,954 / 0,995 do extremo até o centro. A vertical do painel acompanha a coluna, e o corte horizontal é perpendicular a ela. Os ângulos φ são medidos de +X para +Y no plano da placa.

| Eixo dos centros no CAD | Plano H | HPBW H | HPBW V | Ganho em +Z a 5,17 GHz |
|---|---|---:|---:|---:|
| X | YZ | 71,66° | 6,89° | 16,97 dBi |
| Y | XZ | 71,40° | 6,89° | 16,97 dBi |
| φ = 154,2° | φ = 64,2° | 90,00° | 6,97° | 16,97 dBi |

No refletor original, a diferença das montagens X e Y é pequena frente ao passo angular de 1°. A esfera FEM do elemento (passo de 2°) apresenta cerca de 97,9° de abertura no corte a φ = 46°. A configuração selecionada usa o corte de 64,2° para atender à meta de 90°. Para instalar com a coluna paralela à vertical física, alinhar a reta dos centros a essa vertical. Para reproduzir a solução com a coluna paralela a X no referencial mecânico, girar o conjunto completo em +25,8° em torno de +Z. O giro altera a orientação da polarização.

| Frequência | HPBW horizontal | HPBW vertical | Ganho em +Z | Margem sobre 16 dBi |
|---:|---:|---:|---:|---:|
| 5,09 GHz | 90,57° | 7,08° | 16,94 dBi | 0,94 dB |
| 5,17 GHz | 90,00° | 6,97° | 16,97 dBi | 0,97 dB |
| 5,25 GHz | 89,19° | 6,86° | 16,99 dBi | 0,99 dB |

Os cortes do candidato têm passo angular de 0,25°. O resultado do arranjo pressupõe elementos idênticos e a distribuição de alimentação especificada. A avaliação do painel construído requer o arranjo finito com acoplamento, o refletor e a rede de alimentação reais, além de potência ativa, perdas, erros de fase/amplitude e polarização. Os valores em plena banda aqui são três pontos com campo salvo. Para uma especificação contínua, amostrar pontos internos e confirmar a estabilidade de ganho e HPBW com refinamento de malha.

## Abrir os resultados

- [Arquivo HFSS portátil com resultados](../../hfss/historico/elemento/arranjo/synth_dipole_array2_2024.aedt). Para consultar nesta máquina, abrir também o [projeto com o candidato e os seis relatórios de campo](../../hfss/historico/elemento/arranjo/synth_dipole_array2_2024.aedt), mantendo a pasta `.aedtresults` ao lado dele. Esta cópia reproduz a geometria do elemento original. Em **Radiation → Antenna Array → Antenna Array Setup**, inspecionar os centros e pesos. Os CSVs de X e Y capturam as configurações anteriores à seleção do candidato.
- [Coordenadas e pesos do candidato](../../hfss/historico/elemento/arranjo/coluna_obliqua.txt) e [gráfico a 5,17 GHz](../../resultados/historico/elemento/diagramas_5170.png).
- Para editar as dimensões do elemento, usar os modelos com o refletor parametrizado a [42 mm](../../hfss/historico/elemento/variante/P1H_refletor.aedt), [24 mm](../../hfss/historico/elemento/refletor24/P1H_refletor.aedt), [18 mm](../../hfss/historico/elemento/refletor18/P1H_refletor.aedt) ou [12 mm](../../hfss/historico/elemento/refletor12/P1H_refletor.aedt).
