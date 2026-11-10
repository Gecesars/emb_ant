"""Confere a arte KiCad reaberta contra a geometria efetiva do HFSS R13 C12.

Rodar com Python 3.12, Shapely, CairoSVG e Matplotlib. Nao executa HFSS.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import cairosvg
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from shapely.geometry import Polygon, Point, shape
from shapely.ops import unary_union

REPO=Path(__file__).resolve().parents[3]
OUT=REPO/'projetos/P2M21/kicad/4_elementos'
SOURCE=REPO/'projetos/P2M21/quatro_elementos_casamento_banda/c12_raiz_intermediaria'
g=json.loads((SOURCE/'geometria.json').read_text(encoding='utf-8'))
r=json.loads((OUT/'leitura_kicad.json').read_text(encoding='utf-8'))
assert hashlib.sha256((SOURCE/'geometria.json').read_bytes()).hexdigest()==r['source_sha256']
assert hashlib.sha256((OUT/'4_elementos.kicad_pcb').read_bytes()).hexdigest()==r['native_sha256']

def disk(xy,radius):
    return Point(*xy).buffer(radius,quad_segs=256)

expected={(l['layer'],l['net']):shape(l['geometry']) for l in g['lands']}
actual={key:[] for key in expected}
for drawing in r['drawings']:
    key=(drawing['layer'],drawing['net'])
    # KiCad fratura os furos de poligonos com pontes de largura zero.
    actual[key].extend(Polygon(c).buffer(0) for c in drawing['contours'])

for v in r['vias']:
    assert abs(v['diameter']-.726)<1e-8 and abs(v['drill']-.4)<1e-8
    for layer in ('F','B'):
        actual[(layer,v['net'])].append(disk(v['center'],v['diameter']/2))
for p in r['pads']:
    for layer in p['layers']:
        actual[(layer,p['net'])].append(disk(p['center'],p['diameter']/2))
actual={key:unary_union(value) for key,value in actual.items()}
# O CAD EM adiciona anilhas de vias e pads aos poligonos da geometria.json.
for layer in ('F','B'):
    expected[(layer,'SIG_B')]=unary_union([expected[(layer,'SIG_B')]]+[disk(xy,.363) for xy in g['vias']])
    for p in g['inputs']:
        key=(layer,p['sig'])
        expected[key]=expected[key].union(disk([p['x'],p['y']],.8))

drills=unary_union([disk(xy,.2) for xy in g['vias']]+[disk([p['x'],p['y']],.55) for p in g['inputs']])
comparisons=[]
for key in sorted(expected):
    a=actual[key].difference(drills)
    e=expected[key].difference(drills)
    diff=a.symmetric_difference(e).area
    distance=a.hausdorff_distance(e)
    comparisons.append(dict(layer=key[0],net=key[1],area_hfss_mm2=e.area,area_kicad_mm2=a.area,
        diferenca_area_mm2=diff,distancia_Hausdorff_mm=distance))
    assert diff<.0002 and distance<.000002,(key,diff,distance)
    actual[key]=a

shorts=[]
clear=100
for i,(key,a) in enumerate(actual.items()):
    for key2,b in list(actual.items())[i+1:]:
        if key[0]!=key2[0] or key[1]==key2[1]:continue
        clear=min(clear,a.distance(b))
        if a.intersection(b).area>1e-9:shorts.append([key,key2])
assert not shorts and clear>=.15
assert all(Polygon(g['outline']).contains(a) for a in actual.values())

# Verificacao independente da continuidade por polarizacao e camada.
connectivity={}
for net in ('SIG_A','SIG_B','RET_A','RET_B'):
    nodes=[]
    for (layer,n),a in actual.items():
        if n!=net:continue
        polys=list(a.geoms) if a.geom_type=='MultiPolygon' else [a]
        nodes.extend((layer,p) for p in polys if p.area>1e-9)
    parents=list(range(len(nodes)))
    def find(i):
        while parents[i]!=i:i=parents[i]
        return i
    def join(indices):
        for i in indices[1:]:parents[find(i)]=find(indices[0])
    transitions=[v for v in r['vias'] if v['net']==net]+[p for p in r['pads'] if p['net']==net and p['drill']>0]
    for t in transitions:
        annulus=disk(t['center'],t['diameter']/2).difference(disk(t['center'],t['drill']/2))
        touched=[i for i,(_,a) in enumerate(nodes) if a.intersection(annulus).area>1e-8]
        join(touched)
    count=len({find(i) for i in range(len(nodes))})
    connectivity[net]=dict(componentes_conectados=count,partes_planares=len(nodes))
    assert count==1,(net,count)

drc=json.loads((OUT/'drc.json').read_text(encoding='utf-8'))
counts=Counter((v['severity'],v['type']) for v in drc['violations'])
errors=sum(v['severity']=='error' for v in drc['violations'])
assert errors==0 and not drc['unconnected_items']
assert all(v['type']=='solder_mask_bridge' for v in drc['violations'])
result=dict(aprovado_geometria=True,fonte='geometria R13 C12 mais anilhas de vias/pads e furos do CAD EM',
    tolerancia_Hausdorff_mm=.000002,tolerancia_area_mm2=.0002,
    max_distancia_Hausdorff_mm=max(x['distancia_Hausdorff_mm'] for x in comparisons),
    max_diferenca_area_mm2=max(x['diferenca_area_mm2'] for x in comparisons),
    folga_minima_mm=clear,shorts=shorts,continuidade=connectivity,comparacoes= comparisons,
    drc_erros=errors,drc_desconectados=len(drc['unconnected_items']),
    drc_avisos=[dict(severity=k[0],type=k[1],quantidade=v) for k,v in counts.items()],
    observacao='Mascara totalmente aberta por intencao RF; nao implica qualificacao de fabricacao ou nova simulacao EM.')
(OUT/'verificacao.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

fig,axs=plt.subplots(1,2,figsize=(8,12))
for ax,layer in zip(axs,['F','B']):
    svg=OUT/'preview'/f'4_elementos-{layer}_Cu.svg'
    png=svg.with_suffix('.png')
    cairosvg.svg2png(url=str(svg),write_to=str(png),output_height=1800,background_color='white')
    ax.imshow(mpimg.imread(png));ax.axis('off')
    ax.set_title(layer+'.Cu — vista comum pelo topo',fontsize=10)
fig.suptitle('4_elementos — geometria R13 C12 no KiCad\n70 × 184 mm | RO4350B 0,76 mm | passo 48 mm',fontsize=13)
fig.text(.5,.025,'Cobre exportado do arquivo nativo; B.Cu sem espelhamento nesta comparação.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.045,1,.92))
fig.savefig(OUT/'preview/4_elementos.png',dpi=180)
plt.close(fig)
print(json.dumps({k:result[k] for k in ('aprovado_geometria','max_distancia_Hausdorff_mm','max_diferenca_area_mm2','folga_minima_mm','drc_erros','drc_desconectados','drc_avisos')},ensure_ascii=False,indent=2))
