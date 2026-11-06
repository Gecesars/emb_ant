# Curto em CC nas duas entradas

O HFSS resolveu dois corpos de prova coaxiais com a janela de 4 mm prevista na entrada do divisor. Ambos têm as mesmas linguetas de massa e duas portas de 50 Ω. A peça com bobina usa a união de cobre extraída da entrada A do painel. As dimensões da hélice também se aplicam à entrada B. Os planos de referência ficam 4 mm antes e 4 mm depois da janela.

| Frequência | Perda de inserção sem bobina | Com bobina | Acréscimo | Perda de retorno da entrada com bobina |
|---|---:|---:|---:|---:|
| 5,09 GHz | 0,77 dB | 1,07 dB | 0,30 dB | 6,84 dB |
| 5,17 GHz | 0,81 dB | 1,10 dB | 0,29 dB | 6,75 dB |
| 5,25 GHz | 0,85 dB | 1,13 dB | 0,29 dB | 6,65 dB |

A perda de inserção é −20 log₁₀|S₂₁|, com a saída casada. Inclui o efeito das reflexões nas descontinuidades. Os dois lançamentos A e B estão em paralelo no painel, um por polarização. O acréscimo por caminho fica entre 0,285 e 0,297 dB nos 17 pontos. Para o ganho da antena, é preciso resolver a rede carregada pelo divisor e pelos radiadores.

O controle convergiu em oito passes, com ΔS de 0,00501. A geometria com a bobina convergiu em seis passes, com ΔS de 0,00164. Os dois modelos atingiram o critério de 0,008 em dois passes consecutivos, seguidos por varreduras FEM discretas de 10 MHz. A verificação numérica confirmou 50 Ω, reciprocidade e passividade nas 17 frequências.

O contato contínuo no CAD liga o centro à blindagem. A resistência real em corrente contínua depende das duas soldas e da remoção do esmalte nas pontas. Este ensaio caracteriza a terminação local numa linha de 50 Ω. O ambiente do refletor e a carga do divisor pertencem ao modelo integrado.

[Resultados nos 17 pontos](comparacao.csv) · [Matriz com bobina](Com_bobina.s2p) · [Matriz de controle](Controle.s2p) · [Convergência com bobina](convergencia_Com_bobina.txt) · [Convergência do controle](convergencia_Controle.txt)
