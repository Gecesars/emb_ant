# P2S13 — três placas de dois elementos e alvo H100°

**R11 — radome FR-4 2 mm e C08 fabricável, verificado em 12/11: solução inválida.** O sexto passe terminou em 11/11 às 20:19, com 14 núcleos, sem sweep, duas entradas de 0,5 W/0°. ΔS final **0,138887**, VSWR ativo **1,598/2,023**. O ganho exportado de **14,291 dBi não é válido**: o solver iterativo atingiu 600 iterações sem convergir, residual máximo 0,04803 frente ao alvo 0,00001, e exportou 3,232 W radiados para 1 W incidente. Os cortes exportados H/V são **63,09°/9,85°**, máximo vertical **+0,523°**, assimetria principal **1,375 dB**; são dados de diagnóstico, sem aprovação RF. A C08 passou no DRC com zero erros e zero itens desconectados; os 113 avisos são de máscara totalmente aberta. A correção de fabricação não comprova desempenho. [Relatório, diagramas, CAD, HFSS, KiCad e Gerbers para revisão](fabricavel_radome/README.md). Não foram executados novos passes durante esta verificação.

**KiCad C07 — 11/11:** [PCB editável, Gerbers/Excellon e revisão de fabricação](kicad/divisor_duplo_1x3_C07/README.md). A arte nominal de 220 × 64 mm foi preservada e comparada ao CAD/HFSS e ao CAM exportado. Oito NPTH Ø0,9195 mm, terra até a borda, sem máscara. Zero itens desconectados; nove violações DRC deliberadamente preservadas por refletirem a C07 original. **Requer revisão especial da JLCPCB antes de produzir**, sobretudo para não remover o cobre dos furos NPTH nem alterar a borda do terra. Nenhum novo solve.

**R09 — versão selecionada C07, 11/11.** O usuário aceitou ganho ≥12 dBi incluindo os divisores e priorizou o lóbulo principal vertical simétrico e centrado. Com duas entradas de **0,5 W / 0°**, a correção dos comprimentos físicos das trilhas produziu **12,746 dBi**, VSWR ativo **1,093/1,092**, H/V **98,614°/10,162°** e máximo V **−0,01°** (grade de 0,01°), praticamente em zero. A assimetria em ±4° caiu de **0,550 para 0,060 dB**. Os lóbulos secundários foram registrados, sem nova meta nesta etapa. O divisor convergiu em **seis passes**, **ΔS 0,023112**, dois passes consecutivos ≤0,05, **14 núcleos**, sem sweep e sem reparos Major/Minor. A conexão das matrizes foi conferida no Nexxim. Com a outra entrada casada, VSWR A/B **1,1765/1,2551**; portanto B ainda ultrapassa 1,25 nessa condição distinta. As seis saídas carregadas não têm ondas exatamente iguais: a pequena compensação de fase é física; as duas fontes externas permanecem em fase. **Estudo preliminar**, com as ressalvas de campos/reciprocidade da antena e sem soma da radiação direta do divisor aos diagramas. [Relatório completo, layout, diagramas, nativos e evidências](divisor_duplo_1x3_correcao/README.md).

**Histórico R08, anterior à correção R09:**

**Divisor físico HFSS — C01 de 11/11.** Duas redes 1:3 em uma PCB de 220×64 mm, ZYF300CA-C de 1,52 mm. Cada rede usa estágios Wilkinson desigual/igual e compensação de fase. Após corrigir a junção assimétrica do segundo estágio, o divisor convergiu em seis passes: **ΔS 0,049458, dois passes consecutivos**, 14 núcleos e sem sweep. Carregado pela antena S6: **VSWR ativo A/B 1,319/1,417**, outra entrada casada **1,528/1,642**; ganho frontal **11,772 dBi**, H/V **99,308°/10,321°**, máximos **−17,50°/−0,50°**. **VSWR≤1,25 e ganho≥13 dBi não atingidos.** Nexxim conferiu a matriz; a antena conserva as pendências numéricas anteriores. [Projetos, layout, comparação e diagramas](divisor_duplo_1x3_hfss/README.md). O plano analítico abaixo permanece histórico e não equivale ao desempenho EM do layout.

**P2S13 — continuação concluída em 11/11.** Executados somente os passes 7 e 8 nas três PCBs idênticas de dois elementos, dobra **28,5 mm / 150°**, preservando malha e geometria. Em 5,17 GHz, 14 núcleos, seis entradas de 1/6 W / 0°, sem sweep: **ΔS 0,017600, convergência S atendida**, ganho frontal **13,349 dBi**, H **98,727°**, V **9,931°**, VSWR máximo ativo/casado **1,3220/1,3129**. Estabilidade de campos e reciprocidade estrita ainda reprovam; aprovação conjunta pendente. [Resultados, diagramas e nativos de oito passes](continuacao_tres_placas2/README.md) · [Histórico de seis passes](tres_placas2/README.md).

**Histórico: divisor duplo 1:3 planejado em circuito antes do layout HFSS.** Duas redes Wilkinson idênticas, ajuste comum de entrada e ramais de comprimentos iguais, preservando os seis cabos físicos de 50 mm. No modelo de linhas carregado pelo S6 de oito passes: VSWR ativo A/B **1,1979/1,0895**, outra entrada casada **1,0895/1,1978**, ganho **13,143 dBi**, H/V **98,720°/9,931°**. Nexxim confere a matriz S2 deste modelo. **É um plano analítico preliminar, distinto do layout EM descrito acima.** [Plano, dimensões, circuito nativo e ressalvas](divisor_duplo_1x3/README.md). A antena não foi recalculada durante a criação do divisor. A [campanha 4+2 permanece encerrada](dobras_placas_ajustadas/README.md).

## Histórico anterior: oito níveis e composição 4+2

Nova revisão iniciada em 10/11/2026 após a entrega da mecânica preliminar P2M21 R18. A R18 e seus documentos enviados por e-mail permanecem preservados.

**Revisão histórica, 11/11: dois passes adicionais com a malha preservada.** O conjunto 4+2 concluiu os passes 7 e 8 em 5,17 GHz, com 14 núcleos e quatro entradas iguais/em fase. **ΔS=0,016429**, três passes consecutivos abaixo de 0,05. VSWR ativo PCB2 **1,22085/1,14980**, demais entradas casadas **1,10125/1,14708**: a meta ≤1,25 foi atingida numericamente. Ganho frontal total **10,7554 dBi**, H **86,738°**, V **10,148°**, máximos **−0,50°/+2,50°**. **A validação completa permanece pendente:** uma sonda de campo variou 0,7446 dB e a reciprocidade excedeu o limite da auditoria (3,84×10⁻⁵ contra 1×10⁻⁵). [Comparação, diagramas, evidências e HFSS atualizado](continuacao_placa2/README.md).

Os transformadores simétricos de **0,546717 × 13,151813 mm**, o refletor b10/90 e os cabos físicos foram mantidos. A revisão de seis passes e seus resultados permanecem preservados no [histórico do casamento da PCB2](casamento_placa2/README.md). Nenhum novo sweep ou passe além dos dois solicitados foi executado.

O estudo anterior de seis níveis testou três refletores: [placa nova, resultados e nativos](seis_elementos/README.md). A placa de quatro e a antiga KiCad de dois elementos foram preservadas. O restante desta página registra o estudo inicial de oito níveis.

O usuário confirmou **duas placas C12 de quatro elementos, uma acima da outra**, formando oito níveis em uma coluna. Mantêm-se os divisores impressos, os quatro cabos físicos de 50 mm e as quatro entradas iguais/em fase, com 0,25 W por entrada e 1 W total. A simulação inicial é somente em **5,17 GHz**, sem sweep, com 14 núcleos, até seis passes e alvo ΔS ≤0,05. Não se aplica ganho de uma entrada MIMO isolada.

| Grandeza | Meta |
|---|---:|
| Ganho frontal realizado total | ≥13 dBi |
| Abertura horizontal a −3 dB | 99° a 121° |
| Abertura vertical a −3 dB | 16,2° a 19,8° |

O novo refletor tem comprimento de 392 mm, largura desenvolvida de 90 mm e alumínio de 2 mm. O raio interno nominal das dobras é 2 mm e o fator K usado para preservar a largura desenvolvida é 0,4. A altura da face inferior do núcleo da PCB permanece 14,949 mm. Não foram adicionados apoios plásticos, conectores N ou rede externa ao modelo RF.

Os parâmetros de estudo são a distância **b** entre o eixo central e o início da dobra, medida na face frontal plana, e o ângulo das abas para trás. **0° significa plano; 90° significa aba paralela ao eixo frontal Z, orientada para −Z.** As duas abas são simétricas. Foram calculados o refletor plano e b=20 mm/60°. As demais tentativas foram diagnósticos de malha; não há resultado RF de b=30 mm/60°.

**Ressalva de viabilidade:** o fator de arranjo aplicado aos campos da C12 prevê aproximadamente 7,63° de abertura vertical para as duas PCBs em coluna, contra 15,18° para uma placa. Essa estimativa não inclui o acoplamento ou as dobras do refletor. Ela não é uma solução HFSS do novo painel e mostra por que atingir 110° na horizontal não basta para aprovar o conjunto. A meta vertical será conferida separadamente; não será relaxada silenciosamente.

Os scripts em `automacao` criam geometrias reproduzíveis, validam contatos/interferências, executam os casos em sequência e auditam matrizes, potência, campos, 14 núcleos e convergência real. Resultados que terminarem no limite de seis passes sem convergir serão identificados como preliminares. A geometria CAD é BREP gerado por parâmetros no JSON/script; as propriedades documentais no FreeCAD não recalculam o sólido automaticamente.

Pasta de trabalho: `D:/dev/EMBRAER/P2S13/R00_Refletor_Dobrado`. Estado atual e evidências de execução ficam nessa pasta. O Git não inclui malhas ou campos volumétricos.

## Correção e resultado de 10/11

O gargalo estava na geração inicial do refletor importado, antes dos passes RF. A reconstrução da mesma dobra com arcos, extrusão e furos nativos do HFSS permitiu ao **Classic concluir a malha em 2 min 09 s**, contra uma tentativa original interrompida após **56,66 min**. A geometria foi conferida por diferença booleana e os demais 83 sólidos permaneceram iguais. Não foram usados TAU Flex, operações locais ou refinamento lambda na versão corrigida. [Diagnóstico completo e tentativas rejeitadas](diagnostico_hfss.md).

**Os resultados RF abaixo são preliminares; nenhuma das duas versões está qualificada.**

| Grandeza em 5,17 GHz | Plano | Dobra b=20 mm / 60° | Meta |
|---|---:|---:|---:|
| Ganho frontal realizado total | 14,794 dBi | 12,905 dBi | ≥13 dBi |
| Abertura H | 73,34° | 78,23° | 99–121° |
| Abertura V | 7,58° | 7,54° | 16,2–19,8° |
| VSWR ativo máximo | 1,509 | 1,197 | Informativo |
| Passes / ΔS final | 6 / 0,073777 | 6 / 0,067051 | ΔS ≤0,05 |

Na versão dobrada, os máximos dos cortes são H −6,75° e V −0,25°. O pior VSWR com as outras entradas casadas é 1,302. Todos os passes usaram 14 núcleos; não houve sweep ou reparos Major/Minor. A matriz é passiva e o balanço de potência confere, mas o erro máximo de reciprocidade é 1,2723×10⁻⁵, acima do limite de auditoria de 1×10⁻⁵. Essa reprovação e a falta de convergência foram preservadas, sem relaxar tolerâncias. O estado `REQUER_VERIFICACAO` da fila é uma interrupção da auditoria após o cálculo concluído, não um novo travamento do solver.

[HFSS corrigido](refletor_nativo_b20_60/P2S13_Nativo.aedt) · [FreeCAD](refletor_nativo_b20_60/P2S13.FCStd) · [Dados e verificações](refletor_nativo_b20_60/resultado.json) · [Diagramas polares E/Emax](refletor_nativo_b20_60/polar_HV.png) · [Comparação normalizada](comparacao_normalizada.png) · [Manifesto de arquivos](manifesto_correcao.json).

O nativo fechado, S4 e campos distantes foram arquivados. Os resultados de campo volumétrico e a malha ficam somente na pasta de trabalho: abrir o nativo do Git não restaura a solução de campo completa. Para novas geometrias dobradas, `criar_hfss.py` aceita `refletor_construcao="nativo"` e usa `desenhar_refletor_hfss.py`, que reproduz a construção corrigida. Scripts de diagnóstico são históricos e não devem ser lançados como uma fila de otimização.

As duas PCBs C12 desse estudo permanecem preservadas. A largura vertical obtida é próxima da previsão de oito níveis uniformes e está muito abaixo de 18°. Após esta correção, o usuário escolheu testar seis níveis com uma placa de quatro e outra de dois elementos, exigindo alimentação simétrica na placa nova. Essa continuação está documentada em [seis_elementos](seis_elementos/README.md).
