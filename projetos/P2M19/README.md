# P2M19 — duas colunas, objetivo de 19 dBi

**Orientação atualizada após a R01 (13/11): abertura horizontal próxima de 30° também é aceitável.** A meta de ganho permanece 19 dBi. O usuário não definiu uma tolerância numérica para essa abertura. A rodada abaixo conserva a geometria de 88 mm solicitada e seus resultados originais.

Para uma próxima comparação, 72 mm entre colunas permite manter 2 mm de folga entre as PCBs de 70 mm e buscar abertura maior com lóbulos laterais menores. A referência histórica R15 apresentou H 24,35°, mas não estava convergida e incluía cabos de 50 mm e outro refletor. Portanto não garante 30° nem o ganho da P2M19. Esse novo espaçamento ainda não foi simulado nesta versão.

[Simulação R01 de 16 níveis × duas colunas a 88 mm](centro_16x2_88mm/README.md): criada e executada em 13/11/2026, em 5,17 GHz, sem sweep, 14 núcleos, seis passes máximos e ΔS alvo 0,05.

**Resultado preliminar, não convergido:** ganho frontal total 19,055 dBi, H 19,428° e V 3,820°; ΔS final 0,177100. As 16 entradas recebem 0,0625 W a 0°, total 1 W. Ganho não qualifica cada entrada MIMO independentemente nem inclui uma rede externa de distribuição.

A largura H é a do lóbulo principal. O lóbulo em −37° está apenas 2,829 dB abaixo do pico; o estudo não demonstra um feixe único de aproximadamente 20°. O balanço de potência é consistente, mas a variação do ganho frontal entre os dois últimos passes ainda foi 0,819 dB. Não houve continuação além de seis passes.

- [Projeto HFSS](centro_16x2_88mm/P2M19_16x2_88mm.aedt)
- [Geometria CAD utilizada](centro_16x2_88mm/P2M19_16x2_88mm.FCStd)
- [Diagramas polares E/Emax](centro_16x2_88mm/polar_HV.png)
- [Auditoria completa](centro_16x2_88mm/resultado.json)
- [Scripts de criação, execução e análise](automacao)
- [Estimativa anterior à simulação](estimativa_inicial/README.md), preservada como histórico e sem valor de validação.

As placas C12, o passo vertical de 48 mm e a altura de 14,949 mm foram preservados. Refletor de 178 × 776 × 2 mm. Divisores impressos e perdas dos materiais incluídos; sem cabos em 3D, rede externa 1:8, conectores N, radome ou suportes plásticos. Trabalho local e malhas: `D:/dev/EMBRAER/P2M19/R01_16x2_88mm`; o repositório recebe somente nativos e evidências compactas.
