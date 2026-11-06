# P1H de dez elementos · PCBs e cotação JLCPCB

Consulta pelo Google Chrome em 6 de novembro de 2026, às 14h18, horário de São Paulo. Valores da opção **Web Price** no [configurador JLCPCB](https://cart.jlcpcb.com/quote), com os Gerbers enviados e reconhecidos. A conta exibiu os preços em reais. A cotação é instantânea, sujeita à revisão de engenharia e sem validade formal indicada. A JLCPCB confirmou o armazenamento do upload em **Projects → Quotes**.

## Preço de fabricação

| PCB nua | Dimensões no KiCad | Lote | Preço do lote | Por PCB | Fabricação |
|---|---|---:|---:|---:|---|
| Coluna em uma PCB, dez radiadores | 501,7125 × 28,3125 mm | 5 | R$ 655,64 | R$ 131,13 | 4–5 dias |
| Radiador individual | 28,3125 × 28,3125 mm | 10 | R$ 550,16 | R$ 55,02 | 4–5 dias |
| Radiador individual | 28,3125 × 28,3125 mm | 50 | R$ 701,53 | R$ 14,03 | 6–7 dias |
| Divisor com duas entradas e vinte saídas | 39 × 78 mm | 5 | R$ 536,50 | R$ 107,30 | 4–5 dias |

| Conjuntos | Compras de PCBs | Total | Média por conjunto completo |
|---|---|---:|---:|
| 1 protótipo com radiadores separados | 10 radiadores + 5 divisores, com quatro divisores de reserva | R$ 1.086,66 | — |
| 5 com placa contínua | 5 colunas + 5 divisores | R$ 1.192,14 | R$ 238,43 |
| 5 com radiadores separados | 50 radiadores + 5 divisores | R$ 1.238,03 | R$ 247,61 |

Para um protótipo, os elementos avulsos exigem R$ 105,48 a menos de desembolso que os lotes de cinco colunas e cinco divisores. Para cinco conjuntos, a placa contínua reduz a despesa em R$ 45,89 no lote. O modelo de HFSS com ganho mínimo de 16,58 dBi usou substratos individuais ao passo de 52,60 mm. A região entre os elementos da opção contínua contém laminado Rogers e requer nova simulação para determinar o ganho e as aberturas dessa versão.

O comércio eletrônico mostrou frete indicativo individual DHL Express de R$ 221,61 e trânsito de 4–6 dias úteis. O total com frete consolidado e tributos depende do checkout. Os valores da tabela cobrem apenas as PCBs, incluindo os serviços da fábrica discriminados no configurador. Os cabos, a soldagem, os refletores metálicos, os suportes e a montagem são itens adicionais. A opção de produto habilitada para os laminados foi **Industrial/Consumer electronics**. A opção **Aerospace** apareceu desabilitada. Os valores correspondem a protótipos nessa categoria. A comparação foi encerrada antes do carrinho e do pagamento.

## Desenhos e verificação

* **Antenas.** Rogers RO4350B, núcleo de 0,76 mm, duas faces de cobre 1 oz, ENIG 1 µin, máscara verde aberta sobre a área ativa em ambas as faces e vias expostas. A face superior contém as alimentações A/B. A face inferior contém os quatro setores do radiador, a ponte de cruzamento e os contatos das malhas coaxiais. O Dk de projeto no KiCad é 3,66, conforme o HFSS. O catálogo do fabricante identifica o laminado pelo Dk de processo de 3,48. [Materiais disponíveis](https://jlcpcb.com/pcb-fabrication/high-frequency-pcb)
* **Passagem das sondas.** Em cada posição há duas vias metalizadas de 0,40 mm e dois furos metalizados de 0,85 mm para sondas de 0,726 mm. Os pads das sondas têm 1,20 mm de diâmetro. A furação de 0,85 mm permite folga para a tolerância negativa de 0,08 mm publicada pela JLCPCB. A malha coaxial tem área de soldagem anular no quadrante correspondente. São adaptações para a montagem do modelo no protótipo. A PCB individual usa quatro furos, a contínua usa quarenta. [Tolerâncias de fabricação](https://jlcpcb.com/capabilities/pcb-capabilities/)
* **Divisor.** A mesma revisão KiCad 2 × 1:10 do estudo de alimentação usa PTFE ZYF300CA-C de 1,52 mm, duas faces de cobre 1 oz e ENIG 1 µin. O Gerber tem 22 furos metalizados de 1 mm. Os vinte cabos coaxiais de saída são iguais, com comprimento nominal de 254 mm.
* **DRC e Gerbers.** O KiCad 10.0.5 encontrou zero erros e zero pads desconectados nas duas PCBs de antenas. Os avisos de máscara ocorrem nas janelas intencionais que expõem várias redes na área de RF. O divisor passou no DRC original sem violações. As coordenadas de furação e os quatro segmentos de contorno das antenas foram verificados nos arquivos exportados. A área de cobre dos Gerbers foi comparada à geometria dos radiadores com os pads de fabricação nas duas faces. A JLCPCB identificou as três placas com duas camadas e confirmou as dimensões, arredondadas a 0,01 mm.

## Revisões cotadas

| Pacote Gerber | SHA-256 |
|---|---|
| Gerber_P1H_Individual.zip | `6efeaacbe9695f4c32f228e3225698d3338586ca4ebf4af5a1c6ec5a041062c0` |
| Gerber_P1H_Coluna_10.zip | `6f7b16622e02315e772a2115624d73dff43d2ac2e488a7dcc91708f004db86d8` |
| Gerber_Divisor_PTFE_2x10.zip | `17813005736f5d3bb52e95a45e8aef289bdc1a86a5ba025c7a799501987d5729` |

[Coluna contínua, 5 peças](cotacao_coluna_5.jpg) · [Antena individual, 10 peças](cotacao_individual_10.jpg) · [Antena individual, 50 peças](cotacao_individual_50.jpg) · [Divisor, 5 peças](cotacao_divisor.jpg)
