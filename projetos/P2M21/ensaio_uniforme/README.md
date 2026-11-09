# P2M21 — ensaio uniforme de 16 níveis × 2 colunas

Pedido de 9/11/2026: corrigir a malha e calcular ganho total e aberturas horizontal/vertical em **17 frequências de 5,09 a 5,25 GHz**, a cada 10 MHz, com todas as portas na mesma amplitude e fase. A última instrução aceita **ΔS ≤ 0,04**, substituindo o valor anterior de 0,02; mantém o máximo de **seis passes**.

**Estado: cálculo em andamento, sem resultado novo aprovado.** Esta página será atualizada após a auditoria. Os números de [pré-dimensionamento](../estimativa_uniforme/README.md) são estimativas e não resultados deste ensaio.

**Verificação de 9/11 às 03:18:** quatro passes concluídos, 3.432.963 tetraedros e ΔS = 0,249792, ainda acima de 0,04; a adaptação para o quinto passe está ativa. O cache frontal do quarto passe registra 22,94745 dBi em 5,17 GHz, exclusivamente como resultado preliminar sem convergência. A nova malha tem zero reparos graves e sete menores até esta verificação. A banda de 17 pontos ainda não começou e não há aberturas H/V exportadas. [Evidências do monitoramento, sem interferir no solver](monitor_20261109_0318.json).

## Modelo e excitação

- Mesma geometria R00: 32 radiadores de duas polarizações, quatro módulos 2×4, refletor e apoios. Passos de 52,6 mm vertical e 40 mm horizontal.
- As **64 portas** recebem **15,625 mW a 0°**, totalizando **1 W incidente**. O ganho principal é o ganho frontal realizado total (`RealizedGainTotal`), normalizado pela soma das potências de todas as portas.
- Nesta etapa as portas são alimentadas diretamente: não há divisores nem cabos no modelo radiante. Os divisores R00 permanecem separados e preservados. A excitação uniforme não representa os desequilíbrios da rede física carregada.
- A análise coerente total não substitui a qualificação MIMO de cada entrada com a outra casada.

## Correção da malha

O R00 anterior encerrou seis passes com ΔS = 0,040859 e sete corpos com reparos graves. Seus resultados e sua malha foram preservados. O novo projeto foi copiado **sem importar resultados ou malha antiga**.

Aplicou-se aproximação de superfície com desvio de 0,0005 mm e normal de 5° aos 64 fragmentos Cu0, 64 Cu1 e 128 soldas. O limite de comprimento de 0,06 mm foi acrescentado aos Cu0; os Cu1 já tinham esse limite. A configuração das vias foi preservada. A conferência do arquivo nativo verificou a igualdade dos **782 blocos de geometria** com a origem: nenhum corpo foi redesenhado para ocultar um reparo.

Há nove amostras de campo registradas por passe, somente para observar a evolução do ganho próximo ao eixo e aos limites dos feixes. Elas não impõem um critério adicional ao ΔS solicitado. O centro deve atender ΔS ≤ 0,04 em dois passes consecutivos, dentro do máximo de seis. Atingir o sexto passe sem convergir interrompe a fila.

## Sequência e auditoria

1. Resolver a adaptação em 5,17 GHz.
2. Auditar o histórico nativo, as matrizes S64 e os avisos de reparo. A banda só começa após convergência e ausência de reparos graves.
3. Executar `Banda17`, do tipo **Discrete**, com campos radiados salvos nos 17 pontos reais. É uma malha adaptada no centro, não 17 adaptações independentes.
4. Exportar os cortes complexos H/V, ganho realizado total, ganho referido à potência aceita e diretividade. Medir aberturas a −3 dB e desvios de apontamento.
5. Conferir as frequências, normalização de 1 W, passividade, reciprocidade, coerência entre campos e ganho, e potência aceita obtida da matriz S64.

Os nativos, matrizes, cortes, tabelas e evidências compactas serão arquivados. Malhas, `.aedtresults`, campos volumétricos, `g3derr` e locks permanecem fora do Git.

Trabalho local: `D:/dev/EMBRAER/P2M21/R02_Malha_Uniforme17`. Scripts: [preparação](../automacao/uniforme_preparar.py), [execução](../automacao/uniforme_resolver.py), [auditoria](../automacao/uniforme_verificar.py) e [fila](../automacao/uniforme_pipeline.ps1).
