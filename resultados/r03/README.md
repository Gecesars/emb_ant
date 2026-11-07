# Comparação das placas compactas e alongadas

## Resultado da rede física no centro da banda

**A primeira alongada R03 de 1,52 mm reprovou como rede de alimentação uniforme.** A solução convergida do HFSS a 5,17 GHz entregou 40,98% da potência às cargas, com perda excedente de **3,874 dB**, retorno ativo de **6,89 dB**, diferença de amplitude de **16,27 dB** e dispersão circular de fase de **239,65°** entre saídas. A adaptação terminou em 18 passes, com 1.014.456 tetraedros e ΔS de 0,00659, cumprindo dois passes consecutivos abaixo de 0,009. [Matriz S11P e convergência](rede_C_centro) · [Métricas](rede_hfss_centro.csv)

A compacta C entregou 82,25%, com perda de 0,849 dB e dispersões de 0,089 dB e 0,528°. Na compacta ZYF255DA, os dois estágios físicos e os mesmos coaxiais entregaram 80,49%, com 0,943 dB de perda no centro. Assim, a menor perda por metro do material 255DA, isoladamente, foi insuficiente para superar a compacta C.

Os cálculos por linhas abaixo registram a etapa de síntese. A diferença encontrada no modelo físico exige revisar a interação entre as trilhas longas e as transições. Foi iniciado um controle de espessura com núcleo de 0,76 mm, disponível no configurador da JLCPCB, e trilhas redimensionadas. Essa revisão experimental usa diretório próprio e conserva os resultados da R03 original. A revisão do painel radiador continua usando RO4350B de 0,76 mm.

## Geometria e custo

A R03 reduz o coaxial instalado em **2,997 m por painel (81,6%)** frente à R02 e alinha cada uma das vinte saídas com a respectiva solda do radiador. A contrapartida é aumentar a microstrip por percurso de aproximadamente 30,4 para 494,2 mm. Na comparação por linhas de transmissão com ZYF300CA-C, a compacta tem 0,061 dB de vantagem no centro. O custo de placas nuas da alongada aumenta R$ 38,44 por antena no lote de cinco.

| Percurso nominal | R02 compacta | R03 alongada |
|---|---:|---:|
| Entrada N → primeira PCB | 2 × 271,792 mm | 2 × 71,108 mm |
| Enlaces coaxiais entre estágios | 4 × 132,000 mm | Etapas ligadas por microstrip |
| Último trecho até cada porta do radiador | 20 × 130,000 mm | 20 × 26,610 mm |
| Coaxial N → radiador | 533,792 mm | 97,718 mm |
| Microstrip N → radiador, por caminho | ≈ 30,4 mm | 494,206–494,214 mm em ZYF300CA-C |
| Coaxial total no painel | 3,672 m | 0,674 m |
| Peças de coaxial | 26 | 22 |
| PCBs de antena e de distribuição, por painel | R$ 364,56 | R$ 403,00 |

## Perda de distribuição para vinte cargas casadas

Cada coluna abaixo foi calculada com o mesmo modelo de linhas com perdas, a mesma referência de 50 Ω e a mesma atenuação de catálogo do coaxial UT-141C. Os transformadores e as larguras foram redimensionados em cada material. O cálculo soma a potência entregue às vinte cargas e inclui reflexão. Os 10 dB da divisão ideal entre dez saídas por polarização ficam fora da perda excedente. Trata-se de uma previsão nominal com junções ideais, cobre de 35 µm e rugosidade de 0,5 µm. [17 frequências e oito combinações](comparacao_linhas.csv)

| PTFE de 1,52 mm | Dk / Df nominais | Compacta a 5,17 GHz | Alongada a 5,17 GHz | Alongada, mín.–máx. nos 17 pontos |
|---|---|---:|---:|---:|
| ZYF300CA-C | 2,94 / 0,0016 | 0,946 dB | 1,007 dB | 0,995–1,021 dB |
| ZYF300CA-P | 3,00 / 0,0018 | 0,946 dB | 1,084 dB | 1,071–1,099 dB |
| ZYF265D | 2,65 / 0,0019 | 0,973 dB | 1,047 dB | 1,034–1,062 dB |
| ZYF255DA | 2,55 / 0,0018 | 0,977 dB | 0,996 dB | 0,985–1,010 dB |

Para o ZYF300CA-C, a alongada apresenta menos perda prevista nos cinco pontos entre 5,09 e 5,13 GHz. A compacta fica à frente nos doze restantes. A maior perda prevista em cada configuração é de 1,061 dB na compacta a 5,09 GHz e de 1,021 dB na alongada a 5,25 GHz.

O cálculo por linhas favorece o ZYF255DA sobre o ZYF300CA-C em apenas 0,011 dB na alongada a 5,17 GHz. Para a compacta C, as matrizes HFSS dos dois estágios, interligadas pelos coaxiais, dão 0,849 dB no centro e 0,726–1,076 dB na banda. A diferença de 0,097 dB entre métodos para a compacta é maior que a diferença entre os dois melhores materiais previstos na alongada. A escolha inicial de ZYF300CA-C mantém uma referência comum para a cotação e o painel integrado. [HFSS da compacta em 50 Ω](../r02/rede/README.md)

## Ensaio HFSS dos quatro laminados

Os oito cupons físicos concluíram as 17 frequências. Cada linha atingiu dois passes consecutivos com ΔS ≤ 0,003. A atenuação de 100 mm foi extraída dos autovalores da matriz composta pelas linhas de 20 e 120 mm. A fase do quociente de transmissão resolve o sinal dos autovalores perto de múltiplos de π, e a fase prevista seleciona apenas a volta inteira. Foram conferidas reciprocidade, passividade e continuidade da fase. [Matrizes e convergência](cupons) · [Dados completos](cupons_hfss.csv)

| PTFE | Atenuação de 50 Ω a 5,17 GHz | Mín.–máx. em 5,09–5,25 GHz | Alongada com trechos de 50 Ω corrigidos pelos cupons, a 5,17 GHz |
|---|---:|---:|---:|
| ZYF300CA-C | 2,281 dB/m | 2,246–2,318 dB/m | 1,214 dB |
| ZYF300CA-P | 2,454 dB/m | 2,416–2,494 dB/m | 1,299 dB |
| ZYF265D | 2,301 dB/m | 2,266–2,336 dB/m | 1,225 dB |
| ZYF255DA | 2,175 dB/m | 2,143–2,208 dB/m | 1,163 dB |

O ZYF255DA teve a menor atenuação nominal no cupom de 50 Ω. A coluna da direita combina a propagação HFSS desses trechos com os modelos analíticos dos transformadores e das junções. Ela mostra o efeito da perda de linha sobre os cerca de 494 mm da alongada. O ensaio com toda a rede física inclui as curvas, as divisões e as emendas. [Previsão intermediária nos 17 pontos](comparacao_com_cupons.csv)

O estudo da rede alongada usa os dois divisores, as emendas de sinal e massa, os planos de cobre e os lançamentos coaxiais. A simetria magnética aplica-se à rede sob excitação par das duas polarizações. As portas coaxiais são inteiras e afastadas do plano de simetria, com referência de 50 Ω e multiplicador unitário. O painel completo tem domínio inteiro e duas portas nos N. O modelo de painel inclui suporte, refletor, bobinas e acoplamento. O teste de geometria do HFSS foi concluído para os quatro modelos de rede e para o painel em ZYF300CA-C. A aprovação de ganho e abertura requer os campos radiados. [Modelos das quatro redes](../../hfss/alimentacao/R03) · [Modelo do painel](../../hfss/antenas/P1H_R03_Alongada.aedt)

O acabamento cotado é ENIG. Os modelos de cobre finito usam propriedades nominais sem a camada de níquel-fósforo do banho, e as fitas da emenda usam contato metálico ideal nas superfícies soldadas. O resultado de fabricação depende dessas perdas, das tolerâncias de Dk e das soldas. A cotação e a ficha do fabricante identificam os quatro laminados. [Materiais JLCPCB](https://rs.jlcpcb.com/static/file/ptfe-teflon-datasheet.pdf) · [Acabamentos JLCPCB](https://jlcpcb.com/help/article/jlcpcb-surface-finish) · [Influência do ENIG em microstrip, Rogers](https://www.rogerscorp.com/blog/2020/comparing-pcbs-for-microstrip-and-grounded-coplanar-waveguide-circuits)
