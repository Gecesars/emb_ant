# P2M19 — 16 níveis, duas colunas, objetivo de 19 dBi

**P2M19 R06 — convergência de ΔS confirmada em 14/11.** Executados somente os passes **9 e 10**, preservando os oito anteriores, colunas de 72 mm e refletor de 146 mm. 14 núcleos, 5,17 GHz, 16 entradas de 0,0625 W / 0°, sem sweep. ΔS **0,021617 / 0,024510**, dois passes consecutivos abaixo de 0,05. Ganho frontal total **20,391 dBi**, H/V **22,761° / 3,768°**, VSWR ativo **1,054–1,221** e máximo com demais entradas casadas **1,294**. Balanço de potência consistente e zero reparos Major/Minor. **A estabilidade completa dos campos ainda não foi confirmada**: ganho frontal variou +0,122 dB no último passe; maior variação entre as nove sondas foi 0,463 dB. Nenhum passe além de dez foi executado. [Resultados, HFSS e diagramas atualizados](continuacao_72mm_ref146_10passes/README.md).

**P2M19 R05 — dois passes adicionais concluídos em 13/11, PRELIMINAR.** Preservados a geometria de colunas a 72 mm, refletor 146 mm e os seis passes anteriores; executados somente os passes 7/8, com 14 núcleos, 5,17 GHz, 16 entradas iguais/em fase, sem sweep. Resultado: **20,101 dBi**, H **22,734°**, V **3,753°**, VSWR ativo **1,143–1,353**. **ΔS=0,05196469 >0,05: não convergiu.** Balanço de potência consistente, zero reparos Major/Minor; ganho ainda variou +0,241 dB no último passe. O acompanhamento desta execução está concluído, sem novos passes programados. [Relatório e arquivos da continuação](continuacao_72mm_ref146_8passes/README.md).

A comparação de seis passes abaixo permanece preservada como histórico.

**Comparação de 13/11/2026 concluída como estudo preliminar. Nenhuma geometria convergiu em seis passes ao alvo ΔS≤0,05.** Todos os ganhos abaixo superam 19 dBi numericamente; ainda não validam essa meta. A abertura próxima de 30° continua como orientação, sem tolerância numérica inventada.

Oito placas C12 de quatro radiadores, 32 radiadores e 16 entradas de **0,0625 W / 0°**, total 1 W. Simulações efetivas em **5,17 GHz**, com **14 núcleos**, até **seis passes por geometria**, sem sweep. Passo vertical de 48 mm, PCBs a 14,949 mm da face do refletor e espessura de alumínio de 2 mm.

| Caso | Colunas / largura do refletor | G frontal total | H / V | Maior lóbulo H / V | ΔS final |
|---|---:|---:|---:|---:|---:|
| R01, referência | 88 / 178 mm | 19,055 dBi | 19,428° / 3,820° | −2,829 / −6,082 dB | 0,177100 |
| R02, comparação direta | 72 / 178 mm | 19,209 dBi | 24,238° / 3,752° | −4,866 / −5,775 dB | 0,156138 |
| R03, ajuste do refletor | 72 / 162 mm | 19,418 dBi | 23,989° / 3,765° | −5,261 / −5,957 dB | 0,116891 |
| R04, ajuste do refletor | 72 / 146 mm | 19,500 dBi | 23,550° / 3,693° | −5,447 / −6,240 dB | 0,139600 |

H/V são larguras de meia potência do lóbulo principal. Os lóbulos secundários são medidos no hemisfério frontal, em relação ao pico de cada corte. A alteração de 88 para 72 mm alargou numericamente H e reduziu os lóbulos horizontais; a vertical permaneceu estreita. Os ajustes de largura do refletor não levaram H a 30°.

**A diferença de ganho entre geometrias é menor que sua variação no último passe.** Portanto não foi escolhida uma geometria como validada. O ganho frontal ainda variou de 0,782 a 0,880 dB no último passe dos novos casos. Os balanços de potência, passividade, reciprocidade, recomposição das fontes e uso de 14 núcleos foram conferidos; não houve reparos Major/Minor. Essas verificações não substituem convergência.

Inclui acoplamento, divisores impressos e perdas nominais de RO4350B, cobre e ENIG. Sem rede externa, cabos em 3D, conectores N, radome ou suportes plásticos. O ganho é total coerente e não qualifica cada entrada MIMO independentemente.

- [Relatório comparativo completo](estudo_72mm/README.md)
- [Diagramas H/V sobrepostos](estudo_72mm/comparacao_HV.png)
- [Diagramas polares E/Emax](estudo_72mm/comparacao_polar_HV.png)
- [R02: nativos HFSS/FreeCAD, S16 e auditoria](estudo_72mm/casos/R02_16x2_72mm/README.md)
- [R03: refletor de 162 mm](estudo_72mm/casos/R03_72mm_ref162/README.md)
- [R04: refletor de 146 mm](estudo_72mm/casos/R04_72mm_ref146/README.md)
- [Referência R01 de 88 mm preservada](centro_16x2_88mm/README.md)
- [Operação e limites da fila local](automacao/README.md)

A fila local finita acompanhou a R02 e executou automaticamente R03/R04 em sequência; está encerrada. Não foi criado agendamento recorrente do Codex. Uma falha de leitura do código de saída do pós-processamento foi reproduzida e corrigida; os cálculos HFSS não foram repetidos. Evidências em [recuperação do controlador](estudo_72mm/casos/R02_16x2_72mm/evidencias/recuperacao_pipeline.json).

Nativos e evidências compactas foram preservados; malhas, `.aedtresults`, campos volumétricos e locks permanecem fora do Git. Trabalho local em `D:/dev/EMBRAER/P2M19`; manifesto do pacote em [manifesto.json](estudo_72mm/manifesto.json).
