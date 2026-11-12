# R17 — efeito das abas laterais no tubo DN100

Comparação central concluída em12/11/2026, **preliminar**. A placa radiante e o divisor C02 são os mesmos da R16. Substituiu-se apenas o refletor dobrado por uma chapa plana de296×90×2mm, preservando seis furos e todas as demais geometrias. O novo S6 e os campos foram simulados no HFSS; o S8 C02 foi reutilizado com hashes conferidos. Cabos de saída somente RLGC no circuito, seis ramais físicos134mm, com perdas nominais. Nenhum cabo longo em3D.

| 5,17 GHz; A/B0,5 W /0° | Abas150° R16 | Plano90 R17 |
|---|---:|---:|
| Ganho frontal realizado total |14,319757 dBi|14,305150 dBi|
| Abertura H |78,985725°|78,773564°|
| Abertura V |10,050446°|10,106209°|
| VSWR ativo A/B |1,098677 /1,086897|1,124065 /1,056959|
| VSWR outra entrada50Ω A/B |1,090432 /1,103778|1,129042 /1,094662|
| Pico H |−0,75°|−1,00°|
| H(0) abaixo do pico |0,001268 dB|0,001474 dB|
| Pico V interpolado |+0,046330°|−0,071002°|
| Assimetria principal V |0,039131 dB|0,219441 dB|
| Maior secundário V |−7,073426 dB|−6,479861 dB|
| ΔS final da antena /passes |0,041601 /6|0,030507 /6|
| Passes consecutivos abaixo de0,05 |1|1|

**Decisão:** as abas têm influência pequena no H observado; a remoção não está demonstrada como equivalente sob todos os critérios. Mantida a chapa dobrada no CAD principal pelo vertical mais simétrico do caso anterior. O lóbulo secundário vertical da plana ficou0,594dB maior. Diferenças pequenas de ganho/H não devem ser interpretadas como melhoria comprovada, pois os campos ainda variaram.

## Convergência e consistência

R17: máximo6passes,14núcleos em cada passe,5,17GHz,sem sweep,Classic com elementos curvilíneos e solver direto. HistóricoΔS: passe2=0,621237;3=0,125628;4=0,094107;5=0,056507;6=0,030507. São463828tetraedros no passe final. Apenas um passe atendeΔS0,05; **não convergiu conforme os dois consecutivos configurados**. A maior variação final dos nove campos foi0,815299dB. R16 também não completou os dois passes e apresentou0,351395dB no último monitoramento de campo.

Zero reparosMajor/Minor na nova antena; sem avisos de falha do solver. Matriz S6 passiva/recíproca, recomposição uniforme e balanço de potência aprovados. O Nexxim foi efetivamente resolvido; diferença máxima da matriz frente ao cálculo independente **7,34475e−16**. Consistência numérica não equivale a convergência de malha.

## Arquivos

- [HFSS plano](plano90/antena/PCB_Plano90.aedt), [S6](plano90/antena/centro.s6p), [auditoria](plano90/antena/auditoria_em.json).
- [Resultado do circuito](plano90/circuito/resultado.json), [Nexxim nativo](plano90/circuito/C09_PVC_Nexxim.aedt), [arquivo com componentes externos sem malhas](plano90/circuito/C09_PVC_Nexxim_sem_malhas.aedtz).
- [Diagramas polares](plano90/circuito/polar_HV.png), [comparativo ilustrado](../mecanica_R17/documentacao/Relatorio_R17_PRELIMINAR.pdf).
- Referência congelada R16 em `referencia_dobrada_R16`; os nativos completos permanecem em `../tubo_pvc/`.

O tubo comercial continua não caracterizado eletricamente; εr2,68/tanδ0,008 são uma hipótese a5,17GHz. Nesta comparação o tubo está aberto nas extremidades. Não foram incluídos novos flanges, linguetas, grampos, N ou cabos de entrada da montagem R17, nem acoplamento espacial entre divisor e antena. Não é validação RF do fechamento completo.

Os nativos estão sem `.aedtresults`, malhas, campos volumétricos ou locks. Scripts em `../automacao/r17_*.py` e `r17_pipeline.ps1`. Não executar a fila novamente sobre esta solução: ela contém guardas contra duplicação.
