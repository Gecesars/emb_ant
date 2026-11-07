# Comparação das placas compactas e alongadas

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

O estudo dos cupons extrai a atenuação de 100 mm de linha a partir das matrizes de duas linhas físicas com 20 e 120 mm e os mesmos lançamentos. O estudo da rede alongada usa os dois divisores, as emendas de sinal e massa, os planos de cobre e os lançamentos coaxiais. A simetria magnética aplica-se à rede sob excitação par das duas polarizações. O painel completo tem domínio inteiro e duas portas nos N. O modelo de painel inclui suporte, refletor, bobinas e acoplamento. O teste de geometria do HFSS foi concluído para os quatro modelos de rede e para o painel em ZYF300CA-C. A aprovação de ganho e abertura requer os campos radiados. [Modelos das quatro redes](../../hfss/alimentacao/R03) · [Modelo do painel](../../hfss/antenas/P1H_R03_Alongada.aedt)

O acabamento cotado é ENIG. Os modelos de cobre finito usam propriedades nominais sem a camada de níquel-fósforo do banho, e as fitas da emenda usam contato metálico ideal nas superfícies soldadas. O resultado de fabricação depende dessas perdas, das tolerâncias de Dk e das soldas. A cotação e a ficha do fabricante identificam os quatro laminados. [Materiais JLCPCB](https://rs.jlcpcb.com/static/file/ptfe-teflon-datasheet.pdf) · [Acabamentos JLCPCB](https://jlcpcb.com/help/article/jlcpcb-surface-finish) · [Influência do ENIG em microstrip, Rogers](https://www.rogerscorp.com/blog/2020/comparing-pcbs-for-microstrip-and-grounded-coplanar-waveguide-circuits)
