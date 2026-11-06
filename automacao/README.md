# Reproduzir o estudo

Os modelos e as matrizes S são dados independentes. Para inspecionar a geometria, abra diretamente os arquivos em **hfss**, **kicad** ou **freecad**. Para recalcular, use uma pasta de trabalho separada; as malhas dos painéis são grandes.

Ambiente de referência: Windows, HFSS/AEDT 2024 R2, KiCad 10.0.5, FreeCAD 1.1 e Python 3.12 com NumPy, SciPy, matplotlib e scikit-rf. Os scripts internos de modelagem usam o interpretador ScriptEnv do AEDT. Os scripts de rede e gráficos usam o Python do sistema. A geração de placas requer o módulo pcbnew do KiCad.

1. Na raiz do checkout, rode `py -3.12 automacao/preparar_estudo.py D:/Simulacoes/P1H-repro` com um destino novo. O utilitário recompõe a organização dos scripts, geometrias e dados sem alterar os originais.
2. Para inspecionar um painel, abra `Comparacao_PCB/Continua/P1H_Continua.aedt` ou `Comparacao_PCB/Separadas/P1H_Separadas.aedt`. Para gerar ambas as malhas do zero, executar as varreduras e exportar os campos compatíveis com o pós-processamento, use o [roteiro de simulação](executar.ps1) em uma nova pasta de saída. Ele começa do elemento base, aplica a geometria KiCad e o refinamento de curvatura e resolve um painel por vez.
3. O roteiro resolve a placa de distribuição e a junta, interliga as redes, recombina os campos e gera `Comparacao_PCB/comparacao_P1H.md`. O script registra a convergência e recusa publicar resultados se as verificações de rede ou dos relatórios nativos falharem. Os arquivos de malha e de campos ficam somente na pasta de execução.

Exemplo no PowerShell (a pasta de saída deve estar vazia):

```powershell
./automacao/executar.ps1 -Destino D:/Simulacoes/P1H-novo
```

**Convenções.** X é o eixo da coluna e +Z é a frente. O corte horizontal está no plano YZ e o vertical no XZ. O painel é resolvido com vinte portas físicas, sem aproximação por fator de arranjo. A rede usa o divisor eletromagnético, vinte coaxiais com perdas e as transições soldadas. A co-simulação inclui reflexões entre as portas e o acoplamento de cada modelo EM. A radiação ou o acoplamento externo de cabos e suportes entre os blocos depende de uma instalação mecânica definida.

As referências FreeCAD podem ser regeneradas com o [script](../freecad/gerar_referencias.py) no Python do FreeCAD. As formas de cobre, furos, laminados e refletores são nominais. Use os arquivos KiCad e os Gerbers para as camadas de fabricação.
