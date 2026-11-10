# P2S13 — estudo do refletor para 110° horizontal

Nova revisão iniciada em 10/11/2026 após a entrega da mecânica preliminar P2M21 R18. A R18 e seus documentos enviados por e-mail permanecem preservados.

**Revisão atual: seis níveis, placa C12 de quatro elementos e nova placa de dois com alimentação simétrica.** Os três ensaios do refletor terminaram em seis passes, 14 núcleos, 5,17 GHz, sem sweep. A maior abertura horizontal preliminar foi **85,91°**, com **10,145 dBi**, V **10,26°** e VSWR ativo máximo **1,943**, para b=10 mm/90°. Nenhum ensaio confirmou dois passes consecutivos de convergência ou atingiu as metas. [Placa nova, três resultados, desenhos e nativos](seis_elementos/README.md). A placa de quatro e a antiga KiCad de dois elementos foram preservadas. O restante desta página registra o estudo anterior de oito níveis.

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
