# Historico dos ensaios — interrompido a pedido do usuario

Os testes foram encerrados em 10/11/2026 para concluir a [mecanica PRELIMINAR R18](../mecanica_preliminar_R18/README.md). Nao ha solver ativo nem retomada automatica.

| Caso | Ganho frontal total | H / V | DeltaS | Estado |
|---|---:|---:|---:|---|
| [R15: oito placas, 72 mm, oito passes](R15_Oito_Celulas_8passes/README.md) | 19,84687 dBi | 24,3513 / 3,7484 graus | 0,05001533 | Nao convergido |
| [R16: oito placas, 78 mm, seis passes](R16_Oito_Celulas_78mm/README.md) | 19,47983 dBi | 22,9569 / 3,7125 graus | 0,10314416 | Nao convergido |
| [R17: dez placas, 78 mm](R17_Dez_Celulas_78mm/README.md) | Sem resultado final | Sem resultado final | — | Interrompido no segundo passe |

Todos os valores calculados acima sao preliminares, em 5,17 GHz, com todas as entradas iguais e em fase, 1 W total, cabos fisicos de 50 mm e divisores impressos incluidos. Nao incluem a futura distribuicao externa de duas entradas. O alargamento de 72 para 78 mm nao comprovou melhora de ganho ou lobulos; a falta de convergencia impede uma conclusao de projeto. A R14 original e seus resultados permanecem preservados byte a byte, conforme preservacao_R14.json. Nenhum sweep foi executado.

O manifesto preserva nativos e evidencias compactas; malhas e campos FEM ficam somente no diretorio local de trabalho. O lock remanescente da interrupcao nao e copiado.
