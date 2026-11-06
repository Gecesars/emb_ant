# Painel setorial P1H · 5,09 a 5,25 GHz

Projeto de uma coluna de antenas impressas com duas polarizações. A versão de dez elementos tem passo de 52,6 mm no eixo X. Duas entradas alimentam dois divisores 1:10 em uma PCB comum; cada saída chega à antena por um coaxial UT-141C de 254 mm. A referência de ganho é a potência incidente nas duas entradas externas: 0,5 W a 0° em cada uma.

| Para consultar | Arquivos |
|---|---|
| Modelos HFSS das duas montagens | [Uma placa](hfss/antenas/P1H_Continua.aedt) · [Dez placas](hfss/antenas/P1H_Separadas.aedt) · [Elemento de origem](hfss/antenas/P1H_AB_em_fase.aedt) |
| Modelos HFSS da alimentação | [Divisor de 22 portas](hfss/alimentacao/Divisor_2x10_PTFE.aedt) · [Transição soldada](hfss/alimentacao/Junta_UT141_P1H.aedt) |
| Fontes KiCad | [Coluna contínua](kicad/P1H_Coluna_10) · [Radiador individual](kicad/P1H_Individual) · [Divisor duplo](kicad/Divisor_2x10) |
| Referências dimensionais FreeCAD | [Uma placa](freecad/P1H_10_Continua.FCStd) · [Dez placas](freecad/P1H_10_Separadas.FCStd) · [Envelope do divisor](freecad/Divisor_2x10_PTFE.FCStd) |
| Mecânica do protótipo com refletor contínuo | [Montagem, chapa dobrada, planificação e desenho de fabricação](freecad/mecanica_R01/README.md) |
| Painel integrado R01 | [Modelo HFSS com duas portas N](hfss/antenas/P1H_R01.aedt) · [Premissas e reprodução](automacao/r01/README.md) · [Cotação da placa contínua e do divisor](resultados/r01/cotacao.md) |
| R02 com divisores inferior e superior | [Montagem, chapa e chicote](freecad/mecanica_R02/README.md) · [HFSS integrado](hfss/antenas/P1H_R02.aedt) · [Reprodução](automacao/r02/README.md) · [Cotação das três placas](resultados/r02/cotacao.md) |
| Controle R02-S com as dez placas individuais | [HFSS no mesmo refletor e rede R02](hfss/antenas/P1H_R02_10Separadas.aedt) · [Comparação dos divisores em 50 Ω](resultados/r02/rede/README.md) · [Relatório de engenharia e estado da qualificação](resultados/r02/Relatorio_P1H.pdf) |
| Fabricação | [Três pacotes Gerber com furação](fabricacao/gerbers) · [Ligação dos cabos](fabricacao/montagem/ligacao_dos_cabos.csv) · [Cotação JLCPCB](fabricacao/cotacao/Cotacao_JLCPCB.md) |
| Estudos anteriores | [Colunas de 8, 9 e 10 elementos](documentacao/historico/comparacao_colunas.md) · [Elemento com ambas as portas em fase](documentacao/historico/analise_AB.md) · [Dados numéricos](resultados/historico) |
| Como reproduzir | [Procedimento e convenções](automacao/README.md) |

**Critérios de RF:** abertura horizontal a −3 dB entre 81° e 99° (alvo 90°) e ganho realizado frontal ≥ 16 dBi em +Z. A abertura vertical pode ser menor que 7°. A comparação das duas revisões de PCB usa 17 frequências, de 5,09 a 5,25 GHz em passos de 10 MHz.

O ensaio anterior das duas revisões de PCB com refletores individuais foi interrompido após a convergência da placa contínua no centro da banda. O ganho mínimo de 16,58 dBi no [estudo histórico](documentacao/historico/comparacao_colunas.md) corresponde às antenas individuais antes dos ajustes dos pads e furos. A campanha autorizada da R01 usa a montagem contínua já desenhada, incluindo o refletor dobrado e os conectores N.

**Materiais e montagem:** os radiadores usam RO4350B de 0,76 mm (Dk de projeto 3,66). O divisor usa PTFE ZYF300CA-C de 1,52 mm. São espessuras do laminado. A placa longa mede 501,7125 × 28,3125 mm e a individual mede 28,3125 × 28,3125 mm. Os modelos RF anteriores usam dez refletores individuais de 48,3125 × 36 mm. O protótipo mecânico R01 usa um refletor contínuo dobrado de alumínio de 2 mm, apoios em poliacetal e conectores N com junta de vedação. A R01 tem geometria própria e requer qualificação de RF.

Os modelos HFSS nativos podem gerar a malha novamente. O Git guarda projetos, dados de engenharia e documentos; as malhas, os campos volumétricos, os backups e os arquivos temporários permanecem fora do repositório. Os Gerbers em **fabricacao/gerbers** correspondem ao orçamento, sem pedido de fabricação.
