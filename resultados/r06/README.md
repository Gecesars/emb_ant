# R06 · PCB contínua e divisores compactos qualificados

**Qualificação numérica concluída em 8/11/2026.** A PCB contínua completa e as duas distribuidoras foram resolvidas separadamente no HFSS. O circuito combina as matrizes S20/S18/S12 e os campos complexos, com acoplamento dentro de cada placa e reflexões múltiplas. Os cabos são linhas ideais de fase, sem atenuação; os conectores N são interfaces ideais.

[Relatório completo ilustrado — 15 páginas](P1H_R06_Relatorio.pdf) · [Síntese rastreável](circuito/qualificacao_final.json) · [Mecânica e desenhos A3](../../freecad/mecanica_R06/README.md).

## Resultado final em 5,17 GHz

Duas entradas de **0,5 W a 0°**, normalizadas em 50 Ω. O ganho inclui descasamento e perdas das PCBs e das bobinas, com correção da atenuação dos acessos do cupom.

| Métrica | Resultado | Critério |
|---|---:|---:|
| Ganho frontal realizado total | **17,3593 dBi** | ≥16 dBi |
| Abertura horizontal a −3 dB | **96,0643°** | 81–99° |
| Abertura vertical a −3 dB | **5,6158°** | Feixe mais estreito permitido |
| VSWR ativo A / B | **1,2115 / 1,1292** | Ambos <1,5 |
| VSWR com outra entrada casada A / B | **1,2321 / 1,2474** | Ambos <1,5 |

A margem de ganho é **1,3593 dB**. O caso com cupom bruto da bobina também atende, com 17,3465 dBi. [Resultados completos](circuito/resultado.json) · [Diagrama numérico](circuito/diagrama.csv).

## Verificação numérica

A PCB convergiu em **23 passes e 6.665.585 tetraedros**, antes do máximo de 25. Os dois últimos ΔS foram **0,00315575 / 0,00136256**, abaixo de 0,004; as maiores variações nas nove direções foram **0,0100888 / 0,00686547 dB**, abaixo de 0,02 dB. A auditoria confirma o mínimo de passes, dois passes em S/campo e ausência de reparos Major na execução refinada. Há dois corpos Minor.

Frente à solução preservada de 21 passes, as mudanças foram **−0,000581 dB** no ganho, **+0,118830°** em H, **−0,000784°** em V e no máximo **0,002717** em VSWR. Todos os limites de estabilidade foram cumpridos. O Nexxim reproduziu a matriz do circuito com erro máximo **4,65 × 10⁻¹⁵**. As matrizes são passivas e recíprocas; o balanço de potência fecha com resíduo **3,61 × 10⁻¹⁶ W**, e a recomposição uniforme dos campos confere com o HFSS a menos de **6,36 × 10⁻¹³ dB**.

[Convergência final](antena/auditoria_convergencia.json) · [Comparação de malhas](circuito/comparacao_malhas.json) · [Nexxim](circuito/verificacao_nexxim.json) · [Histórico de malha e recuperação de memória](conferencia_malha.md). As comparações anteriores reprovadas e a falha por falta de memória permanecem documentadas.

## Construção e fabricação

Antena em **RO4350B de 0,76 mm**, εr de projeto 3,66 / tanδ 0,0037. Distribuidoras em **ZYF300CA-C de 1,52 mm**, εr 2,94 / tanδ 0,0016. Cobre físico 35 µm e ENIG unilateral com Au 0,0254 µm e NiP nominal de 4,5 µm / 1,5 MS/m. O modelo mantém a rugosidade equivalente de cobre de 0,5 µm.

A montagem usa refletor de alumínio de **2 mm**, apoios de poliacetal de **5 mm**, dois N fêmea e duas bobinas de curto DC. Comprimentos de entrada/enlace/ramal: **290 / 132 / 133 mm**, total do chicote 3.768 mm, caminho por radiador 555 mm. Folga nominal mínima de 0,7611 mm e zero interseções volumétricas. Os cabos permanecem no FreeCAD para fabricação.

DRC de 7/11: **zero erros e zero itens desconectados** nas três PCBs. A coluna tem 203 avisos de ponte de máscara nas aberturas RF, preservados; os divisores não têm avisos. Os Gerbers R02 permanecem inalterados. [Verificação de fabricação](fabricacao/verificacao.json).

[Cotação JLCPCB de 7/11](cotacao.md): cinco colunas por R$657,83, cinco distribuidoras inferiores por R$632,75 e cinco superiores por R$538,28. Total **R$1.828,86 para cinco conjuntos**, equivalente a **R$365,77 por conjunto**, sem frete consolidado e tributos; nenhuma compra efetuada.

## Alcance da entrega

O aceite é **somente em 5,17 GHz**. As distribuidoras têm 17 pontos em 5,09–5,25 GHz; a antena S20 de um ponto não qualifica ganho/VSWR do painel em toda a banda. O modelo separado exclui radiação dos trajetos de cabo, acoplamento eletromagnético entre placas distintas e perdas dos cabos/N. Materiais e ENIG são nominais. A qualificação numérica não substitui medição do conjunto real, inspeção de continuidade DC e ensaio de vedação.

O pacote inclui HFSS/Circuit, Touchstone, quarenta campos H/V por malha preservada, KiCad/Gerbers, FreeCAD, STEP/DXF, desenhos A3, imagens e relatório. **Sem malhas, campos volumétricos ou resultados nativos de solver no Git.** [Manifesto de entrega](manifesto_entrega.json) · [Revisão do PDF](revisao_relatorio.json) · [Scripts de reprodução](../../automacao/r06).

Relatório e três pranchas A3 enviados para **gecesars@gmail.com em 8/11/2026**, com confirmação do marcador de enviado e dos dois anexos. [Registro da entrega](entrega_email.json). A automação de acompanhamento foi encerrada.
