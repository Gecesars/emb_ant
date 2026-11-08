# Verificação P2M21 — 8 de novembro de 2026

**A execução terminou às 16h43, sem convergência da antena. Não há aprovação de ganho ≥21 dBi por entrada nem VSWR <1,5 nos 17 pontos.** Não existe resultado do circuito completo com a outra entrada casada em 50 Ω e os cabos sem perdas.

| Verificação | Estado real |
|---|---|
| Antena, 5,17 GHz | Seis passes, 1.984.665 tetraedros; não convergiu |
| ΔS final / limite | 0,040859 / 0,02 — 4,0859% contra 2% |
| Passes consecutivos aprovados | Zero; exigidos dois |
| Auditoria de superfície | Sete corpos com reparo Major e dez com Minor |
| Antena, 17 frequências | Não executada; varredura estava desabilitada até aprovação do centro |
| Campos embutidos e S64 exportados | Ausentes; a fila interrompeu a exportação após reprovar a convergência |
| Circuito final e ganho por entrada | Não calculados |
| Divisores isolados | Ambos concluíram os 17 pontos, convergidos em seis passes |

O aviso de término normal do processo HFSS não significa convergência. O relatório de convergência registra explicitamente **Converged: No**, e a fila preservou esse bloqueio. Os processos dessa execução já encerraram. Nesta verificação não foi iniciada outra simulação.

Os reparos Major pertencem aos seguintes sólidos de cobre: E32/E21/E15 `Feed_B_Inner_Cu0`, E14 `Feed_A_Cu1` e E13/E12/E07 `Feed_B_Inner_Cu1`. Seus volumes são aproximadamente 0,0750 mm³ e 0,00794 mm³. Os nomes antes apresentados como `un_named` no log foram identificados pelos IDs do nativo. A contagem é de corpos únicos, não de avisos repetidos. Os dados e hashes estão no [diagnóstico estruturado](diagnostico_20261108.json) e na [auditoria compacta de malha](hfss/antena/malha.json).

Com as demais portas casadas em 50 Ω, o VSWR isolado dos divisores na banda foi:

| Divisor | Entrada A | Entrada B |
|---|---:|---:|
| Duplo 1:4 | 1,531–1,550 | 1,530–1,551 |
| Duplo 1:8 | 1,668–1,738 | 1,668–1,740 |

Esses valores são dos divisores isolados, não das entradas MIMO do painel. As reflexões dos radiadores e as fases das linhas alteram o resultado carregado. Eles não permitem afirmar o VSWR final, assim como a estimativa inicial de ganho não substitui os campos do painel simulado.

A próxima correção deve tratar a discretização das superfícies pequenas de cobre e solda, incluindo `Feed_B_Inner_Cu0`, que não recebeu o refinamento de comprimento reservado aos fragmentos `Cu1`. Depois será necessário resolver novamente com no máximo seis passes e ΔS ≤0,02, auditar a malha e só então executar os 17 pontos e o circuito. O limite de passes e a meta não foram aumentados ou relaxados.
