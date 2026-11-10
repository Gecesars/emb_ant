# P2M21 — ajuste de casamento na banda R13

Melhor casamento de banda calculado nesta rodada: **c12_raiz_intermediaria**, pior VSWR ativo **1.23548** e casado **1.23260**, em Fast com conferencia discreta. Meta operacional A+B em fase <= 1.25: **Sim**. Condicao com outra entrada em 50 ohms <= 1.25: **Sim**. Pendencias dos criterios centrais: **apontamento_H**. O casamento calculado nao aprova essas pendencias e nao constitui prova de otimo global ou validacao experimental.

Meta atualizada pelo usuario em 9/11: **VSWR <= 1.25 em toda a banda**, nas duas entradas. A avaliacao operacional usa ambas em fase; a condicao com a outra entrada casada tambem e registrada. Os limites historicos da R12 permanecem nos respectivos documentos; a comparacao R13 usa a meta atual.

## Resultado selecionado

| Grandeza | Resultado |
|---|---|
| Maior VSWR ativo A/B na banda Fast | 1.23000 / 1.23547 |
| Maior VSWR com outra entrada casada A/B | 1.15496 / 1.23260 |
| Ganho frontal realizado total, 5,17 GHz | 12.4566 dBi |
| Aberturas H / V, 5,17 GHz | 72.055 / 15.183 graus |
| Maximos H / V, 5,17 GHz | +0.75 / -0.25 graus |
| Maior lobulo secundario V, 5,17 GHz | -10.075 dB |
| Adaptacao / DeltaS final | 6 passes / 1.672% |

O apontamento acima e o observado na grade de 0,25 grau, sem arredondar para zero. Em H, o ganho em zero esta 0.000923 dB abaixo do maximo, mas o limite de apontamento continua registrado separadamente. As larguras e a forma principal foram preservadas dentro dos limites de trabalho; o lobo secundario vertical foi reduzido em relacao a R12. A meta de casamento nao elimina a ressalva de apontamento. As curvas de VSWR abrangem a banda; ganho e diagramas foram calculados somente no centro.

[HFSS editavel](c12_raiz_intermediaria/P2M21_4_elementos.aedt) · [FreeCAD](c12_raiz_intermediaria/4_elementos.FCStd) · [Polares E/Emax em PDF](c12_raiz_intermediaria/polar_HV.pdf) · [Dimensoes dos transformadores](c12_raiz_intermediaria/transformadores_detalhe.png)

![Casamento na banda](c12_raiz_intermediaria/vswr_banda_detalhe.png)

![Diagramas polares selecionados](c12_raiz_intermediaria/polar_HV.png)

Conferencia adicional do pior ponto ativo Fast: **Discrete em 5.173 GHz**, VSWR ativo A/B **1.22904/1.23548**, casado **1.15400/1.21063**. Diferenca maxima de S para o Fast: 2.04339e-06. Solucao com 14 nucleos, sem novos passes ou campos fora do centro. O resumo considera o maior valor entre Fast, Discrete3 e esta conferencia.


## Condicoes

Quatro radiadores verticais, passo 48 mm, PCB de 70 x 184 mm e face inferior a 14,949 mm do refletor de aluminio de 90 x 200 x 2 mm. Duas entradas iguais, A=B=0,5 W/0 graus. Dois divisores impressos 1:4; RO4350B 0,76 mm, cobre 35 um e ENIG nominal. Dois cabos fisicos de 50 mm com perdas, sem conector N ou apoios plasticos. As dimensoes novas dos divisores sao iguais nas duas polarizacoes. Oito percursos geometricos de trilha iguais, 101,490832 mm cada, alem dos cabos.

Propriedades nominais preservadas da referencia: RO4350B com permissividade 3,66 e tangente de perdas 0,0037; PTFE dos cabos com 2,03636 e 0,000276831. O cobre impresso usa condutividade efetiva 28,6886 MS/m, incorporando a aproximacao Groiss para rugosidade de 0,5 um, avaliada em 5,25 GHz e mantida fixa na faixa. Sobre as faces expostas, a impedancia em camadas representa NiP de 4,5 um (1,5 MS/m) e ouro de 0,0254 um (41 MS/m), sem shell elements. O aluminio usa 20 MS/m. Sao hipoteses do modelo, nao propriedades medidas da placa fabricada; os nativos, `cad/enig_hfss.json` e `automacao/r05/enig_solido.py` preservam os valores e a implementacao.

Cada nova geometria usa HFSS sem GUI, 14 nucleos, maximo de seis passes, alvo DeltaS=0,05 e dois passes consecutivos. Malha Classic automatica, sem MeshLink ou refinamentos locais iniciais. O campo de segunda ordem da C02 e variantes que o herdam aumenta o numero de funcoes por tetraedro; nao acrescenta passes. A R12 historica, preservada, tem oito passes. DeltaS mede a mudanca entre solucoes; nao e uma garantia de erro fisico percentual.

O modelo equivalente MLine serviu somente para selecionar dimensoes. Reproduzir os dados usados na sua calibracao nao valida as previsoes. A primeira mudanca grande nos dois estagios nao se confirmou no HFSS e foi rejeitada. Os resultados abaixo sao extraidos das simulacoes completas, com acoplamento, rede impressa e cabos.

Como as correcoes idealizadas de linhas melhoraram mais o centro que as bordas, a selecao C10 passou a usar tambem secantes das matrizes S complexas e campos de tres ensaios HFSS (C07/C08/C09). Essa aproximacao afim cobre apenas duas direcoes geometricas amostradas e pode extrapolar; suas previsoes continuam identificadas como nao validadas. Somente a nova simulacao completa confirma o resultado. Larguras nominalmente fixas em 5 mm foram tratadas como fixas no seletor quando as diferencas numericas eram inferiores a 0,00001 mm, evitando restricoes artificiais; isso nao modifica os dados HFSS das fontes.

A C10 reduziu o pior VSWR ativo discreto para 1,297245, mas nao confirmou a previsao de 1,197945: continuou acima da meta em 5,25 GHz. O arquivo `c10_raiz_secantes/previsao_conferida.json` confronta as matrizes e os valores previstos com os efetivamente calculados. A busca seguinte ampliou a direcao geometrica, reduzindo tambem a largura da primeira secao. Estimativas de novos candidatos nunca substituem os resultados HFSS nas tabelas.

Na C11, reduzir a primeira largura melhorou as bordas, mas elevou o pior VSWR ativo central para 1,330511. A selecao C12 combina quatro respostas reais (C08/C09/C10/C11), agora com tres direcoes geometricas independentes, buscando equilibrar essas respostas. A generalizacao do seletor preservou numericamente a proposta anterior quando recebeu novamente suas tres fontes originais.

## Dimensoes dos transformadores

| Variante | Raiz largura mm | Raiz comprimento mm | Local largura mm | Local comprimento mm | Pos-raiz largura mm | Pos-local largura mm | Fator externo dipolos | BasisOrder |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| c01_rede_banda | 1.300000 | 5.688746 | 0.400000 | 15.206503 | 1.623415 | 1.623415 | 1.0000 | -1 |
| c02_raiz_ordem2 | 0.731795 | 6.826286 | 0.860433 | 8.816344 | 1.623415 | 1.623415 | 1.0000 | 2 |
| c03_dipolos_1012 | 0.656371 | 9.000142 | 0.860433 | 8.816344 | 1.623415 | 1.623415 | 1.0120 | 2 |
| c04_transformadores_duplos | 1.151326 | 5.029404 | 0.650000 | 14.216789 | 1.623415 | 1.623415 | 1.0000 | 2 |
| c05_segmentos_em_fase | 1.643274 | 5.396756 | 0.650000 | 14.262672 | 1.100000 | 2.300000 | 1.0000 | 2 |
| c07_raiz_transicoes | 5.000000 | 14.189724 | 0.860433 | 8.816344 | 1.623415 | 1.623415 | 1.0000 | 2 |
| c08_raiz_ajuste_fino | 4.999997 | 13.927663 | 0.860433 | 8.816344 | 1.623415 | 1.623415 | 1.0000 | 2 |
| c09_raiz_banda_fina | 5.000000 | 14.013546 | 0.860433 | 8.816344 | 1.623415 | 1.623415 | 1.0000 | 2 |
| c10_raiz_secantes | 5.000000 | 14.300029 | 0.860433 | 8.816344 | 1.623415 | 1.623415 | 1.0000 | 2 |
| c11_raiz_largura | 4.425655 | 12.811978 | 0.860433 | 8.816344 | 1.623415 | 1.623415 | 1.0000 | 2 |
| c12_raiz_intermediaria | 4.718845 | 13.470227 | 0.860433 | 8.816344 | 1.623415 | 1.623415 | 1.0000 | 2 |

Os segmentos posteriores usam a largura nominal de 50 ohms (1,623415 mm) quando nao modificados. Se a largura for ajustada, passam a integrar o casamento e nao devem ser descritos como linhas de 50 ohms. Os comprimentos geometricos totais continuam iguais; a confirmacao eletromagnetica inclui a mudanca de fase eletrica e as descontinuidades.

Secoes adicionais em serie na raiz, quando presentes, terminam antes da curva. Todas sao iguais nos ramos e polarizacoes, mantendo os divisores locais e os radiadores da fonte.
O parametro `root_flat_sections` usa juntas planas, com mudancas de largura nas cotas nominais. Os modelos historicos usam extremidades quadradas que se sobrepoem; o seletor novo considera suas fronteiras efetivas ao retirar a rede historica. Isso continua sendo uma aproximacao de circuito. A C06 foi interrompida antes de qualquer solve para corrigir essas transicoes; nao ha resultado RF dessa geometria.

| Variante | Secao na raiz | Largura mm | Comprimento mm |
|---|---:|---:|---:|
| c07_raiz_transicoes | 2 | 2.243383 | 12.100512 |
| c07_raiz_transicoes | 3 | 5.000000 | 6.937990 |
| c08_raiz_ajuste_fino | 2 | 1.832211 | 12.324633 |
| c08_raiz_ajuste_fino | 3 | 5.000000 | 7.084984 |
| c09_raiz_banda_fina | 2 | 1.797951 | 11.987595 |
| c09_raiz_banda_fina | 3 | 5.000000 | 6.903201 |
| c10_raiz_secantes | 2 | 2.150016 | 11.590639 |
| c10_raiz_secantes | 3 | 5.000000 | 6.665488 |
| c11_raiz_largura | 2 | 1.834854 | 13.373004 |
| c11_raiz_largura | 3 | 4.999999 | 7.175301 |
| c12_raiz_intermediaria | 2 | 1.863928 | 12.592316 |
| c12_raiz_intermediaria | 3 | 5.000000 | 6.993442 |

O fator externo opcional modifica apenas a distancia dos contornos dos dipolos alem de +/-4 mm do centro local, preservando a regiao central, as conexoes e vias. Nao e uma escala global da antena nem uma previsao de deslocamento da ressonancia. `alteracao_dipolos.json` registra as areas e a verificacao do nucleo preservado. Os recortes dos retornos acompanham os novos contornos para manter as folgas. As trilhas de sinal da C03 sao identicas as da R12.

## Ganho e diagramas somente em 5,17 GHz

| Caso | Passes | DeltaS | Convergiu | G0 dBi | VSWR ativo A/B | VSWR casado A/B | Maximos H/V graus | Aberturas H/V graus | SLL V dB |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| R12 referencia | 8 | 0.019770 | Sim | 12.7586 | 1.3648/1.2285 | 1.2091/1.1733 | +0.00/-1.25 | 73.322/15.058 | -9.095 |
| c01_rede_banda | 6 | 0.062538 | Nao | 12.9307 | 1.6226/1.7153 | 1.5014/1.6791 | +2.25/+0.25 | 66.955/15.361 | -9.496 |
| c02_raiz_ordem2 | 5 | 0.029992 | Sim | 12.6903 | 1.3553/1.3004 | 1.1926/1.2579 | +1.25/-1.00 | 73.310/15.099 | -9.137 |
| c03_dipolos_1012 | 6 | 0.019014 | Sim | 12.7113 | 1.3846/1.2480 | 1.2482/1.2057 | +0.75/-1.25 | 73.261/15.056 | -9.401 |
| c04_transformadores_duplos | 6 | 0.014700 | Sim | 12.9178 | 1.3330/1.3869 | 1.3517/1.5139 | +2.00/-0.50 | 70.072/15.100 | -9.459 |
| c05_segmentos_em_fase | 6 | 0.020746 | Sim | 12.6330 | 1.2869/1.3218 | 1.3075/1.4408 | +2.50/-0.25 | 71.692/15.204 | -8.446 |
| c07_raiz_transicoes | 5 | 0.014281 | Sim | 12.4188 | 1.4927/1.3537 | 1.4048/1.2857 | +0.75/-0.50 | 72.041/15.209 | -9.942 |
| c08_raiz_ajuste_fino | 6 | 0.011896 | Sim | 12.4688 | 1.1612/1.0564 | 1.1095/1.0492 | +0.25/-0.50 | 71.979/15.175 | -10.014 |
| c09_raiz_banda_fina | 6 | 0.011051 | Sim | 12.4378 | 1.0533/1.1562 | 1.0930/1.2166 | +0.75/-0.25 | 72.034/15.181 | -10.016 |
| c10_raiz_secantes | 6 | 0.017693 | Sim | 12.4695 | 1.1877/1.1143 | 1.0877/1.0648 | +0.75/-0.25 | 72.233/15.181 | -10.023 |
| c11_raiz_largura | 6 | 0.018414 | Sim | 12.4742 | 1.3305/1.2936 | 1.2018/1.1967 | +0.50/-0.50 | 72.268/15.089 | -10.236 |
| c12_raiz_intermediaria | 6 | 0.016719 | Sim | 12.4566 | 1.2273/1.2350 | 1.1548/1.2147 | +0.75/-0.25 | 72.055/15.183 | -10.075 |

Frente +Z, H=phi90 graus, V=phi0 graus, grade angular 0,25 grau. VSWR ativo considera as duas entradas simultaneamente; VSWR casado considera a outra entrada terminada em 50 ohms. Ganho realizado normalizado a 1 W incidente total. Valores de candidatos nao convergidos sao preliminares.

Para preservar os diagramas em relacao a R12, a triagem exige ganho frontal >=12 dBi, variacao da abertura <=5%, diferenca de forma no lobo principal alinhado <=0,75 dB, piora do maior lobulo secundario vertical <=0,5 dB e picos |H|<=0,5 grau e |V|<=1,5 grau. A comparacao de forma usa somente o lobo principal da referencia, delimitado pelos primeiros minimos, e os pontos acima de -10 dB. Esses limites de trabalho nao significam maximos exatamente em zero. Todos constam de `diagrama_comparado.json`. Quando apenas o apontamento reprova, uma varredura explicitamente diagnostica pode medir o VSWR sem aprovar o apontamento; o registro `fast_diagnostico.json` ou `triagem_diagnostica.json` conserva essa ressalva. Os demais limites nao sao dispensados.

Uma falha no auditor inicial fazia a mascara >=-10 dB incluir tambem o lobo secundario vertical da R12 entre 37 e 44,75 graus. Assim, reduzir esse lobo podia ser interpretado como deformacao do principal. A mascara foi corrigida para excluir secundarios; nenhum limite numerico mudou. O diagnostico anterior permanece em `diagrama_comparado_antes_correcao_mascara.json`, e `correcao_mascara_lobo_principal.json` registra valores, angulos e hashes. Na C08 de seis passes, o erro principal V correto e 0,398753 dB, em vez de 1,130560 dB calculado sobre os dois lobos. A verificacao do maior secundario continua independente; outros lobos podem mudar, conforme os graficos completos.

Uma triagem adicional de tres frequencias pode ser usada exclusivamente para calibrar o modelo de um candidato rejeitado, desde que a solucao esteja convergida e fisicamente consistente. Esse uso exige a marca `CALIBRACAO_DE_CANDIDATO_REJEITADO`; nao aprova a geometria nem libera a confirmacao Fast. Os limites de aceitacao dos diagramas permanecem os mesmos.

## Casamento entre 5,09 e 5,25 GHz

Referencia R12 Fast: pior VSWR ativo A=2,27960 e B=2,01420, ambos em 5,09 GHz. Triagem Discrete tem somente tres solucoes (5,09/5,17/5,25 GHz) e nao qualifica os intervalos. A confirmacao Fast produz 161 pontos de saida, com passo de 1 MHz, na malha adaptada em 5,17 GHz. Nao sao 161 adaptacoes independentes. Nenhum diagrama fora do centro foi solicitado ou calculado nesta etapa.

O Fast usa a solucao central para construir a resposta na faixa e conserva a malha adaptada. A conferencia com solucoes Discrete verifica a concordancia em frequencias selecionadas; nao substitui um estudo de tolerancias de fabricacao. [Metodo Fast na documentacao Ansys](https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v251/en/Subsystems/HFSS/Content/HFSS/FastFrequencySweeps.htm).

| Caso | Varredura/pontos | Condicao | VSWR minimo | VSWR maximo | Frequencia max GHz |
|---|---|---|---:|---:|---:|
| c02_raiz_ordem2 | Discrete 3 | ativo_A | 1.35535 | 1.61204 | 5.090 |
| c02_raiz_ordem2 | Discrete 3 | ativo_B | 1.30042 | 1.54648 | 5.250 |
| c02_raiz_ordem2 | Discrete 3 | casado_A | 1.19264 | 1.41154 | 5.250 |
| c02_raiz_ordem2 | Discrete 3 | casado_B | 1.09514 | 1.45282 | 5.250 |
| c03_dipolos_1012 | Discrete 3 | ativo_A | 1.21033 | 2.34224 | 5.090 |
| c03_dipolos_1012 | Discrete 3 | ativo_B | 1.24805 | 2.06981 | 5.090 |
| c03_dipolos_1012 | Discrete 3 | casado_A | 1.24817 | 1.76889 | 5.090 |
| c03_dipolos_1012 | Discrete 3 | casado_B | 1.20565 | 1.57599 | 5.090 |
| c04_transformadores_duplos | Discrete 3 | ativo_A | 1.30335 | 1.63320 | 5.250 |
| c04_transformadores_duplos | Discrete 3 | ativo_B | 1.17721 | 1.66054 | 5.250 |
| c04_transformadores_duplos | Discrete 3 | casado_A | 1.30715 | 1.47263 | 5.250 |
| c04_transformadores_duplos | Discrete 3 | casado_B | 1.34208 | 1.57898 | 5.250 |
| c07_raiz_transicoes | Discrete 3 | ativo_A | 1.40616 | 1.67146 | 5.090 |
| c07_raiz_transicoes | Discrete 3 | ativo_B | 1.35372 | 1.53266 | 5.090 |
| c07_raiz_transicoes | Discrete 3 | casado_A | 1.39363 | 1.53608 | 5.250 |
| c07_raiz_transicoes | Discrete 3 | casado_B | 1.28460 | 1.61814 | 5.250 |
| c08_raiz_ajuste_fino | Discrete 3 | ativo_A | 1.16118 | 1.41644 | 5.090 |
| c08_raiz_ajuste_fino | Discrete 3 | ativo_B | 1.05635 | 1.35433 | 5.250 |
| c08_raiz_ajuste_fino | Discrete 3 | casado_A | 1.10946 | 1.30979 | 5.250 |
| c08_raiz_ajuste_fino | Discrete 3 | casado_B | 1.04918 | 1.39647 | 5.250 |
| c09_raiz_banda_fina | Discrete 3 | ativo_A | 1.05328 | 1.38484 | 5.090 |
| c09_raiz_banda_fina | Discrete 3 | ativo_B | 1.15621 | 1.34192 | 5.250 |
| c09_raiz_banda_fina | Discrete 3 | casado_A | 1.09303 | 1.32121 | 5.090 |
| c09_raiz_banda_fina | Discrete 3 | casado_B | 1.21664 | 1.31555 | 5.250 |
| c10_raiz_secantes | Discrete 3 | ativo_A | 1.16687 | 1.24794 | 5.090 |
| c10_raiz_secantes | Discrete 3 | ativo_B | 1.11426 | 1.29724 | 5.250 |
| c10_raiz_secantes | Discrete 3 | casado_A | 1.06573 | 1.20442 | 5.250 |
| c10_raiz_secantes | Discrete 3 | casado_B | 1.06482 | 1.32676 | 5.250 |
| c11_raiz_largura | Discrete 3 | ativo_A | 1.05868 | 1.33051 | 5.170 |
| c11_raiz_largura | Discrete 3 | ativo_B | 1.04723 | 1.29362 | 5.170 |
| c11_raiz_largura | Discrete 3 | casado_A | 1.05759 | 1.20176 | 5.170 |
| c11_raiz_largura | Discrete 3 | casado_B | 1.10675 | 1.19669 | 5.170 |
| c12_raiz_intermediaria | Discrete 3 | ativo_A | 1.11370 | 1.22733 | 5.170 |
| c12_raiz_intermediaria | Discrete 3 | ativo_B | 1.08740 | 1.23503 | 5.170 |
| c12_raiz_intermediaria | Discrete 3 | casado_A | 1.06243 | 1.15478 | 5.170 |
| c12_raiz_intermediaria | Discrete 3 | casado_B | 1.18231 | 1.22967 | 5.090 |
| c12_raiz_intermediaria | Fast 161 | ativo_A | 1.05326 | 1.23000 | 5.178 |
| c12_raiz_intermediaria | Fast 161 | ativo_B | 1.04802 | 1.23547 | 5.173 |
| c12_raiz_intermediaria | Fast 161 | casado_A | 1.03776 | 1.15496 | 5.168 |
| c12_raiz_intermediaria | Fast 161 | casado_B | 1.13275 | 1.23260 | 5.142 |

## Auditorias

- **c01_rede_banda**: Major/Minor=0/0; passiva=True; reciprocidade=2.77e-06; recomposicao A+B=3.22e-15; potencia aceita=0.937124 W. Barreiras nao atendidas: convergencia, forma_H, abertura_H, apontamento_H.
- **c02_raiz_ordem2**: Major/Minor=0/0; passiva=True; reciprocidade=5.35e-07; recomposicao A+B=3.49e-15; potencia aceita=0.980092 W. Barreiras nao atendidas: apontamento_H.
- **c03_dipolos_1012**: Major/Minor=0/0; passiva=True; reciprocidade=6.59e-05; recomposicao A+B=3.17e-15; potencia aceita=0.980906 W. Barreiras nao atendidas: apontamento_H.
- **c04_transformadores_duplos**: Major/Minor=0/0; passiva=True; reciprocidade=7.33e-05; recomposicao A+B=3.41e-15; potencia aceita=0.976678 W. Barreiras nao atendidas: apontamento_H.
- **c05_segmentos_em_fase**: Major/Minor=0/0; passiva=True; reciprocidade=5.77e-05; recomposicao A+B=3.73e-15; potencia aceita=0.982525 W. Barreiras nao atendidas: SLL_vertical, apontamento_H.
- **c07_raiz_transicoes**: Major/Minor=0/0; passiva=True; reciprocidade=3.99e-07; recomposicao A+B=3.72e-15; potencia aceita=0.969172 W. Barreiras nao atendidas: apontamento_H.
- **c08_raiz_ajuste_fino**: Major/Minor=0/0; passiva=True; reciprocidade=5.14e-07; recomposicao A+B=5.39e-15; potencia aceita=0.996843 W. Barreiras nao atendidas: nenhuma.
  Confirmacao do quinto ao sexto passe total, sem reiniciar: historico dos cinco primeiros identico=True; variacao G=+0.068859 dB, H=-0.382774 grau, V=+0.007739 grau. O estado de cinco passes esta preservado em passe5/. A convergencia de DeltaS nao implica estabilidade exata dos campos.
- **c09_raiz_banda_fina**: Major/Minor=0/0; passiva=True; reciprocidade=2.73e-05; recomposicao A+B=3.45e-15; potencia aceita=0.997039 W. Barreiras nao atendidas: apontamento_H.
- **c10_raiz_secantes**: Major/Minor=0/0; passiva=True; reciprocidade=5.07e-07; recomposicao A+B=3.49e-15; potencia aceita=0.994858 W. Barreiras nao atendidas: apontamento_H.
- **c11_raiz_largura**: Major/Minor=0/0; passiva=True; reciprocidade=5.96e-07; recomposicao A+B=3.6e-15; potencia aceita=0.981750 W. Barreiras nao atendidas: nenhuma.
- **c12_raiz_intermediaria**: Major/Minor=0/0; passiva=True; reciprocidade=1.23e-07; recomposicao A+B=3.29e-15; potencia aceita=0.989263 W. Barreiras nao atendidas: apontamento_H.

## Imagens e curvas dos candidatos

### c01_rede_banda

Convergencia: False. Criterios dos diagramas: False.

![PCB](c01_rede_banda/layout.png)

![Comparacao dos diagramas](c01_rede_banda/comparacao_diagramas.png)

![Diagramas polares](c01_rede_banda/polar_HV.png)
### c02_raiz_ordem2

Convergencia: True. Criterios dos diagramas: False.

![PCB](c02_raiz_ordem2/layout.png)

![Comparacao dos diagramas](c02_raiz_ordem2/comparacao_diagramas.png)

![Diagramas polares](c02_raiz_ordem2/polar_HV.png)
![VSWR](c02_raiz_ordem2/vswr_triagem3.png)
### c03_dipolos_1012

Convergencia: True. Criterios dos diagramas: False.

![PCB](c03_dipolos_1012/layout.png)

![Comparacao dos diagramas](c03_dipolos_1012/comparacao_diagramas.png)

![Diagramas polares](c03_dipolos_1012/polar_HV.png)
![VSWR](c03_dipolos_1012/vswr_triagem3.png)
![Detalhe dos dipolos](c03_dipolos_1012/dipolos_detalhe.png)
### c04_transformadores_duplos

Convergencia: True. Criterios dos diagramas: False.

![PCB](c04_transformadores_duplos/layout.png)

![Comparacao dos diagramas](c04_transformadores_duplos/comparacao_diagramas.png)

![Diagramas polares](c04_transformadores_duplos/polar_HV.png)
![VSWR](c04_transformadores_duplos/vswr_triagem3.png)
![Dimensoes dos transformadores](c04_transformadores_duplos/transformadores_detalhe.png)
### c05_segmentos_em_fase

Convergencia: True. Criterios dos diagramas: False.

![PCB](c05_segmentos_em_fase/layout.png)

![Comparacao dos diagramas](c05_segmentos_em_fase/comparacao_diagramas.png)

![Diagramas polares](c05_segmentos_em_fase/polar_HV.png)
![Dimensoes dos transformadores](c05_segmentos_em_fase/transformadores_detalhe.png)
### c07_raiz_transicoes

Convergencia: True. Criterios dos diagramas: False.

![PCB](c07_raiz_transicoes/layout.png)

![Comparacao dos diagramas](c07_raiz_transicoes/comparacao_diagramas.png)

![Diagramas polares](c07_raiz_transicoes/polar_HV.png)
![VSWR](c07_raiz_transicoes/vswr_triagem3.png)
![Dimensoes dos transformadores](c07_raiz_transicoes/transformadores_detalhe.png)
### c08_raiz_ajuste_fino

Convergencia: True. Criterios dos diagramas: True.

![PCB](c08_raiz_ajuste_fino/layout.png)

![Comparacao dos diagramas](c08_raiz_ajuste_fino/comparacao_diagramas.png)

![Diagramas polares](c08_raiz_ajuste_fino/polar_HV.png)
![VSWR](c08_raiz_ajuste_fino/vswr_triagem3.png)
![Dimensoes dos transformadores](c08_raiz_ajuste_fino/transformadores_detalhe.png)
### c09_raiz_banda_fina

Convergencia: True. Criterios dos diagramas: False.

![PCB](c09_raiz_banda_fina/layout.png)

![Comparacao dos diagramas](c09_raiz_banda_fina/comparacao_diagramas.png)

![Diagramas polares](c09_raiz_banda_fina/polar_HV.png)
![VSWR](c09_raiz_banda_fina/vswr_triagem3.png)
![Dimensoes dos transformadores](c09_raiz_banda_fina/transformadores_detalhe.png)
### c10_raiz_secantes

Convergencia: True. Criterios dos diagramas: False.

![PCB](c10_raiz_secantes/layout.png)

![Comparacao dos diagramas](c10_raiz_secantes/comparacao_diagramas.png)

![Diagramas polares](c10_raiz_secantes/polar_HV.png)
![VSWR](c10_raiz_secantes/vswr_triagem3.png)
![Dimensoes dos transformadores](c10_raiz_secantes/transformadores_detalhe.png)
### c11_raiz_largura

Convergencia: True. Criterios dos diagramas: True.

![PCB](c11_raiz_largura/layout.png)

![Comparacao dos diagramas](c11_raiz_largura/comparacao_diagramas.png)

![Diagramas polares](c11_raiz_largura/polar_HV.png)
![VSWR](c11_raiz_largura/vswr_triagem3.png)
![Dimensoes dos transformadores](c11_raiz_largura/transformadores_detalhe.png)
### c12_raiz_intermediaria

Convergencia: True. Criterios dos diagramas: False.

![PCB](c12_raiz_intermediaria/layout.png)

![Comparacao dos diagramas](c12_raiz_intermediaria/comparacao_diagramas.png)

![Diagramas polares](c12_raiz_intermediaria/polar_HV.png)
![VSWR](c12_raiz_intermediaria/vswr_triagem3.png)
![VSWR](c12_raiz_intermediaria/vswr_banda.png)
![VSWR](c12_raiz_intermediaria/vswr_banda_detalhe.png)
![Dimensoes dos transformadores](c12_raiz_intermediaria/transformadores_detalhe.png)

Os nativos HFSS/FreeCAD, dados S2P, cortes distantes, configuracoes e evidencias acompanham o pacote. No FreeCAD, os corpos sao solidos Part::Feature; as dimensoes sao reproduzidas pelos scripts e JSON, sem arvore nativa de esbocos restringidos. Malhas, `.aedtresults`, campos volumetricos, locks e temporarios ficam somente no estudo local. Reabrir o nativo sem os resultados permite editar o projeto; recuperar os campos FEM em outra maquina exige novo solve. A geometria e os resultados historicos R12 foram preservados. Este estudo nao qualifica o painel 16x2 ou desempenho MIMO por entrada.
