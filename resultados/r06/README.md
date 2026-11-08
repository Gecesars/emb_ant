# R06 · PCBs separadas e circuito sem perda de cabos

**Em qualificação, ainda sem resultado final aprovado.** O usuário alterou o método e o aceite em 7 de novembro de 2026. O cálculo integral R05 com cabos foi encerrado; não será retomado.

O aceite é em **5,17 GHz**, com duas entradas de **0,5 W a 0°**: ganho frontal realizado total **≥16 dBi**, abertura horizontal **81–99°** e **VSWR <1,5** nas duas entradas. O feixe vertical pode ser mais estreito que 7°. As perdas dos cabos são excluídas. O relatório distingue VSWR ativo e VSWR com a outra entrada casada.

## Modelos

- PCB contínua completa de dez elementos: matriz de vinte portas e campos embutidos, incluindo acoplamento entre radiadores, refletor e apoios. Sem chicote 3D, N ou distribuidoras.
- Distribuidora inferior: matriz de dezoito portas, com as duas divisões 1:2 e as duas redes 1:5 na mesma placa.
- Distribuidora superior: matriz de doze portas, com ambas as polarizações. Todas as portas não excitadas ficam casadas em 50 Ω na extração.
- Circuito: reflexão múltipla e acoplamento por matrizes S completas; linhas ideais de fase conservam os comprimentos elétricos, com correção dos planos de referência.
- Bobinas: cupom R05 de duas espiras, raio médio 0,9 mm, fio de 0,3 mm; comparação com e sem bobina e correção da atenuação dos acessos do cupom.

A qualificação exige convergência de S e das nove amostras de campo. O critério é ΔS ≤0,008 e variação de campo ≤0,05 dB, ambos em dois passes consecutivos. Os vinte campos unitários serão recombinados coerentemente com as excitações calculadas pelo circuito. O resultado matricial será confrontado com o Ansys Circuit/Nexxim.

Os materiais nominais são RO4350B de 0,76 mm na antena e ZYF300CA-C de 1,52 mm nas distribuidoras. O cobre físico tem 35 µm e acabamento ENIG unilateral, com NiP de 4,5 µm / 1,5 MS/m nominal e Au de 0,0254 µm. O modelo mantém a rugosidade de cobre equivalente adotada na R05. As dimensões dos Gerbers permanecem iguais à R02.

## Evidências disponíveis

Em 7/11, a primeira malha da PCB isolada convergiu em **16 passes**, com **2.192.285 tetraedros**. Os dois últimos ΔS foram 0,0064491 e 0,0059832; a maior mudança das nove amostras de campo foi 0,046556 e 0,049962 dB. Com vinte entradas diretas uniformes, apresentou **17,3975 dBi, H = 95,0569° e V = 5,5589°**, apenas em 5,17 GHz.

Esses números **não aprovam ainda o painel com a rede**. Há um aviso de reparo superficial em um pequeno fragmento de cobre; sua verificação com malha local mais fina está em execução. Os dois divisores completos concluíram os 17 pontos de 5,09 a 5,25 GHz, ambos em nove passes, com dois passes de convergência e sem reparos Major/Minor. Os quarenta campos H/V exportados recompõem o diagrama uniforme com erro máximo de 6,3 × 10⁻¹³ dB.

O circuito original de 290 / 132 / 135 mm falhou no VSWR convencional da entrada B: **1,531**, apesar de o VSWR ativo atender. O ajuste de vinte ramais para **133 mm**, com os enlaces e as entradas preservados, apresenta os seguintes resultados **preliminares**, usando a primeira malha da PCB e as matrizes finais dos divisores:

| Métrica em 5,17 GHz | Resultado preliminar |
|---|---:|
| Ganho frontal realizado total | 17,3477 dBi |
| Abertura horizontal | 95,2059° |
| Abertura vertical | 5,6197° |
| VSWR ativo A / B | 1,2303 / 1,1539 |
| VSWR com outra entrada casada A / B | 1,1965 / 1,2260 |

O Nexxim conferiu a matriz do circuito com erro máximo de **9,05 × 10⁻¹⁵**. As perdas das PCBs e da bobina corrigida estão incluídas, com zero atenuação nos cabos. **Ainda não há aceite final:** falta a solução refinada e a verificação de estabilidade de ganho, diagrama e VSWR. [Evidências preliminares](preliminar_133/resultado.json) · [Nexxim](preliminar_133/verificacao_nexxim.json).

A nova [montagem R06](../../freecad/mecanica_R06/README.md) foi verificada, com folga nominal mínima de 0,7611 mm e nenhum cruzamento dos cabos. As geometrias fora do chicote são iguais às da R05; os Gerbers permanecem iguais. A recuperação da licença preservou o centro convergido da distribuidora superior e retomou apenas a varredura restante.

Atualização às 19:58: a malha local refinada concluiu em 11 passes e manteve **17,3447 dBi, H 94,3761° e VSWR máximo 1,23735**. Entretanto, H mudou 0,82976° em relação à primeira malha, acima da tolerância de estabilidade de 0,5°. A continuação iniciou no passe 12 com critérios mais rigorosos de S/campo, preservando a malha. O Major anteriormente contado era histórico: a execução refinada possui zero Major e dois Minor. [Conferência e evidências](conferencia_malha.md). O aceite continua pendente.

Atualização às 22:58: a continuação rigorosa convergiu em **21 passes**, com **17,3599 dBi, H 95,9455° e VSWR máximo 1,24633** no circuito. A mudança de H em relação aos 11 passes ainda superou a tolerância interna de estabilidade. Uma conferência com pelo menos dois passes adicionais foi iniciada, preservando os mesmos critérios e o refinamento de 15%. [Histórico completo](conferencia_malha.md). **Ainda não é aceite final.**

O DRC de 7/11 no KiCad 10.0.5 encontrou zero erros e zero itens desconectados nas três placas. A coluna tem 203 avisos de ponte de máscara nas aberturas RF; os divisores não têm avisos. [Evidências e hashes](fabricacao/verificacao.json). Os Gerbers não foram alterados.

[Cotação JLCPCB de 7/11](cotacao.md) · [Vistas detalhadas do CAD](imagens) · [Scripts R06](../../automacao/r06) · [Montagem e fabricação da chapa](../../freecad/mecanica_R06/README.md).

O relatório completo, os nativos RF finais e a mensagem por e-mail serão publicados após a qualificação. A varredura dos divisores não será apresentada como banda validada da antena; não se congela a matriz da PCB em 5,17 GHz para alegar aprovação entre 5,09 e 5,25 GHz.
