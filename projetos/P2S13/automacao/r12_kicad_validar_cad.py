"""Audita KiCad M00 contra as faces e barris do CAD original e rastreia C08."""
from pathlib import Path
import json,hashlib,collections
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
R=Path(__file__).resolve().parents[3];O=R/'projetos/P2S13/kicad/conjunto_R12';P=O/'placa2_M00'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=read(P/'faces_cad.json');k=read(P/'leitura_kicad.json');disk=lambda p,r:Point(p).buffer(r,quad_segs=2048)
assert k['native_sha256']==sha(P/'2_elementos.kicad_pcb')
actual={}
for v in k['drawings']:actual.setdefault((v['layer'],v['net']),[]).extend(Polygon(p).buffer(0) for p in v['contours'])
for p in k['pads']:
 for layer in p['layers']:actual.setdefault((layer,p['net']),[]).append(disk(p['center'],p['diameter']/2))
for p in k['vias']:
 for layer in 'FB':actual.setdefault((layer,p['net']),[]).append(disk(p['center'],p['diameter']/2))
holes=unary_union([disk(v['center'],v['drill']/2) for v in k['pads']+k['vias'] if v['drill']])
rows=[]
for key,parts in actual.items():
 a=unary_union(parts).difference(holes)
 e=unary_union([Polygon(x['exterior'],x['furos']) for x in c['faces'] if (x['camada'],x['rede'])==key])
 assert a.buffer(5e-6).covers(e) and e.buffer(5e-6).covers(a),(key,a.symmetric_difference(e).area)
 rows.append(dict(camada=key[0],rede=key[1],desvio_limite_mm=5e-6,diferenca_area_mm2=a.symmetric_difference(e).area))
assert len(c['barrels'])==6 and all(abs(x['metalizacao_mm']-.035)<1e-10 for x in c['barrels'])
assert collections.Counter(x['diametro_acabado_mm'] for x in c['barrels'])=={.4:4,1.1:2}
drc=read(O/'divisor_C08/drc_12nov.json');assert not drc['unconnected_items']
assert all(x['severity']=='warning' and x['type']=='solder_mask_bridge' for x in drc['violations'])
source_c08=read(O/'origem_C08.json')
for x in source_c08:assert sha(O/x['arquivo'])==x['sha256']==sha(R/x['fonte'])
results=dict(aprovado_geometria_CAD=True,comparacoes=rows,barrels=c['barrels'],fonte_fcstd_sha256=c['fonte_fcstd_sha256'],
 metalizacao_PTH_M00_mm=.035,nota='35 um sao o valor fisico usado no CAD/HFSS M00, distintos dos 18 um do C08. O pacote nao autoriza substituicao silenciosa de processo.',
 arte_C08_inalterada=True,arquivos_C08_conferidos=len(source_c08),DRC_C08_erros=0,DRC_C08_desconectados=0,DRC_C08_avisos=len(drc['violations']))
(O/'conferencia_CAD_conjunto.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
print('Faces CAD/KiCad M00 conferidas:',len(rows),'C08 arquivos:',len(source_c08),'sem alterar geometria RF.')
