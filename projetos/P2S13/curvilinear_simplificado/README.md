# R12 — simplificacao e elementos curvilineos

Pedido de 12/11/2026: melhorar a simulacao R11, simplificar o modelo e habilitar curvilinear elements. A R11 permanece arquivada e reprovada: no sexto passe o sistema linear iterativo atingiu 600 iteracoes, residual maximo 0,04803, e o balanco de potencia foi nao fisico.

## Mudancas desta revisao

- Uniao de 18 pares de corpos contiguos do mesmo material nos seis cabos: vivo com prolongamento, blindagem com prolongamento e PTFE com prolongamento. Total de corpos fisicos 141 para 123; faces 5634 para 5580. Nenhuma homogeneizacao de materiais distintos. Nao foram removidas perdas, soldas, metalizacao PTH, ENIG, dielétricos ou radome.
- Diferencas booleanas verificadas antes/depois das unioes, objetos nao envolvidos preservados, corpos validos, zero intersecoes volumetricas. Ver `cad/simplificacao.json` e `cad/intersecoes.json`. Placas e Gerbers C08 permanecem geometricamente inalterados; a simplificacao pertence ao modelo de simulacao.
- `GlobalCurvilinear.Apply=true` (antes false). Curvas de cabos, furos e refletor passam a usar a opcao global de elementos curvilineos. Esta opcao pode aumentar o custo por elemento; nao se presume ganho de desempenho apenas por habilita-la.
- `BasisOrder=1` (antes2), solver **Direct Solver** (antes Iterative Solver), crescimento adaptativo configurado30% (antes50%). O solver direto evita a mesma limitacao de600iteracoes do iterativo; memoria e tempo reais ainda precisam ser medidos. O percentual configurado nao e garantia do crescimento efetivo dos tetraedros.
- Classic automatico, slider5, sem fallback, sem TAU, sem MeshLink, sem operacoes locais de pre-refinamento e sem refinamento lambda inicial.

## Condicoes preservadas

5,17GHz somente, sem sweep, 14nucleos, no maximo6passes, DeltaS<=0,05 por2passes consecutivos. Fontes externas IN_A/IN_B de0,5W/0graus. Mesma geometria externa, tres placas de dois elementos, C08, seis cabos50mm e radome FR4 Isola370HR de2mm, nominal epsilon3,92/tand0,025. Refletor28,5mm/150graus. Conectores externos e vedacao nao caracterizados.

Metas: ganho frontal realizado>=12dBi, VSWRativo<=1,25, lobo principal vertical centrado (tolerancia angular anterior+/-0,5grau) e simetria registrada (auditoria0,2dB). VSWR com a outra entrada casada tambem e reportado. Convergencia S nao basta: conferir solver matricial, reciprocity, potencia, recomposicao dos campos e estabilidade. Nenhum resultado RF novo foi aprovado na preparacao.

`r12_pipeline.ps1` cria e fecha o nativo, verifica os parametros salvos em `setup_confirmado.json`, reabre para resolver e exportar, fecha, audita e plota. Qualquer falha para a fila; ela nao cria um novo ciclo nem ultrapassa6passes. Nao executar novamente enquanto houver uma fila ativa.

Referencia da opcao: https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v242/en/Subsystems/HFSS/Content/Mesh/SpecifyingInitialMeshSettings.htm. API local PyAEDT `Mesh.assign_initial_mesh_from_slider(curvilinear=True)` mapeia para `InitialMeshSettings / GlobalCurvilinear / Apply`. A configuracao efetiva deve ser confirmada no arquivo nativo, nao apenas no script.

## Estado do pacote

Calculo em andamento; sem resultados RF nesta copia. O AEDT ativo permanece somente na pasta de trabalho.
