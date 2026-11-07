# R05 · correção da placa contínua e dos divisores compactos

**Campanha integral encerrada em 7/11/2026 por mudança de método solicitada pelo usuário.** Não houve resultado integral convergido de ganho. A qualificação continua na [R06, com PCBs separadas e circuito sem perdas de cabo](../r06/README.md). As tabelas abaixo são diagnósticos e cupons históricos; não constituem aprovação do painel montado.

O candidato conserva as três PCBs cotadas da R02. Muda a terminação das bobinas de curto DC, a face do refletor de 36 para 40 mm e o chicote para 290 / 132 / 135 mm nas entradas, enlaces e ramais. As duas entradas N recebem 0,5 W a 0°, total de 1 W incidente. O plano anterior de aceitação era 5,09–5,25 GHz, com 17 pontos discretos; esse cálculo integral não foi concluído. O aceite atual da R06 é no centro de 5,17 GHz.

| Evidência concluída | Resultado | Limite de interpretação |
|---|---|---|
| Referência integral R02 a 5,17 GHz | 12,00 dBi; H 94,82° | Reprova ganho; base da correção |
| Placa/refletor de 36 mm, vinte portas diretas | 17,237 dBi; H 100,599° | Exclui a rede traseira; H fora da meta |
| Placa/refletor de 40 mm, vinte portas diretas | 17,383 dBi; H 97,205°; V 5,609° | Exclui a rede traseira; somente 5,17 GHz |
| Bobina com abertura radial de Ø1 mm | Perda 0,0214 dB no centro; retorno mínimo 30,44 dB | Cupom calculado em 17 pontos |
| Divisor 1:2 com cobre físico e ENIG unilateral | Perda excedente 0,209–0,236 dB | Cupom em 17 pontos, oito passes, ΔS final 0,00649 |
| Predição da rede com 290/132/135 mm | 16,545–16,660 dBi | **Antena congelada em 5,17 GHz; não valida a banda** |

Os dez radiadores incluem acoplamento mútuo no diagnóstico de vinte portas. A exigência anterior de modelo integral visava esclarecer a diferença da recombinação por blocos da referência R02. A R06 adota a separação solicitada pelo usuário e declara a exclusão do acoplamento direto com os trajetos de cabo; não usa essa aproximação como prova de desempenho do modelo integral anterior.

A primeira tentativa integral com ENIG por shell elements falhou na representação de contatos metálicos. Não produziu ganho utilizável. A correção usa 138 sólidos de cobre de 35 µm e acabamento Au/NiP unilateral nas faces expostas. O divisor isolado comprovou que essa representação resolve e converge; comparado ao shell, sua perda excedente mudou cerca de −0,021 dB. O painel exige ΔS ≤ 0,008 e estabilidade de 0,05 dB nas nove amostras angulares monitoradas, por dois passes consecutivos, além da avaliação dos cortes completos.

As condutividades do NiP e os dielétricos dos acessórios são hipóteses nominais. O conector N usa dimensões internas aproximadas e ainda precisa ser substituído ou correlacionado com dados do componente comprado. O teste de esmalte de 20 µm, εr = 4,5 e tanδ = 0,03, alterou a previsão da rede em menos de 0,0024 dB; isso não certifica um fio comercial. A decisão atual deve consultar o resultado da R06 e distingui-lo da validação física do protótipo.

[Mecânica, chapa dobrada e planificada](../../freecad/mecanica_R05/README.md) · [Procedimento e histórico técnico](../../automacao/r05/README.md) · [Referência de conector encontrada no Drive](referencia_conector_drive.md) · [Referência R02](../r02/comparacao_paineis.md)
