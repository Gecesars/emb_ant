# Correção da geração de malha — 10/11/2026

**A geração inicial foi corrigida pela reconstrução do refletor com primitivas nativas do HFSS.** O Classic concluiu em **129,22 s (2 min 09 s)**, com **114.371 tetraedros**, estatísticas dos **84 corpos** e nenhuma mensagem de erro ou aviso. A tentativa original com refletor importado foi interrompida após 56,66 min sem concluir. A referência plana levou 4 min 03 s. Os dados suportam atribuir o gargalo à representação da dobra e à sua recuperação pelo gerador de malha; não foi diagnosticada uma falha específica do kernel interno do Ansys.

O atraso ocorreu na **geração inicial de malha, antes de qualquer passe de RF**. A referência plana e o primeiro refletor dobrado tinham AnalysisSetup e configurações iniciais de malha iguais. Não foi encontrado sweep acidental, aumento do limite de passes, uso de refinamento lambda ou mudança de materiais. O modelo possui 83 sólidos físicos mais a região de ar.

| Ensaio | Geometria / método | Observação medida |
|---|---|---|
| Referência plana | Classic | Malha inicial em 4 min 03 s; seis passes RF em mais 14 min 30 s. ΔS final 0,073777: não convergiu. |
| Dobra b=20 mm / 60° | Classic original | Interrompido após 56,66 min de geração inicial; nenhum passe RF. |
| Mesma dobra | TAU estrita | Falhou na geração volumétrica; nenhum passe RF. |
| Mesma dobra | Classic, resolução superficial dinâmica | Interrompido após aproximadamente 12 min; nenhum passe RF. |
| Mesma dobra | Classic, controle de aspecto apenas no refletor | Triangulação do refletor melhorou; interrompido após 411 s sem conclusão volumétrica. |
| Mesma dobra | TAU Flex | Malha completa em 47,16 s, mas dois corpos com reparo pequeno: resultado não liberado para RF. |
| Mesma dobra | TAU Flex, controle de aspecto na interface | Malha completa em 51,63 s; mesmos dois avisos. Inspeção identificou vértices sinalizados fora da trilha: resultado não liberado para RF. |
| Mesma dobra | TAU Flex, prioridade em quatro objetos | Malha em 49,25 s; aviso transferido para outra trilha e duas faces de porta. Não liberada. |
| Mesma dobra | TAU Flex, prioridade em todo o cobre/PCBs/portas | Malha em 67,54 s; contornos de alta prioridade mal preservados e avisos de não planaridade. Não liberada. |
| Mesma dobra reconstruída nativamente | Classic, sem operações locais | **Malha em 129,22 s, sem avisos; 114.371 tetraedros. Auditoria aprovada para retomar o RF.** |

Os tempos das tentativas interrompidas são tempos transcorridos até a interrupção, não previsões de tempo de conclusão. Os testes de diagnóstico executaram apenas `GenerateMesh`. Após a aprovação da malha nativa, foi executado um cálculo RF central, descrito abaixo.

## Evidências geométricas

O CAD original contém sólidos válidos e não apresentou sobreposição entre os cabos e o refletor. A conferência de uma exportação feita pelo próprio HFSS reproduziu a folga mínima de 0,3095 mm entre blindagem e refletor. Não houve alteração das placas C12 para esses testes.

Na triangulação intermediária do teste com resolução dinâmica, o pior triângulo do refletor tinha aresta máxima de 289,95 mm e altura mínima de 0,00661 mm. O controle local de aspecto melhorou sua medida de qualidade mínima de 0,00003948 para 0,014167, cerca de 359 vezes. Isso não bastou para demonstrar que a geração volumétrica seria concluída: qualidade superficial e conclusão volumétrica são verificações distintas.

No TAU Flex, o refletor apresentou recuperação superficial de 100% e nenhum reparo. Os avisos foram em `R2_PCB_RO4350B` e `R2_F_SIG_A_Cu0`. A análise de todos os vértices sinalizados do ensaio com controle de aspecto encontrou distâncias máximas ao sólido CAD de 0,035 mm e 2,328 mm, respectivamente. Essa análise mede posição dos vértices; não comprova conectividade ou completude das superfícies. Por isso a ausência de reparo classificado como grave, isoladamente, não foi aceita como validação.

## Correção aplicada e conferida

As tentativas com TAU Flex foram rejeitadas pela auditoria. O ensaio `v12_b20_a60_refletor_nativo` reconstrói somente o refletor com arcos, extrusão e cilindros nativos do HFSS, usando as mesmas dimensões, raios e furos. Volumes, identificadores de faces e caixas envolventes dos outros 83 sólidos foram conferidos iguais, assim como materiais, Boundaries e AnalysisSetup. A comparação booleana entre o refletor original e uma exportação do refletor nativo não encontrou diferença volumétrica dentro da tolerância do kernel CAD. Ambos têm 18 faces.

Esse ensaio voltou ao Classic, sem operações locais de refinamento, sem prioridade especial e sem reparos tolerantes. A geração inicial concluiu sem avisos e foi auditada antes de retomar o cálculo RF. O Classic não exporta as colunas percentuais de recuperação usadas pelo TAU Flex; não foi inventado um percentual de 100%. A evidência é o retorno normal, as mensagens sem aviso, as estatísticas dos 84 corpos e a ausência de arquivo de reparos gerado pelo solver.

Também foi identificado um problema de persistência de operações de malha em algumas cópias: a operação aparecia na sessão, mas não no arquivo salvo. O teste em um novo nome de projeto gravou a operação. A conferência do nativo impediu que os casos não persistidos fossem calculados. Nessa gravação, o contador `GeometryCore/DataVersion` mudou de 5 para 6; uma comparação normalizando **somente esse contador** confirmou o restante do bloco idêntico. Não se normalizaram dimensões ou dados geométricos.

A [documentação Ansys 2024 R2 sobre prioridade superficial](https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v242/en/Subsystems/HFSS/Content/HFSS/SurfaceRepresentationPriorityforTauMesheffectiveonlyforTauTolerantMesh.htm) descreve esse recurso para preservar detalhes críticos no TAU tolerante. A [documentação de TAU Flex](https://ansyshelp.ansys.com/public/views/secured/electronics/v261/en/subsystems/hfss/Content/Mesh/TAUFlexMeshing.htm) explica os avisos de recuperação e exige sua inspeção. A existência de uma malha rápida não demonstra, sozinha, a correção do modelo.

## Cálculo RF após a correção

O cálculo terminou em 10/11/2026, mantendo 5,17 GHz, quatro entradas de 0,25 W e 0°, 14 núcleos em todos os passes, máximo de seis passes, alvo ΔS de 0,05 e nenhum sweep. O processo foi fechado após exportar os dados. **Corrigir a demora de geração não qualificou a antena: os seis passes terminaram com ΔS=0,0670506.**

| Resultado da dobra b=20 mm / 60° | Valor |
|---|---:|
| Ganho frontal realizado total | 12,90535 dBi |
| Abertura H / V a −3 dB | 78,2344° / 7,5425° |
| Máximo H / V | −6,75° / −0,25° |
| Maior lóbulo secundário V no hemisfério frontal | −9,929 dB, em +13° |
| VSWR ativo R1_A / R1_B / R2_A / R2_B | 1,1687 / 1,1225 / 1,1968 / 1,1024 |
| VSWR máximo com as outras entradas casadas | 1,3021 |
| Tetraedros da última solução / passes | 299.868 / 6 |
| Reparos Major / Minor nos passes | 0 / 0 |

A matriz S é passiva (maior valor singular 0,16245); a potência aceita é 0,99506 W e a eficiência total é 82,52%. O balanço de potência difere em menos de 2×10⁻¹⁴ W e a recomposição dos campos individuais confere com a excitação conjunta. Porém, **o erro máximo de reciprocidade é 1,2723×10⁻⁵ e excede o limite de 1×10⁻⁵**. A auditoria mantém `fisica_ok=false`, `validado_numericamente=false` e `aprovado=false`. A fila parou em `REQUER_VERIFICACAO` por essa verificação numérica, não por falha do processo HFSS. As nove sondas de campo também não demonstraram estabilidade no limite configurado.

As metas de 13 dBi, H 99–121° e V 16,2–19,8° não foram atingidas simultaneamente. Não se deve interpretar esta solução preliminar como aprovação de fabricação ou prova do desempenho final. A referência plana também não convergiu em seis passes, portanto a comparação serve apenas para orientar o próximo estudo.

[Resultado completo](refletor_nativo_b20_60/resultado.json) · [Histórico dos passes](refletor_nativo_b20_60/historico_passes.json) · [Auditoria da malha inicial](refletor_nativo_b20_60/malha_inicial.json) · [Conferência geométrica](refletor_nativo_b20_60/conferencia_refletor_nativo.json) · [Diagramas H/V](refletor_nativo_b20_60/diagramas_HV.png).
