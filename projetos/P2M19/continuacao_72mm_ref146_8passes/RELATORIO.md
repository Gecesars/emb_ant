# P2M19 — continuação da malha: colunas 72 mm, refletor 146 mm

**PRELIMINAR — NAO CONVERGIDO.** Executados exatamente os passes **7 e 8**, preservando os seis anteriores. ΔS final **0.05196469**, alvo **0,05**; passes consecutivos atendidos: 0.

5,17 GHz, 14 núcleos, sem sweep. Oito placas C12, 16 níveis × duas colunas, 32 radiadores, 16 entradas iguais de 0,0625 W / 0°, total 1 W. Mesma geometria, materiais, fronteiras, portas, definições de malha e nove monitores de campo; alterados somente os limites mínimo/máximo para oito passes.

| Resultado | 6 passes | 8 passes |
|---|---:|---:|
| Ganho frontal realizado total (dBi) | 19.500282 | 20.100983 |
| Abertura horizontal (°) | 23.549832 | 22.734187 |
| Abertura vertical (°) | 3.693246 | 3.753405 |
| Máximo H (°) | 0.373646 | 0.409364 |
| Máximo V (°) | 0.077628 | 0.042310 |
| VSWR ativo mínimo | 1.207618 | 1.143031 |
| VSWR ativo máximo | 1.655145 | 1.352969 |
| VSWR máximo com demais entradas casadas | 1.497627 | 1.323147 |
| Maior lóbulo secundário H (dB) | -5.446880 | -5.076796 |
| Maior lóbulo secundário V (dB) | -6.239981 | -6.804629 |
| ΔS | 0.139600 | 0.051965 |

Potências: incidente 1.000000 W, refletida 0.013565 W, aceita 0.986435 W, radiada 0.780141 W e dissipada 0.206294 W. [VSWR individual das 16 entradas](vswr_por_porta.csv).

A variação de ganho entre seis e oito passes foi +0.600701 dB. A meta numérica de 19 dBi é atendida. Convergência S: False; estabilidade das nove sondas (0,1 dB em dois passes): False; validação numérica conjunta: False. Resultado não convergido não é aprovação, mesmo quando supera 19 dBi.

As aberturas são de meia potência do lóbulo principal. Picos refinados em grade de 0,05° com interpolação parabólica local; lóbulos secundários avaliados no hemisfério frontal, em relação ao pico de cada corte. O zero corresponde à normal frontal do refletor.

Balanço de potência válido: True; reparos Major/Minor: 0/0. Maior valor singular da matriz S: 0.26355854; erro de reciprocidade 3.415e-11; recomposição dos campos 3.965e-15.

Inclui acoplamento e perdas dos divisores impressos, RO4350B de núcleo 0,76 mm, cobre 35 µm e ENIG nominal. Refletor 146 × 776 × 2 mm, passo vertical 48 mm e altura de PCB 14,949 mm. Exclui rede externa de distribuição, cabos em 3D, conectores N, radome e apoios plásticos. É ganho total coerente, não qualificação por entrada MIMO. Nenhuma banda foi simulada nesta etapa.

![Diagramas polares E/Emax](polar_HV.png)

![Comparação dos diagramas](comparacao_diagramas.png)

![Casamento das 16 entradas](acoplamento_vswr.png)

![Histórico de adaptação](historico_convergencia.png)

## Histórico

| Passe | Tetraedros | ΔS | G frontal (dBi) |
|---:|---:|---:|---:|
| 1 | 268534 | — | 6.079411 |
| 2 | 315805 | 0.46880860 | 13.579744 |
| 3 | 371134 | 0.49768489 | 16.589591 |
| 4 | 435972 | 0.22326489 | 17.865506 |
| 5 | 512299 | 0.19307471 | 18.619939 |
| 6 | 602282 | 0.13960010 | 19.500282 |
| 7 | 708350 | 0.08591476 | 19.859973 |
| 8 | 834197 | 0.05196469 | 20.100983 |

[HFSS](P2M19_R04_72mm_ref146.aedt) · [FreeCAD EM](P2M19_R04_72mm_ref146.FCStd) · [S16](centro.s16p) · [Resultados detalhados](resultado.json) · [Prova da continuidade](evidencias/continuidade_final.json).

O basename e o design HFSS conservam o nome R04 para reconhecer a malha copiada; a pasta e a configuração identificam a continuação R05. O original R04 permanece intacto. Malhas e campos nativos restauráveis ficam apenas na pasta local de trabalho; o Git contém nativo, campos distantes e evidências, sem `.aedtresults`, malhas, campos volumétricos ou locks.

Acompanhamento desta execução encerrado após os oito passes e a revisão. Não há novos passes, sweep, otimização geométrica ou agendamento recorrente ativos.
