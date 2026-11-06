# Comparação dos divisores e cabos em cargas de 50 Ω

Com 0,5 W a 0° em cada entrada, o chicote R02 entregou **0,8225 W** às 20 cargas no centro da banda. O chicote de divisor único R01 entregou **0,7599 W** nas mesmas condições. A vantagem da R02 foi de 0,344 dB a 5,17 GHz e de 0,153 a 0,440 dB nos 17 pontos. No centro, a potência devolvida aos dois geradores caiu de 0,0876 para 0,0296 W. O encurtamento de 26,85 mm do comprimento de coaxial em cada percurso explica aproximadamente 0,025 dB de atenuação de ida. A mudança da rede, do casamento e das reflexões múltiplas explica o restante da diferença no ensaio.

| Indicador | R01 em 5,17 GHz | R02 em 5,17 GHz | R02, 5,09–5,25 GHz |
|---|---:|---:|---:|
| Perda excedente do conjunto de 20 saídas | 1,192 dB | 0,849 dB | 0,726 a 1,076 dB |
| Potência entregue às cargas | 75,99% | 82,25% | 78,06% a 84,61% |
| Dispersão de amplitude entre saídas, pico a pico | 0,149 dB | 0,089 dB | 0,086 a 0,089 dB |
| Dispersão de fase entre saídas, pico a pico | 1,050° | 0,528° | 0,466° a 0,543° |
| Fase média superior menos inferior | −0,012° | +0,072° | +0,051° a +0,075° |

As matrizes dos divisores são FEM de onda completa do HFSS, com microstrip, dielétrico, lançamentos e solda. Para a R02, o primeiro estágio de seis portas convergiu em sete passes, último ΔS = 0,009379, e o estágio de grupo de 12 portas em nove, último ΔS = 0,007095. Cada matriz foi calculada em 17 frequências discretas. Um circuito linear fecha os quatro enlaces e as vinte saídas com a fase e a atenuação do UT-141C. As duas polarizações e as reflexões entre os estágios entram pelo conjunto das matrizes complexas. O segundo cálculo, montado com o objeto Circuit do scikit-rf, reproduziu a matriz resultante de 22 portas com erro máximo de 7,1 × 10⁻¹⁵.

O plano de entrada deste ensaio fica na extremidade coaxial traseira do N e o de saída nos vinte terminais coaxiais junto aos radiadores, terminados em 50 Ω. A perda excedente usa a soma da potência nas vinte cargas. Os corpos dos N, as bobinas, a interação eletromagnética pelo chassi e pela ponte física da PCB inferior, as terminações dos radiadores e as cargas reais acopladas são tratados no [modelo integrado da R02](../../../hfss/antenas/P1H_R02.aedt). A aplicação num painel irradiando exige os campos desse modelo para determinar ganho e abertura.

[Resultados por frequência](rede_cargas_50ohm.csv) · [Matriz R01 de 22 portas](R01_2x10.s22p) · [Matriz R02 1:2](R02_1x2.s6p) · [Matriz R02 1:5](R02_1x5.s12p) · [Convergência do 1:2](convergencia_1x2.txt) · [Convergência do 1:5](convergencia_1x5.txt)
