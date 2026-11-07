# Painel setorial P1H · 5,09 a 5,25 GHz

**Resultado da campanha de 7 de novembro de 2026.** As duas montagens com divisores compactos reprovam o requisito conjunto de abertura horizontal e ganho em toda a banda. A 5,17 GHz, a placa contínua produziu **94,82° / 5,54° / 12,00 dBi** e as dez placas individuais **105,13° / 5,57° / 13,48 dBi**, respectivamente em H, V e ganho frontal realizado. A compacta teve a menor perda de distribuição entre as arquiteturas estudadas. [Comparação dos painéis](resultados/r02/comparacao_paineis.md) · [Relatório de engenharia](resultados/r02/Relatorio_P1H.pdf) · [Quatro materiais e divisores alongados](resultados/r03/README.md)

Projeto de uma coluna de dez antenas impressas com duas polarizações e passo de 52,6 mm no eixo X. A comparação atual usa duas PCBs distribuidoras, uma para os cinco radiadores inferiores e outra para os cinco superiores. Cada PCB atende às duas polarizações. A referência de ganho é a potência incidente nas duas entradas N, com 0,5 W a 0° em cada uma. Os modelos anteriores com divisor único e ramais de 254 mm também estão preservados.

| Para consultar | Arquivos |
|---|---|
| Modelos HFSS das duas montagens | [Uma placa](hfss/antenas/P1H_Continua.aedt) · [Dez placas](hfss/antenas/P1H_Separadas.aedt) · [Elemento de origem](hfss/antenas/P1H_AB_em_fase.aedt) |
| Modelos HFSS da alimentação | [Divisor de 22 portas](hfss/alimentacao/Divisor_2x10_PTFE.aedt) · [Transição soldada](hfss/alimentacao/Junta_UT141_P1H.aedt) |
| Fontes KiCad | [Coluna contínua](kicad/P1H_Coluna_10) · [Radiador individual](kicad/P1H_Individual) · [Divisor duplo](kicad/Divisor_2x10) |
| Referências dimensionais FreeCAD | [Uma placa](freecad/P1H_10_Continua.FCStd) · [Dez placas](freecad/P1H_10_Separadas.FCStd) · [Envelope do divisor](freecad/Divisor_2x10_PTFE.FCStd) |
| Mecânica do protótipo com refletor contínuo | [Montagem, chapa dobrada, planificação e desenho de fabricação](freecad/mecanica_R01/README.md) |
| Painel integrado R01 | [Modelo HFSS com duas portas N](hfss/antenas/P1H_R01.aedt) · [Premissas e reprodução](automacao/r01/README.md) · [Cotação da placa contínua e do divisor](resultados/r01/cotacao.md) |
| R02 com divisores inferior e superior | [Montagem, chapa e chicote](freecad/mecanica_R02/README.md) · [HFSS integrado](hfss/antenas/P1H_R02.aedt) · [Reprodução](automacao/r02/README.md) · [Cotação das três placas](resultados/r02/cotacao.md) |
| Controle R02-S com as dez placas individuais | [HFSS no mesmo refletor e rede R02](hfss/antenas/P1H_R02_10Separadas.aedt) · [Comparação convergida dos painéis](resultados/r02/comparacao_paineis.md) · [Comparação dos divisores em 50 Ω](resultados/r02/rede/README.md) · [Relatório de engenharia](resultados/r02/Relatorio_P1H.pdf) |
| R03 com saídas alinhadas e dois divisores alongados | [Comparação com a compacta e quatro laminados](resultados/r03/README.md) · [Montagem e chapa](freecad/mecanica_R03/README.md) · [HFSS do painel completo](hfss/antenas/P1H_R03_Alongada.aedt) · [Cotação](resultados/r03/cotacao.md) |
| Fabricação | [Pacotes Gerber com furação das revisões](fabricacao/gerbers) · [Ligação dos cabos da versão inicial](fabricacao/montagem/ligacao_dos_cabos.csv) · [Cotação JLCPCB inicial](fabricacao/cotacao/Cotacao_JLCPCB.md) |
| Estudos anteriores | [Colunas de 8, 9 e 10 elementos](documentacao/historico/comparacao_colunas.md) · [Elemento com ambas as portas em fase](documentacao/historico/analise_AB.md) · [Dados numéricos](resultados/historico) |
| Como reproduzir | [Procedimento e convenções](automacao/README.md) |

Os **critérios de RF** são abertura horizontal a −3 dB entre 81° e 99° (alvo 90°) e ganho realizado frontal ≥ 16 dBi em +Z. A abertura vertical pode ser menor que 7°. A banda é de 5,09 a 5,25 GHz. As redes compactas e os cupons de materiais foram calculados em 17 frequências, em passos de 10 MHz. Os painéis completos convergiram no centro e reprovaram nesse ponto, encerrando a avaliação de atendimento em toda a banda.

O ensaio anterior das duas revisões de PCB com refletores individuais foi interrompido após a convergência da placa contínua no centro da banda. O ganho mínimo de 16,58 dBi do estudo histórico corresponde às antenas individuais antes dos ajustes dos pads e furos. As campanhas R01, R02 e R02-S usam a mecânica completa, incluindo o refletor dobrado e os conectores N. [Estudo histórico](documentacao/historico/comparacao_colunas.md)

No painel completo R01, o ponto convergido de 5,17 GHz apresentou 14,06 dBi de ganho frontal e aberturas de 102,34° na horizontal e 6,19° na vertical. A R01 reprova as metas simultâneas de banda. [Campos, convergência e métricas](resultados/r01/README.md)

Os **radiadores** usam RO4350B de 0,76 mm (Dk de projeto 3,66). Os divisores de referência usam PTFE ZYF300CA-C de 1,52 mm. São espessuras do laminado. A placa longa mede 501,7125 × 28,3125 mm e a individual mede 28,3125 × 28,3125 mm. Os modelos RF anteriores usam dez refletores individuais de 48,3125 × 36 mm. Os protótipos mecânicos R01 a R03 usam refletor contínuo dobrado de alumínio de 2 mm, apoios em poliacetal e conectores N com junta de vedação. Os modelos nominais de cobre ainda excluem a camada de níquel-fósforo do acabamento ENIG cotado.

Os modelos HFSS nativos podem gerar a malha novamente. O Git guarda projetos, dados de engenharia e documentos. As malhas, os campos volumétricos, os backups e os arquivos temporários ficam nos diretórios locais de trabalho. Os Gerbers em **fabricacao/gerbers** correspondem aos protótipos cotados. A campanha documenta a reprovação das metas de RF e exige revisão antes da fabricação.
