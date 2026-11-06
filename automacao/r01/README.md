# Montagem R01 no HFSS

A geometria parte da montagem FreeCAD, dos perfis das trilhas e das 22 linhas de centro do chicote. As duas únicas portas do modelo estão nos conectores N. A referência é 1 W de potência incidente total, dividido igualmente, a 0°. +Z é a frente, X acompanha a coluna, YZ é o corte horizontal e XZ o vertical.

## Reprodução em diretório local

1. Definir a variável de ambiente `P1H_R01` com o caminho absoluto de uma pasta de trabalho e `P1H_ITERATIVO=1` para reproduzir a malha TAU Flex e o solucionador iterativo da campanha. Criar a subpasta `estudo`. No Python do FreeCAD 1.1, executar [preparar_em.py](preparar_em.py) com `runpy.run_path(..., run_name="__main__")`. O script verifica as formas OCCT e exporta os STEP por material para a subpasta `cad`.
2. No Ansys Electronics Desktop 2024 R2, executar [modelo_hfss.py](modelo_hfss.py) com `-ng -RunScriptAndExit`. A última linha de `estudo/modelo.log` deve ser `MODELO_OK`. O projeto inclui a geometria importada. Para refazer a importação, regenerar primeiro os STEP.
3. Executar [resolver.py](resolver.py) pelo mesmo comando do AEDT. O adaptativo roda em 5,17 GHz, alvo ΔS = 0,015 e dois passes consecutivos dentro do limite. O roteiro exporta a convergência, os parâmetros S e os dois cortes, depois configura a varredura discreta de 5,09 a 5,25 GHz em passos de 10 MHz. Ao gerar a malha e os campos, usar disco local fora do repositório.
4. Executar [medir.py](medir.py) com Python, NumPy e scikit-rf, passando os caminhos da subpasta `estudo` e de uma pasta de saída. A opção `--centro` mede apenas o adaptativo. O programa verifica as frequências, as duas impedâncias de referência, a passividade, a reciprocidade e a igualdade entre os ganhos em θ = 0° nos dois cortes. A abertura usa os cruzamentos interpolados 3 dB abaixo do pico de cada corte. O ganho frontal usa diretamente a amostra de θ = 0°.

## Premissas eletromagnéticas

| Componente | Representação nominal |
|---|---|
| Radiadores | Dez elementos em uma PCB contínua RO4350B, Dk de projeto 3,66, tan δ 0,0037, núcleo 0,76 mm. Cobre superficial 35 µm e rugosidade nominal de 0,5 µm. Sondas, anéis, vias e ponte de cruzamento explícitos. |
| Divisor 2 × 1:10 | ZYF300CA-C de 1,52 mm, Dk 2,94, tan δ 0,0016. Condutores impressos e lançamentos coaxiais. O pino e a solda no furo são um condutor preenchido. Os anéis de solda das blindagens nas vinte saídas usam 7,58 MS/m. Máscara e acabamento metálico final ficam fora do modelo. |
| Chicote | 20 saídas de 254 mm e 2 entradas de 306,64 mm. Condutores e dielétrico percorrem os arcos e retas do gabarito. Raios do condutor central, isolante e capa de 0,45975, 1,515 e 1,7905 mm. Dk equivalente 2,036 e tan δ nominal 0,000277. A perda é calibrada por aproximação TEM à atenuação de catálogo em torno do centro da banda. |
| Mecânica | Refletor de alumínio 5052, condutividade assumida 20 MS/m. Parafusos e arruelas simplificados. Apoios e trilhos em POM, Dk nominal 3,4 e tan δ 0,010. Silicone das vedações, Dk 2,77 e tan δ 0,020. Manga isolante, Dk 2,3 e tan δ 0,001. |
| Conectores e bobinas | Portas de 50 Ω na seção de acoplamento do N. Interior do conector aproximado por transição coaxial lisa, com trecho em ar e preenchimento parcial em PTFE. Contato metálico da porca com a rosca e a arruela representado. Duas espiras por entrada, diâmetro médio 1,80 mm, fio de 0,30 mm e passo de 0,73 mm. O cobre do fio, o percurso dos terminais e as uniões soldadas estão no modelo. A película de esmalte e a geometria microscópica das soldas dependem da montagem real. |

As propriedades dos polímeros mecânicos e as geometrias internas dos conectores são hipóteses de protótipo. Os resultados numéricos se referem à montagem nominal. A verificação de curto em corrente contínua considera o contato geométrico do pino, da bobina e da blindagem. A resistência do conjunto produzido deve ser medida entre pino e carcaça.

## Ensaio independente do lançamento com bobina

Após gerar o CAD da R01, apontar `P1H_BOBINA` para uma segunda pasta. Executar [bobina_cad.py](bobina_cad.py) no FreeCAD e [bobina_hfss.py](bobina_hfss.py) no AEDT. Executar [verificar_bobina.py](verificar_bobina.py) no Python com o diretório dos cupons e o nome do CSV de saída. O relatório do ensaio inclui as matrizes e a convergência dos dois corpos de prova. [Resultados das bobinas](../../resultados/r01/bobinas/README.md)

[Mecânica e fichas dos componentes](../../freecad/mecanica_R01/README.md) · [Cotação dos laminados efetivamente selecionados](../../resultados/r01/cotacao.md)
