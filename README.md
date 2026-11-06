# Painel setorial P1H · 5,09 a 5,25 GHz

Projeto de uma coluna de antenas impressas com duas polarizações. A versão de dez elementos tem passo de 52,6 mm no eixo X. Duas entradas alimentam dois divisores 1:10 em uma PCB comum; cada saída chega à antena por um coaxial UT-141C de 254 mm. A referência de ganho é a potência incidente nas duas entradas externas: 0,5 W a 0° em cada uma.

| Para consultar | Arquivos |
|---|---|
| Modelos HFSS das duas montagens | [Uma placa](hfss/antenas/P1H_Continua.aedt) · [Dez placas](hfss/antenas/P1H_Separadas.aedt) · [Elemento de origem](hfss/antenas/P1H_AB_em_fase.aedt) |
| Modelos HFSS da alimentação | [Divisor de 22 portas](hfss/alimentacao/Divisor_2x10_PTFE.aedt) · [Transição soldada](hfss/alimentacao/Junta_UT141_P1H.aedt) |
| Fontes KiCad | [Coluna contínua](kicad/P1H_Coluna_10) · [Radiador individual](kicad/P1H_Individual) · [Divisor duplo](kicad/Divisor_2x10) |
| Referências dimensionais FreeCAD | [Uma placa](freecad/P1H_10_Continua.FCStd) · [Dez placas](freecad/P1H_10_Separadas.FCStd) · [Envelope do divisor](freecad/Divisor_2x10_PTFE.FCStd) |
| Fabricação | [Três pacotes Gerber com furação](fabricacao/gerbers) · [Ligação dos cabos](fabricacao/montagem/ligacao_dos_cabos.csv) · [Cotação JLCPCB](fabricacao/cotacao/Cotacao_JLCPCB.md) |
| Estudos anteriores | [Colunas de 8, 9 e 10 elementos](documentacao/historico/comparacao_colunas.md) · [Elemento com ambas as portas em fase](documentacao/historico/analise_AB.md) · [Dados numéricos](resultados/historico) |
| Como reproduzir | [Procedimento e convenções](automacao/README.md) |

**Critérios de RF:** abertura horizontal a −3 dB entre 81° e 99° (alvo 90°) e ganho realizado frontal ≥ 16 dBi em +Z. A abertura vertical pode ser menor que 7°. A comparação das duas revisões de PCB usa 17 frequências, de 5,09 a 5,25 GHz em passos de 10 MHz.

**Estado da revisão de PCB:** os modelos dos dois painéis e a geometria de fabricação estão disponíveis. A verificação com pads e furos do KiCad está em processamento. O ganho mínimo de 16,58 dBi no [estudo anterior](documentacao/historico/comparacao_colunas.md) corresponde às antenas individuais antes desses ajustes.

**Materiais e montagem:** os radiadores usam RO4350B de 0,76 mm (Dk de projeto 3,66). O divisor usa PTFE ZYF300CA-C de 1,52 mm. São espessuras do laminado. A placa longa mede 501,7125 × 28,3125 mm; a individual, 28,3125 × 28,3125 mm. Os dois arranjos usam dez refletores individuais de 48,3125 × 36 mm. Os arquivos FreeCAD representam a geometria nominal; o posicionamento do divisor, o trajeto externo dos cabos, o radome e as ferragens de instalação não estão especificados.

Os modelos HFSS nativos podem gerar a malha novamente. O Git guarda projetos, dados de engenharia e documentos; as malhas, os campos volumétricos, os backups e os arquivos temporários permanecem fora do repositório. Os Gerbers em **fabricacao/gerbers** correspondem ao orçamento, sem pedido de fabricação.
