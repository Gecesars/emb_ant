"""Audita e desenha os Gerbers/Excellon reais exportados pelo KiCad 10.

Parser restrito ao subconjunto produzido nesta placa: regioes lineares positivas,
flashes circulares, perfil linear e Excellon metrico decimal. Comandos geometricos
nao suportados provocam erro; nao ha inferencia por extensao apenas.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import math
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch
from shapely import affinity, make_valid
from shapely.geometry import Point, Polygon, LineString, shape
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

REPO=Path(__file__).resolve().parents[3]
OUT=REPO/'projetos/P2M21/kicad/4_elementos'
CAM=OUT/'gerbers'
SOURCE=REPO/'projetos/P2M21/quatro_elementos_casamento_banda/c12_raiz_intermediaria'
g=json.loads((SOURCE/'geometria.json').read_text(encoding='utf-8'))

def read_gerber(path, function):
    raw=path.read_text(encoding='utf-8')
    assert '%FSLAX46Y46*%' in raw and '%MOMM*%' in raw
    assert '%TF.FileFunction,'+function+'*%' in raw
    assert '%LPC' not in raw and '%AM' not in raw
    apertures={int(n):float(d) for n,d in re.findall(r'%ADD(\d+)C,([.\d]+)\*%',raw)}
    parts=[]; segments=[]; region=None; aperture=None; last=None
    for line in raw.splitlines():
        if line=='G36*':
            assert region is None
            region=[]
        elif line=='G37*':
            assert region is not None and len(region)>3 and region[0]==region[-1]
            parts.append(make_valid(Polygon(region))); region=None
        elif m:=re.fullmatch(r'D(\d+)\*',line):
            aperture=int(m[1]); assert aperture in apertures
        elif m:=re.fullmatch(r'X(-?\d+)Y(-?\d+)D0([123])\*',line):
            pt=(int(m[1])/1e6,int(m[2])/1e6); op=m[3]
            if op=='3':
                assert region is None and aperture in apertures
                parts.append(Point(pt).buffer(apertures[aperture]/2,quad_segs=256))
            elif region is not None:
                assert (op=='2') == (len(region)==0)
                region.append(pt)
            elif op=='1':
                assert last is not None
                segments.append((last,pt))
            last=pt
        else:
            assert (not line or line.startswith(('G04 ','%TF.','%TA.','%TO.','%TD','%ADD'))
                    or line in ('%FSLAX46Y46*%','%MOMM*%','%LPD*%','G01*','M02*')),line
    assert region is None
    return unary_union(parts),segments

def cam_transform(s):
    # CAM Y is upward: from HFSS X/Y to Gerber X=80+Y, Y=X-110.
    return affinity.affine_transform(s,[0,1,1,0,80,-110])

def disk(pt,r): return Point(pt).buffer(r,quad_segs=256)

expected={face:[] for face in ('F','B')}
for land in g['lands']: expected[land['layer']].append(shape(land['geometry']))
for face in expected:
    expected[face]+=[disk(pt,.363) for pt in g['vias']]
    expected[face]+=[disk((p['x'],p['y']),.8) for p in g['inputs']]
    expected[face]=cam_transform(unary_union(expected[face]))
actual={}; results=[]
for face,suffix,func in [('F','gtl','Copper,L1,Top'),('B','gbl','Copper,L2,Bot')]:
    a,segments=read_gerber(CAM/f'4_elementos-{face}_Cu.{suffix}',func)
    assert not segments
    e=expected[face]; diff=a.symmetric_difference(e).area; dist=a.hausdorff_distance(e)
    assert diff<.0003 and dist<.000002,(face,diff,dist)
    actual[face]=a
    results.append(dict(face=face,area_diferente_mm2=diff,Hausdorff_mm=dist))

board=cam_transform(Polygon(g['outline']))
for face,suffix,func in [('F','gts','Soldermask,Top'),('B','gbs','Soldermask,Bot')]:
    mask,segments=read_gerber(CAM/f'4_elementos-{face}_Mask.{suffix}',func)
    assert not segments and mask.equals(board)
    assert '%TF.FilePolarity,Negative*%' in (CAM/f'4_elementos-{face}_Mask.{suffix}').read_text()
_,segments=read_gerber(CAM/'4_elementos-Edge_Cuts.gm1','Profile,NP')
assert len(segments)==4 and set(Counter(p for s in segments for p in s).values())=={2}
assert unary_union([LineString(s) for s in segments]).equals(board.boundary)

drill=(CAM/'4_elementos-PTH.drl').read_text()
assert 'METRIC' in drill and 'TF.FileFunction,Plated,1,2,PTH' in drill
tools={int(n):float(d) for n,d in re.findall(r'^T(\d+)C([\d.]+)$',drill,re.M)}
holes={d:[] for d in tools.values()}; current=None
for line in drill.splitlines():
    if m:=re.fullmatch(r'T(\d+)',line): current=tools[int(m[1])]
    elif m:=re.fullmatch(r'X(-?[\d.]+)Y(-?[\d.]+)',line):
        assert current is not None
        holes[current].append((float(m[1]),float(m[2])))
    else:
        assert (line.startswith((';','T')) or line in ('M48','FMAT,2','METRIC','%','G90','G05','M30')),line
assert {d:len(v) for d,v in holes.items()}=={.4:8,1.1:2}
npth=(CAM/'4_elementos-NPTH.drl').read_text()
assert 'TF.FileFunction,NonPlated,1,2,NPTH' in npth and not re.search(r'^X',npth,re.M)
expected_holes={.4:[(80+y,x-110) for x,y in g['vias']],
                1.1:[(80+p['y'],p['x']-110) for p in g['inputs']]}
errors=[]
for diameter in holes:
    for p,q in zip(sorted(holes[diameter]),sorted(expected_holes[diameter])):
        errors.append(math.dist(p,q))
        assert max(abs(v-w) for v,w in zip(p,q))<=.000501,(p,q)
drills=unary_union([disk(p,d/2) for d,pts in holes.items() for p in pts])
edge_clearance=min(a.distance(board.boundary) for a in actual.values())
assert all(board.contains(a) for a in actual.values()) and edge_clearance>=.15
result=dict(aprovado=True,fonte='Gerbers X2 e Excellon realmente exportados',cobre=results,
    contorno_mm=[70,184],contorno_fechado_unico=True,mascara_aberta_duas_faces=True,
    PTH={str(d):len(p) for d,p in holes.items()},NPTH=0,
    erro_posicao_Excellon_max_mm=max(errors),resolucao_Excellon_mm=.001,
    folga_cobre_borda_mm=edge_clearance,
    nota='Excellon decimal nativo KiCad arredonda a 0,001 mm; cobre Gerber a 0,000001 mm. Estes valores nao sao tolerancias de fabricacao.',
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(CAM.iterdir())})
(OUT/'verificacao_gerbers.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def draw(ax,s,color,alpha=1):
    if s.is_empty:return
    if s.geom_type!='Polygon':
        for p in s.geoms:draw(ax,p,color,alpha)
        return
    s=orient(s,1); vertices=[]; codes=[]
    for ring in [s.exterior,*s.interiors]:
        xy=list(ring.coords);vertices.extend(xy)
        codes.extend([MPath.MOVETO]+[MPath.LINETO]*(len(xy)-2)+[MPath.CLOSEPOLY])
    ax.add_patch(PathPatch(MPath(vertices,codes),facecolor=color,edgecolor='none',alpha=alpha))

fig,axs=plt.subplots(1,3,figsize=(12,11))
for i,ax in enumerate(axs):
    if i<2:
        face=('F','B')[i];draw(ax,actual[face].difference(drills),('#b96616','#246ca4')[i])
        ax.set_title(face+'.Cu + furos PTH')
    else:
        draw(ax,actual['B'],'#246ca4',.45);draw(ax,actual['F'],'#b96616',.85);draw(ax,drills,'white')
        ax.set_title('Sobreposição F/B e furação')
    x,y=board.exterior.xy;ax.plot(x,y,color='#333333',lw=.7)
    ax.set_aspect('equal');ax.set_xlim(40,120);ax.set_ylim(-207,-13)
    ax.set_xlabel('X CAM [mm]');ax.set_ylabel('Y CAM [mm]');ax.tick_params(labelsize=8)
    for p in g['inputs']:
        ax.annotate(p['name'],(80+p['y'],p['x']-110),xytext=(0,9),textcoords='offset points',ha='center',fontsize=9)
fig.suptitle('4_elementos — leitura dos arquivos de fabricação\n70 × 184 mm | 8 vias Ø0,40 + 2 entradas Ø1,10 mm | vista comum pelo topo',fontsize=14)
fig.tight_layout(rect=(0,.025,1,.94))
fig.text(.5,.012,'Máscara: abertura integral nas duas faces. Sem serigrafia. Contorno e furos lidos do CAM.',ha='center',fontsize=10)
fig.savefig(OUT/'preview/gerbers_conferidos.png',dpi=160);plt.close(fig)
print(json.dumps({k:result[k] for k in ['aprovado','cobre','PTH','NPTH','erro_posicao_Excellon_max_mm','folga_cobre_borda_mm']},indent=2))
