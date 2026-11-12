# P2S13 R17 — fechamento DN100 — PRELIMINAR

Montagem completa dimensionada em 12/11/2026. **Não liberada como antena RF qualificada nem como invólucro IP certificado.** A RF disponível compara apenas as abas laterais, antes de acrescentar os novos flanges, linguetas, suportes e entradas N–divisor.

- [Montagem FreeCAD](Antena_DN100_R17_PRELIMINAR.FCStd) e [STEP completo](Antena_DN100_R17_PRELIMINAR.step).
- [Relatório ilustrado de 7 páginas](documentacao/Relatorio_R17_PRELIMINAR.pdf).
- [Cinco pranchas A3](documentacao/Desenhos_R17_A3_PRELIMINAR.pdf), [BOM CSV](documentacao/BOM_R17.csv) e [pacote mecânico ZIP](P2S13_R17_Mecanica_PRELIMINAR.zip).
- [Chapa planificada FreeCAD](Refletor_planificado_PRELIMINAR.FCStd), [STEP](Refletor_planificado_PRELIMINAR.step) e [DXF](documentacao/Refletor_planificado.dxf).
- Flanges: [inferior STEP](Flange_Inferior.step), [DXF inferior](documentacao/Flange_Inferior.dxf), [superior STEP](Flange_Superior.step), [DXF superior](documentacao/Flange_Superior.dxf).
- [Parâmetros e coordenadas](dimensoes.json), [auditoria CAD](verificacao_cad.json), [contatos e reabertura STEP](verificacao_interfaces.json).

## Dimensões principais

| Item | Dimensão nominal |
|---|---|
| Tubo Tigre Série Normal DN100 | OD101,6; ID98; parede1,8; comprimento350 mm; sem bolsa |
| Flanges | Ø110 ×4,76 mm; Al6061-T6 proposto |
| Canal confirmado pelo usuário | Largura radial2,5; profundidade2,5; ID97,3; OD102,3 mm |
| Encaixe do tubo | Folga radial0,35 por lado; inserção2,2 por ponta |
| Vedação axial nominal | EPDM anular0,5 livre /0,3 montado; compressão40% a ensaiar |
| Comprimento entre faces externas dos flanges | 355,12 mm |
| Envelope com conectores e cabeças | 371,72 ×110 ×110 mm |
| Refletor | Al5052-H32 de2 mm; desenvolvido296×90; duas abas150° |
| Dobra lateral | TangênciaY±28,5; giro150° desde a chapa plana, ângulo interno30°; Ri2 |
| Linguetas finais | Largura20; giro90° para trás; Ri2; reta14; dois furosØ3,4 por ponta |
| Chapa planificada | Comprimento374,396459 mm; K0,4 nominal a calibrar |
| Radiantes | 3 PCBs88×50; núcleo0,76; centrosX−96/0/+96; seis níveis a48 mm |
| Grampos | 12 POM radiantes +4 POM divisor; largura5; sem novos furos nas PCBs |
| Conectores | 2×Amphenol082-6784; centrosY±22/Z−25; flange inferior |
| Recorte N | Ø16,5 com duas faces planas a14 mm |
| Cabos | 6 saídas134 mm; 2 entradas158,625 mm entre planos mecânicos, mais preparo/encaixe |

O STEP original possui face anular de assentamento em X=10,9 mm. O corpo foi colocado para contato efetivo com o flange e o conjunto porca/arruela deslocado1,69 mm em seu eixo local. A arruela completa foi isolada até X=5,5; a seleção antiga deixava pequenos fragmentos da arruela. Os dois conectores têm contato nominal com o flange e não atravessam outras peças. O STEP não separa os materiais internos para uso em RF.

## Verificações e limitações

São **219 objetos físicos /235 sólidos**. A auditoria de interfaces novas não encontrou interseções volumétricas; os contatos chapa–flanges, juntas–PVC/flanges e conectores–flange foram verificados. As PCBs, o divisor e os seis ramais R16 foram copiados sem alterar sua geometria. O STEP reimportado é válido; a diferença de volume global é aproximadamente2,07ppm. O FCStd/BREP é a referência geométrica principal.

O CAD inclui parafusos, arruelas, porcas, juntas, termorretráteis e oito cabos. Roscas das ferragens são simplificadas. O termorretrátil tem dimensão montada nominal; a proteção final depende da montagem. Não há interface de fixação a mastro nesta definição de fechamento.

O comprimento das novas entradas é de percurso entre a boca traseira do conector e a interface da PCB. Não é comprimento de corte pronto: o desenho Amphenol exige inserção até o batente, mas não cota esse encaixe como comprimento de corte no STEP. Confirmar uma amostra antes de cortar o lote. A ficha recomenda preparo com6,05mm de condutor central além da blindagem e4,10mm expostos além do dielétrico.

O canal deixa fundo nominal2,26mm e borda radial externa3,85mm. Medir ovalização/espessura do tubo, conferir juntas, dilatação térmica, retenção e estanqueidade. Não foi realizada análise estrutural nem ensaio IP. Espessuras e tolerâncias propostas estão nas pranchas. A planificação depende de K0,4 e do ferramental real.

## Escolha do refletor

As abas quase não alteraram H no teste atual (78,99° versus78,77°), mas a versão dobrada apresentou menor assimetria do principal vertical e menor secundário. Mantida na montagem principal, **sem afirmar equivalência RF validada**. [Resultados e ressalvas](../comparacao_refletor_R17/README.md). A [chapa plana alternativa](alternativa_plana/Refletor_plano_alternativo.step) usa as mesmas interfaces mecânicas; não substitui automaticamente a principal.

## Fontes e reprodução

- [Tigre Série Normal](https://www.tigre.com.br/produto/tubo-serie-normal-6m): dimensões nominais do tubo.
- [Amphenol82-6784](https://www.amphenolrf.com/en-us/assets/file/4069129560/): desenho do conector, faixa de painel1–6,75mm, recorte e torque30in·lbf. [STEP de referência](referencias/82-6784.stp).
- [Micro-Coax UT-141C](https://www.micro-coax.com/wp-content/uploads/2024/12/micro-coax-ut-141c-datasheet.pdf): OD3,581; vivoØ0,9195; PTFE; raio interno mínimo1,905mm. As entradas usam raio no eixo6mm, interno4,2095mm.

Scripts `../automacao/r17_mecanica.py`, `r17_verificar_interfaces.py`, `r17_imagens.py`, `r17_documentar.py` e `r17_empacotar.py`. Regeneração por parâmetros Python/JSON; não é uma árvore de juntas cinemáticas. O FreeCAD foi deixado aberto na montagem R17. Documentos anteriores preservados.
