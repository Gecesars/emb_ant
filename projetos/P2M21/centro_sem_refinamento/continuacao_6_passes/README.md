# P2M21 — dois passes adicionais e diagramas polares

**Em cálculo: os passes adicionais 5 e 6 foram autorizados em 9/11. Ainda não há resultados novos nem email enviado.** A adaptação continua a partir da malha do quarto passe, somente em 5,17 GHz, com 14 núcleos e sem sweep. O mínimo/máximo foi fixado em seis para executar exatamente os dois passes pedidos. Os quatro anteriores e sua classificação preliminar estão preservados no diretório pai e no histórico Git.

A conferência do nativo confirmou alterações somente nos limites mínimo/máximo de passes. Geometria, fontes, expressões de campo e demais opções de setup ficaram idênticas. O quinto passe iniciou em 9/11 às 05:27:50 com `-solve_adapt 5 -max_processors 14`.

Após o sexto passe serão revisados ganho, H/V, DeltaS, qualidade numérica e comparação com quatro passes. Os diagramas H/V usarão amplitude linear total `E/Emax = sqrt(|Etheta|²+|Ephi|²)/máximo do corte`, e serão conferidos contra `10^((G-Gmax)/20)`. O vertical terá detalhe frontal para leitura do feixe estreito.

O usuário autorizou envio de dois PNG finais para **gecesars@gmail.com**. Não enviar prévias ou reutilizar os gráficos do quarto passe. `email_payload_polares.py` exige seis passes reais e registro de revisão visual com hashes; somente prepara a mensagem. O envio efetivo usa o conector Gmail e deve guardar o recibo, evitando duplicatas.

Scripts: `continuacao_dois_preparar.py`, `continuacao_dois_pipeline.ps1`, `continuacao_dois_verificar.py`, `continuacao_dois_entregar.py`, `polares_emax.py` e `email_payload_polares.py`, em `projetos/P2M21/automacao`. Trabalho local: `D:/dev/EMBRAER/P2M21/R04_Centro_Classic`. Não executar novamente a fila existente.
