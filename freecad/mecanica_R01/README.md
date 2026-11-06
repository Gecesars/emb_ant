# P1H · refletor e montagem mecânica R01

A R01 monta a PCB contínua de dez radiadores e o divisor duplo em uma chapa de alumínio de 2 mm. A base e as nervuras fazem parte da mesma peça. A coluna fica na frente; o divisor, as conexões e o chicote ficam atrás. A base recebe dois conectores N voltados para baixo quando a coluna está na vertical.

| Para fazer | Arquivo |
|---|---|
| Inspecionar a montagem por grupos e ocultar componentes | [Montagem FreeCAD](03_Antena_montada.FCStd) · [Vista frontal](07_Frente.png) · [Vista traseira](07_Verso.png) |
| Abrir a chapa conformada | [FreeCAD dobrado](01_Refletor_dobrado.FCStd) · [STEP do refletor](01_Refletor_dobrado.step) |
| Inspecionar o desenvolvimento | [FreeCAD planificado](02_Refletor_planificado.FCStd) |
| Cortar o protótipo | [DXF 1:1 em mm, somente corte](04_Refletor_CORTE_1a1.dxf) |
| Posicionar e executar as dobras | [DXF de marcação com camada EIXOS_DOBRA](05_Refletor_marcacao_dobras.dxf) · [Quatro pranchas cotadas](06_Desenho_de_fabricacao.pdf) |
| Usinar os suportes e produzir o passa-cabos | [Cinco modelos STEP](componentes/) |
| Formar o chicote | [Gabarito 3D dos trechos e dobras](08_Gabarito_dos_cabos.csv) · [Mapa de portas do divisor](../../fabricacao/montagem/ligacao_dos_cabos.csv) |

## Chapa e suportes

O modelo usa alumínio 5052-H32, raio interno de 2,00 mm e fator K de 0,40. O desenvolvimento nominal de 585,398 × 82,00 mm inclui os alívios de canto e as interrupções nas nervuras para passagem do divisor. A chapa dobrada ocupa 533 × 82 × 56 mm. A largura plana da face ativa é 36 mm e chega a 44 mm nas nervuras. A oficina deve conferir o desenvolvimento em um corpo de prova de 2 mm com a ferramenta de produção. Aplicar a compensação de corte no CAM.

Cinco berços recortados em POM-C de **5 mm de espessura** sustentam a face inferior da PCB a **16,61 mm do alumínio**. O canal de 1,01 mm retém a PCB de núcleo 0,76 mm. Conferir a espessura acabada nas bordas antes de usinar a série. Dois batentes longitudinais deixam 0,54 mm de folga nominal em cada ponta. Os roscados M2,5 são feitos no POM. Instalar os berços na PCB antes de aparafusá-los ao refletor. A PCB preserva os furos originais.

Dois trilhos traseiros espelhados, de POM-C de **8 mm**, prendem as bordas da PCB do divisor de 39 × 78 × 1,52 mm. As quatro meias-luas acomodam as subidas dos cabos centrais. A face das trilhas fica em Z = −6,00 e a face das malhas coaxiais em Z = −7,52. O centro do divisor está deslocado +2,509 mm em X para acompanhar a linha real das sondas.

## Cabos, vedação e entradas em CC

Cada um dos dez rasgos de 7,00 × 12,018 mm recebe um passa-cabos duplo de silicone com garganta para a chapa de 2 mm. Instalar antes de soldar os coaxiais. O arquivo de formação descreve as linhas de centro em coordenadas da antena. Os vinte caminhos de saída somam 254 mm cada, incluindo 3 mm reservados à terminação do radiador. Os dois caminhos entre a traseira dos conectores N e as entradas do divisor medem 306,64 mm cada. Somar a inserção no conector e aplicar a preparação de pontas correspondente ao gabarito usado na bancada. O menor raio ao eixo é 4,40 mm, que equivale a cerca de 2,61 mm internos para este coaxial. A ficha do UT-141C indica um mínimo interno de 1,905 mm. Reservar pelo menos 114 mm atrás de Z = 0 para o envelope nominal dos cabos, além da folga de montagem. [Ficha Micro-Coax UT-141C](https://www.micro-coax.com/wp-content/uploads/2024/12/micro-coax-ut-141c-datasheet.pdf)

Os dois N fêmea de 50 Ω usam a referência Amphenol 082-6784 para RG-402 / semirrígido de 0,141″. Montar o corpo de fora para dentro, com a junta de silicone sob o flange externo e arruela de trava e porca internamente. O desenho prescreve recorte Ø16,50 com 14,00 entre planos e aperto de painel de 30 lbf·in (3,39 N·m). O eixo de cada N fica 31 mm atrás da face frontal. Usar conector acoplante vedado ou tampão vedado conforme a condição de serviço. A referência IP67 é do conector; a estanqueidade da antena montada depende do fechamento e de ensaio físico. Os modelos dos N representam os volumes de montagem, chave, junta e cabo. [Desenho Amphenol 082-6784](https://www.amphenolrf.com/en-us/assets/file/4069129560/)

Passar a manga termorretrátil do kit no cabo antes da soldagem. Após a união, cobrir a entrada do cabo no corpo do conector e retrair. Preservar o contato elétrico da arruela com a chapa se houver pintura ou anodização. O assento externo da junta deve permanecer plano e livre de riscos radiais.

L1 e L2 fazem a ligação de corrente contínua do condutor central para a blindagem do respectivo cabo, junto a J1 (A) e J12 (B). O modelo prevê uma janela acessível de 4 mm na terminação de entrada. Duas pequenas linguetas ligam a blindagem ao anel GND da PCB. A bobina fica na lateral da janela. A geometria reservada é fio de cobre esmaltado de Ø0,30 mm, diâmetro médio 1,80 mm, duas espiras e passo de 0,73 mm. Desesmaltar e estanhar as pontas e manter as espiras afastadas. Verificar a continuidade pino–carcaça de cada N e a ligação da carcaça à chapa. O valor de indutância, a resposta em 5 GHz e a capacidade de corrente exigem qualificação antes de fixar a geometria elétrica.

## Conferências e edição

Os dois FCStd da chapa contêm perfis e extrusões nativos. Na montagem, os componentes estão posicionados no sistema de coordenadas do projeto. Foram conferidos o sólido do refletor reaberto em FreeCAD e STEP, as 31 curvas fechadas do DXF, os encaixes das placas e dos conectores e as interferências entre cabos e com chapa, suportes, trilhos e parafusos. Os caminhos dos cabos são sólidos geométricos construídos com retas e arcos; foram verificadas as 22 extensões. [Registro da conferência](verificacao.json)

O envelope da montagem nominal reaberta no FreeCAD é de **546,0 × 90,6 × 133,1 mm** (X × Y × Z), incluindo os dois N e o chicote. Os limites em Z são −113,47 e +19,60 mm. As duas bobinas tocam no CAD o pino central e a blindagem da entrada correspondente. A verificação de bancada deve confirmar a resistência de cada união soldada.

A série RF anterior usou dez refletores individuais. Esta revisão mecânica tem um refletor contínuo, base dobrada, nervuras, chicote formado, dois cabos adicionais de entrada e duas bobinas. O desempenho RF desta montagem permanece em aberto. A R01 é uma revisão de protótipo mecânico. Os limites de ganho e abertura de outra geometria não se transferem automaticamente.

Para regenerar os modelos, usar [formar_cabos.py](fonte/formar_cabos.py) no Python com NumPy e SciPy, [construir.py](fonte/construir.py) no FreeCAD e [exportar_corte.py](fonte/exportar_corte.py) e [desenhos.py](fonte/desenhos.py) no Python com ezdxf, Shapely e Matplotlib. Os perfis da chapa e as furações partem de [dimensoes.py](fonte/dimensoes.py). Em uma nova revisão, conferir as cotas de desenho, o raio real da dobradeira e todas as interfaces antes da liberação.
