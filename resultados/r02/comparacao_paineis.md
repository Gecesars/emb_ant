# Painel completo com os divisores e os cabos

## Resultado

**Ambas as montagens com os dois divisores compactos reprovam a meta de manter abertura horizontal de 81° a 99° e ganho frontal realizado de pelo menos 16 dBi em toda a banda.** A placa contínua atende à abertura horizontal a 5,17 GHz. As duas montagens ficam abaixo do ganho mínimo nesse ponto.

| Montagem | H a −3 dB | V a −3 dB | Ganho realizado em +Z | Potência refletida |
|---|---:|---:|---:|---:|
| R01, contínua e divisor único | 102,34° | 6,19° | 14,06 dBi | 4,80% |
| R02, contínua e dois divisores compactos | **94,82°** | **5,54°** | **12,00 dBi** | 55,00% |
| R02-S, dez PCBs e os mesmos divisores compactos | 105,13° | 5,57° | 13,48 dBi | 39,68% |

São resultados convergidos do HFSS a **5,17 GHz**, com 0,5 W a 0° em cada entrada N, total de 1 W incidente. O eixo X acompanha a coluna, o corte YZ representa a horizontal e o XZ a vertical. O ganho frontal refere-se a +Z. Cada corte tem passo angular de 0,25°. A avaliação angular usa os cruzamentos a −3 dB do lóbulo principal.

O ponto de centro reprovado é suficiente para concluir que as montagens falham na exigência de manter as duas metas em toda a banda de 5,09 a 5,25 GHz. A varredura dos painéis terminou na avaliação central. Os divisores compactos e os cupons de materiais foram calculados nas **17 frequências** de 5,09 a 5,25 GHz. Os modelos longos R03 e R04 foram rejeitados pela distribuição física no centro.

## Condições da comparação

R02 e R02-S usam a mesma rede de distribuição, dez posições com passo de 52,6 mm, refletor dobrado de alumínio de 2 mm, conectores N, soldas, bobinas de curto em CC e comprimentos de coaxial. Na R02-S, a remoção do laminado entre radiadores e a inclusão das guias de POM fazem parte da montagem comparada. A placa contínua mede 501,7125 × 28,3125 mm. Cada radiador individual tem 28,3125 mm de lado. Todos usam RO4350B com núcleo de 0,76 mm.

Cada caminho da R02 contém 271,792 mm de coaxial na entrada, 132 mm entre estágios e 130 mm até o radiador. Os vinte ramais têm o mesmo comprimento nominal. Na carga casada, a rede compacta C apresentou 0,849 dB de perda no centro e 0,726–1,076 dB nos 17 pontos, com dispersão máxima de 0,089 dB e 0,543°. O painel completo apresentou forte descasamento ao incluir os radiadores e a montagem. [Resultados da rede em cargas casadas](rede/README.md)

## Diretividade, ganho aceito e ganho realizado

| Montagem | Diretividade frontal | Ganho referido à potência aceita | Ganho referido à potência incidente |
|---|---:|---:|---:|
| R01 | 15,187 dBi | 14,273 dBi | 14,059 dBi |
| R02 contínua | 16,644 dBi | 15,466 dBi | 11,998 dBi |
| R02-S separadas | 16,675 dBi | 15,674 dBi | 13,479 dBi |

O ganho realizado inclui o efeito da reflexão nas entradas. Na R02, o descasamento corresponde a 3,468 dB de diferença entre ganho aceito e realizado. Na R02-S, essa diferença é de 2,195 dB. A análise em cargas de 50 Ω isola a alimentação. A matriz e o campo do painel montado incluem as impedâncias ativas dos radiadores e a interação com a estrutura.

## Convergência e arquivos

| Montagem | Passes | Tetraedros finais | ΔS final | Passes consecutivos abaixo de 0,015 |
|---|---:|---:|---:|---:|
| R01 | 8 | 3.232.419 | 0,01206 | 2 |
| R02 | 8 | 2.694.533 | 0,01413 | 2 |
| R02-S | 15 | 7.746.579 | 0,01184 | 2 |

Os dados da contínua estão neste diretório, incluindo S2P, cortes H/V, métricas e convergência. O controle de dez placas está no diretório `r02_separadas`. Os projetos AEDT guardam a geometria e os parâmetros para regenerar a malha. As malhas e os campos permanecem localmente. [R02 contínua](metricas_Centro.csv) · [R02-S separadas](../r02_separadas/metricas_Centro.csv) · [HFSS contínua](../../hfss/antenas/P1H_R02.aedt) · [HFSS separadas](../../hfss/antenas/P1H_R02_10Separadas.aedt)

Os modelos usam cobre finito de propriedades nominais, perdas dielétricas nominais, geometria nominal de solda e modelo dos conectores. A camada de níquel-fósforo do acabamento ENIG cotado permanece fora do modelo de cobre. Essa limitação também se aplica às comparações de materiais. A campanha estabelece a reprovação das metas de RF nas montagens estudadas.

## Documentação e cotação

Os dois divisores compactos, a placa contínua, a chapa dobrada e planificada, os apoios, os desenhos, os arquivos KiCad e os Gerbers estão organizados no repositório. A cotação JLCPCB de cinco conjuntos completos de três PCBs somou **R$ 1.822,79**, ou **R$ 364,56 por antena**, antes de frete, tributos e montagem. As alongadas somaram R$ 2.014,99 por cinco, com economia de coaxial e maior perda de RF. [Mecânica compacta](../../freecad/mecanica_R02/README.md) · [Mecânica alongada](../../freecad/mecanica_R03/README.md) · [Cotação compacta](cotacao.md) · [Cotação alongada](../r03/cotacao.md)
