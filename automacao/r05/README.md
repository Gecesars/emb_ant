# Correção da alimentação da placa contínua

A R05 busca ganho realizado em +Z de pelo menos 16 dBi e abertura horizontal de 81° a 99° na banda de 5,09 a 5,25 GHz. A excitação operacional continua sendo de 0,5 W a 0° em cada entrada N. A referência é a placa contínua de dez elementos com os dois divisores compactos, os 26 coaxiais, o refletor e os apoios da R02.

O diretório de trabalho desta campanha é `D:/dev/EMBRAER/P1H/R05_Correcao`. Os campos, as malhas e os arquivos temporários são gerados nesse diretório.

## Diagnóstico e geometria

- `diagnosticar_r02.py` abre os campos convergidos da R02 e exporta separadamente os campos complexos de A e B. A recombinação confirma 11,99775 dBi com ambas as entradas. As impedâncias ativas são aproximadamente 21,35 − j103,42 Ω e 28,79 − j54,22 Ω. A integração de perdas por objeto exige conferência do fechamento do balanço antes de atribuir a perda a um componente.
- `cupons_cad.py` mantém a blindagem e o PTFE do coaxial, com uma abertura radial de 1 mm para o terminal da bobina. Compara raios médios de 0,65, 0,75 e 0,90 mm, duas espiras, passo de 0,73 mm e fio de 0,30 mm. O controle tem a mesma abertura e o pino livre da bobina. O cobre e o PTFE têm as mesmas propriedades nominais da R02. O esmalte permanece uma hipótese a qualificar.
- `cupons_hfss.py` reutiliza as portas, referências e o solver do cupom R01. `avaliar_cupons.py` exige dois passes consecutivos convergidos, as 17 frequências, passividade e reciprocidade. O raio de 0,90 mm apresentou perda de 0,02138 dB no centro e retorno mínimo de 30,44 dB na banda, frente a 1,10 dB no cupom da entrada anterior.
- `entrada_painel_cad.py` aplica a terminação selecionada aos dois coaxiais completos da R02. A continuidade em CC resulta de um sólido único de cobre por entrada. O gerador confere a separação entre cobre e PTFE.
- `entrada_painel_hfss.py` aplica as quatro peças alteradas numa cópia nativa da R02. O primeiro candidato usa `P1H_R05_WORK=<diretório de trabalho>/painel_entrada` e `P1H_RAIO_BOBINA=0.9`.

## Simulações de diagnóstico e do painel

`antena_direta_cad.py` extrai a placa contínua, o refletor, os apoios e vinte terminações coaxiais, com planos a Z = −4 mm. `antena_direta_hfss.py` calcula a matriz de vinte portas e o campo com alimentação uniforme de 0,05 W por porta. Esse diagnóstico permite avaliar o carregamento dos divisores. `extrair_20portas.py` exporta os padrões complexos de cada porta, mantendo as demais terminadas em 50 Ω. A combinação com a rede deve respeitar esses planos e descontar os trechos já presentes no FEM.

`conector_cad.py` e `conector_hfss.py` isolam a representação nominal do N da R02, com planos em X = −288 e −260 mm. Essa representação será comparada à especificação do componente selecionado. O fabricante declara retorno de 25 dB até 6 GHz, contato BeCu prateado e corpo de latão com bronze branco. As dimensões internas do modelo anterior são aproximadas. [Desenho Amphenol 082-6784](https://www.amphenolrf.com/en-us/assets/file/4069129560/)

## Resultados de diagnóstico e candidato físico

O diagnóstico com vinte portas e face do refletor de 36 mm convergiu em oito passes, com 611.595 tetraedros. Os dois últimos valores de ΔS foram 0,008911 e 0,006085. Com 0,05 W por porta, resultou em 17,23715 dBi em +Z, abertura H de 100,59918° e V de 5,60515°. A recombinação dos vinte campos individuais reproduziu os dois cortes nativos com erro máximo inferior a 10⁻¹¹ dB. Esse resultado exclui a rede traseira.

`rede_carregada.py` conecta a matriz de vinte portas às matrizes nativas dos divisores, bobinas e conectores e aos coaxiais com perdas. Os planos descontam os 20,61 mm de coaxial já presentes no diagnóstico dos radiadores e os lançamentos incluídos nos cupons. A predição com a nova bobina e os comprimentos anteriores foi 16,035 dBi e H = 100,658°. A otimização dos três comprimentos comuns produziu 16,554 dBi e H = 100,503°, com 287,582 / 134,139 / 142,139 mm. **Nenhum desses casos atende à abertura horizontal.**

Essa combinação por blocos é usada para selecionar candidatos, não para aprovação. Com o cupom da bobina antiga, ela prevê 13,791 dBi, enquanto o FEM integral R02 resultou em 11,998 dBi. Portanto, as interações físicas e diferenças dos lançamentos entre os blocos e a montagem integral não podem ser ignoradas.

O candidato realizável usa face de 40 mm no refletor e cabos de 288 / 134 / 142 mm: duas entradas, quatro enlaces e vinte ramais, respectivamente, totalizando 3.952 mm de coaxial. `ajustar_chicote.py` procura percursos com curvas de raio 4,4 mm. `painel_cad.py` verifica as interferências pelo OCCT: nenhuma colisão e folga mínima de 0,771694 mm entre as capas. O arquivo `candidato288/cad/verificacao.json` registra todos os comprimentos.

O diagnóstico da face de 40 mm convergiu em oito passes (618.859 tetraedros, ΔS final 0,0062692 e dois passes consecutivos). Resultou em 17,38285 dBi, H = 97,20526° e V = 5,60852° nos planos dos vinte coaxiais. Com os cabos de 288 / 134 / 142 mm e a rede em cobre, a predição por blocos é 16,70225 dBi, H = 97,13069° e V = 5,58101°. É uma predição de centro de banda; não substitui o FEM integral com ENIG.

`refletor_parametrico.py` gera a chapa dobrada e planificada em FCStd e o corte/marcação de dobras em DXF 1:1. A diferença simétrica entre o refletor paramétrico de 40 mm e a geometria usada no RF foi zero. O DXF contém 39 contornos fechados e passa pela conferência independente de área/volume com o fator K = 0,4 e raio interno de 2 mm.

`alargar_refletor.py` preserva os furos e a aba inferior, amplia a alma e desloca as nervuras. A simulação de vinte portas em `face40/antena_direta` verifica a mudança de diagrama. A versão integral está em `candidato288_enig/estudo/P1H_R05_ENIG.aedt`, com duas entradas de 0,5 W a 0°. Sua aprovação exige convergência por dois passes, estabilidade das métricas e os 17 pontos da banda. A ordem inicial do FEM integral é zero para acomodar a montagem na memória disponível, como na referência R02; o diagnóstico de vinte portas usa ordem mista. Não há aprovação do conjunto até a exportação dos resultados correspondentes.

As etapas preliminares `painel_entrada` (refletor de 36 mm) e a geração de malha de `candidato288` (cobre sem ENIG) foram canceladas para priorizar o candidato final. Seus arquivos não são evidência de convergência.

## Acabamento metálico

O ENIG usa cobre de 35 µm, NiP de 4,5 µm e ouro de 0,0254 µm (1 µin). A espessura de níquel é o meio da faixa de 3–6 µm publicada pela [JLCPCB](https://jlcpcb.com/help/article/jlcpcb-surface-finish). A condutividade de NiP adotada, 1,5 MS/m, é uma hipótese nominal dentro da faixa de resistividade de 50–100 µΩ·cm publicada por um [fornecedor de niquelação química](https://nationalelectrolessnickel.com/specs_medium_phosphorus.htm). Não é um certificado do processo JLCPCB. Foi adotada permeabilidade relativa unitária.

`enig_divisores.py` aplica os filmes nos dois estágios isolados. `enig_painel_cad.py` remove das folhas apenas as áreas cobertas por metal volumétrico; o condutor que cobre a área permanece. Isso permite usar shell elements com material de solução em ambos os lados. `enig_boundary.py` confere a normal importada por espessamento de uma cópia descartável e posiciona o ouro na face exposta. Cobre e revestimento não são trocados de lado por uma orientação incidental do STEP.

O HFSS 2024 R2 exige rugosidade zero no atributo do shell. Por isso, a rugosidade RMS de cobre de 0,5 µm é representada pela condutividade equivalente σ/K², com o fator de [Groiss](https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v251/en/Subsystems/HFSS3DLayout/Content/HFSS/GroissModel.htm) avaliado em 5,25 GHz. Isso conserva a impedância de superfície do cobre espesso no limite superior da banda. A ficha `enig_hfss.json` registra o valor usado e as orientações. A [documentação de shell elements](https://ansyshelp.ansys.com/public/views/secured/electronics/v252/en/Subsystems/HFSS/Content/HFSS/ShellElementsTheory.htm) descreve as incógnitas separadas em cada face.

Os dois estágios convergiram por dois passes consecutivos e foram calculados nas 17 frequências. O 1:2 apresentou perda excedente de 0,24277 dB no centro, contra 0,22902 dB no cobre. O 1:5 apresentou 0,33179 dB, contra 0,32485 dB. O acréscimo nominal conjunto foi cerca de 0,021 dB. `analisar_enig.py` confere passividade, reciprocidade, frequências e fechamento de potência dos cupons. O conjunto ainda precisa de validação integral.

O conector N permanece uma representação nominal com dimensões internas aproximadas; o seu cupom apresentou retorno mínimo de 12,24 dB, diferente dos 25 dB especificados pelo fabricante até 6 GHz. O CAD/dados de RF do fabricante exigem autenticação, solicitada ao usuário no Chrome. O esmalte da bobina também permanece uma hipótese a qualificar. Esses limites precisam constar do relatório de resultados.

## Seleção pela pior frequência da rede

`otimizar_banda_rede.py` usa as matrizes dos divisores ENIG, bobinas e conectores em cada frequência, mantendo temporariamente a matriz e os campos da antena em 5,17 GHz. Essa aproximação serve para selecionar o chicote, **não é uma simulação da antena em toda a banda**. O candidato de 288 / 134 / 142 mm mostrou uma queda nessa análise, de 16,68 dBi no centro para 15,74 dBi no extremo. Portanto, sua malha integral foi interrompida antes de produzir resultados, para priorizar uma solução mais larga em frequência.

O novo candidato usa **290 / 132 / 135 mm**, total de **3.808 mm**, com previsão de 16,55 a 16,66 dBi na análise de antena congelada. A solução numérica não arredondada foi 290,393 / 132,052 / 134,751 mm. A busca também encontrou 274 / 138 / 138 mm, mas o roteamento pesquisado não encontrou folga realizável nas entradas; esse candidato não foi construído.

Os arquivos `candidato290/cad/verificacao.json` e `candidato290/compacta/chicote_ajustado.json` confirmam os comprimentos, nenhuma colisão e folga mínima OCCT de 1,259530 mm entre capas. A montagem nativa está em `candidato290/cad/Painel_R05.FCStd`. O modelo completo com ENIG em `candidato290_enig/estudo/P1H_R05_ENIG.aedt` passou por `ValidateDesign = 1`, porém **falhou no solver em 7/11/2026 às 12:10**, porque a fronteira shell `ENIG_inverso` ainda tocava metais volumétricos. Não produziu campos convergidos. A validação inicial da geometria não detectou essa restrição do solver.

`sensibilidade_conector.py` substitui os dois N por uma hipótese passiva e recíproca com retorno de 25 dB, perda de 0,15 dB e 73 fases de reflexão. A perda adotada é um limite de projeto hipotético, não uma especificação verificada do 082-6784. Com a antena congelada, a previsão mínima foi 16,48285 dBi. O teste não elimina a necessidade de medir ou obter os dados do conector real.

## Sensibilidade ao esmalte

`esmalte_cad.py` e `esmalte_hfss.py` acrescentam uma película hipotética de 20 µm somente à hélice, com permissividade 4,5 e tangente de perdas 0,03. As pontas são consideradas sem esmalte. Não são propriedades certificadas de um fio comprado. O cupom convergiu em cinco passes, 41.239 tetraedros, com ΔS final de 0,001467 e dois passes consecutivos abaixo de 0,008. Foram calculadas as 17 frequências.

O cupom revestido apresentou perda de 0,02094 dB no centro e retorno mínimo de 30,784 dB. Ao substituir as duas bobinas no modelo de rede, o efeito no ganho previsto ficou entre −0,00239 e +0,00124 dB. `avaliar_esmalte.py` confere esses resultados. O painel integral conserva a geometria de cobre sem película; o teste de cupom documenta a pequena sensibilidade **nessa hipótese**, sem qualificar todo esmalte comercial.

## Representação volumétrica do cobre

`cobre_volumetrico_cad.py` cria os 138 sólidos impressos com espessura física de 35 µm, deslocada para fora do laminado, retirando os volumes ocupados por pinos, vias e soldas. O cobre permanece sem solução volumétrica interna. `enig_solido.py` aplica ouro e NiP por impedância estratificada unilateral nas faces expostas, com cobre semi-infinito como camada posterior. A face do cobre junto ao laminado permanece em cobre. A aproximação é apropriada porque 35 µm excede muitas profundidades de penetração nessa banda; evita as condições de contato incompatíveis dos shell elements. As propriedades nominais e a equivalência de rugosidade são as mesmas do estudo anterior.

`divisor_solido.py` verifica primeiro essa representação no divisor isolado 1:2. `painel_solido_hfss.py` constrói o painel em `candidato290_solido/estudo/P1H_R05_SOLIDO.aedt`. Inclui controle de curvatura nas vinte vias (desvio superficial de 0,002 mm), após a malha anterior ter registrado reparo importante em `Via04_0`. `criterios_campo.py` exige ΔS ≤ 0,008 e alteração absoluta ≤ 0,05 dB no ganho frontal e em oito amostras próximas às bordas H/V, durante dois passes consecutivos. A análise do diagrama completo continua obrigatória. O teto de 18 passes não é aceitação por si só.

Ao iniciar esse modelo com `executar_candidato.ps1`, fornecer `-Nome P1H_R05_SOLIDO -Marcador MODELO_SOLIDO_OK -PreservarSetup`. A opção preserva os critérios de campo; sem ela, o executor histórico configura apenas ΔS = 0,015. Os resultados do painel e a verificação nos 17 pontos ainda precisam ser produzidos antes de aprovar o projeto.
