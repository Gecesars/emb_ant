"""Documenta a montagem R09 ja criada/verificada, sem executar simulacao."""
from pathlib import Path
import json,csv,hashlib,datetime
ROOT=Path(__file__).resolve().parents[1]/'mecanica_R09_PRELIMINAR'
rows=[
('01','PCB C12 4_elementos',8,'184 × 70 mm, RO4350B núcleo 0,76 mm, Cu 35 µm, ENIG nominal','328 corpos RF preservados; nenhuma furação nova na PCB'),
('02','Refletor',1,'Al 5052 proposto, 776 × 146 × 2 mm','16 passagens RF originais + 32 M2 + 6 M4 + 12 M3 novos; novos furos não simulados'),
('03','Base inferior',1,'Al 6061-T6 proposto, 146 × 70 × 4 mm; recortes N e rebaixos Ø32 × 2 mm','Primitivas/Cuts nativos editáveis; material/acabamento/tolerâncias a confirmar'),
('04','Reforço longitudinal L',2,'L 20 × 20 × 2 mm, comprimento 780 mm; pé soldado 4 × 20 × 20 mm','Al 6061-T6 proposto; solda/processo/resistência não dimensionados'),
('05','Grampo isolante de borda',32,'POM natural, largura 5 mm, altura de apoio 14,949 mm','4 por PCB; retenção de borda sem furar laminado; folga a ajustar ao acabado'),
('06','Parafuso M2x25',32,'Inox A2, cabeca cilindrica','Roscas simplificadas noCAD; aperto nao definido'),
('07','Porca M2',32,'Inox A2','Envelope nominal; catalogo a confirmar'),
('08','Arruela M2',64,'Inox A2, Ø4 / Ø2,2 × 0,5 mm','2 por fixação'),
('09','Parafuso M4 × 12',6,'Inox A2; reforço ao refletor','3 por reforço; cabeça frontal abaixo das PCBs'),
('10','Parafuso M4 × 16',2,'Inox A2; pé dos reforços à base','1 por reforço; roscas simplificadas'),
('11','Porca M4',8,'Inox A2','3,2 mm de altura nominal'),
('12','Arruela M4',16,'Inox A2, Ø9 / Ø4,4 × 0,8 mm','2 por fixação'),
('13','PCB central duplo 1:2',1,'Reserva 60 × 78 × 1,52 mm, ZYF300CA-C proposto','Sem cobre/Gerbers; duas redes independentes A/B; projeto RF pendente'),
('14','PCB filial duplo 1:4',2,'Reserva 39 × 78 × 1,52 mm, ZYF300CA-C proposto','Sem cobre/Gerbers; centros X=±192 mm; projeto RF pendente'),
('15','Espaçador de rede M3',12,'POM, Ø5 / Ø3,2 × 8,48 mm','4 por PCB; face de apoio Z=−10,48 mm'),
('16','Parafuso M3 × 16',12,'Inox A2','Suportes das PCBs da rede; roscas simplificadas'),
('17','Porca M3',12,'Inox A2, altura 2,4 mm nominal','Catálogo a confirmar'),
('18','Arruela M3',24,'Inox A2, Ø7 / Ø3,2 × 0,5 mm','2 por fixação'),
('19','Kit N fêmea Amphenol 082-6784',2,'50 Ω, RG-402 / UT-141; STEP fornecido','Kit porca/arruela/junta já representado, não comprar duplicado; parede de montagem 2 mm'),
('20','UT-141C entrada',2,'425 mm por eixo; Ø3,581 mm','Comprimento geométrico, NÃO é lista de corte; decapagens/inserções/soldas pendentes'),
('21','UT-141C tronco',4,'260 mm por eixo; Ø3,581 mm','Ramais iguais por classe; raio de eixo 10 mm'),
('22','UT-141C saída',16,'205 mm por eixo; Ø3,581 mm','22 cabos somam 5,170 m de eixo; total por caminho 890 mm'),
]
with (ROOT/'lista_materiais_PRELIMINAR.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f,delimiter=';');w.writerow(['Item','Componente','Quantidade','Especificacao','Estado']);w.writerows(rows)
(ROOT/'lista_materiais.json').write_text(json.dumps([dict(zip(['item','componente','quantidade','especificacao','estado'],r)) for r in rows],ensure_ascii=False,indent=2),encoding='utf-8')
state=dict(estado='PRELIMINAR_MECANICA_E_REDE_PLANEJADA',data='2026-11-14',simulacoes_executadas=0,liberado_fabricacao=False,GUI_aberta=True,
 arquivo='P2M19_R09_PRELIMINAR.FCStd',observacao='A antena RF de referencia e R08/14passes. As adicoes mecanicas/rede/cabos nao foram simuladas.')
(ROOT/'estado.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
assert json.loads((ROOT/'verificacao_cad.json').read_text())['intersecoes']==[]
review=dict(data='2026-11-14',revisor='Codex',estado='REVISADO',imagens=[dict(arquivo=str(p.relative_to(ROOT)).replace('\\','/'),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted((ROOT/'imagens').glob('*.png'))],
 observacao='Nove vistas. Frente/traseira ajustadas para margem; detalhes base/N/grampos/rede legiveis. Vista acesso porcas oculta cabos/parteferragens intencionalmente; azul nas PCBs indica reserva semcobre.')
(ROOT/'revisao_visual.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
print('BOM, estado e revisao visual gravados.')
