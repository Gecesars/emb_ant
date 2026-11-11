"""Nova celula de dois elementos: etapas locais simetricas do C12, sem meandros assimetricos."""
from pathlib import Path
import json,math,hashlib,argparse
from shapely.geometry import Polygon,Point,LineString,mapping,box
from shapely.affinity import translate,scale
from shapely.ops import unary_union
from shapely import set_precision
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MP
from matplotlib.patches import PathPatch

REPO=Path(__file__).resolve().parents[3]
parser=argparse.ArgumentParser();parser.add_argument('--out',default='D:/dev/EMBRAER/P2S13/R01_Seis_Elementos/celula2_simetrica');parser.add_argument('--width',type=float);parser.add_argument('--length',type=float);args=parser.parse_args()
OUT=Path(args.out)
SRC=REPO/'projetos/P2M21/quatro_elementos_casamento_banda/c12_raiz_intermediaria'
assert not (OUT/'geometria.json').exists(),'Nao substituir celula existente'
OUT.mkdir(parents=True,exist_ok=True)
source=json.loads((SRC/'geometria.json').read_text());artfile=REPO/'automacao/P1H/KiCad_Antenas/elemento_hfss.json'
art=json.loads(artfile.read_text());p=art['ports']['B'][0];pitch=48.;centers=[-24.,24.]
lines=source['lines'];w50=lines['50']['w_mm'];w70=lines[str(50*math.sqrt(2))]['w_mm'];l70=lines[str(50*math.sqrt(2))]['l90_mm']
if args.width is not None:w70=args.width
if args.length is not None:l70=args.length
assert .3<=w70<=2.5 and 2<=l70<=23,(w70,l70)
outline=[[-44.,-25.],[44.,-25.],[44.,25.],[-44.,25.]];lands=[];vias=[];traces=[];inputs=[]
for i,cx in enumerate(centers,1):
    for land in art['lands']:
        net=land['net'] if land['net'] in ['SIG_A','SIG_B','RET_A','RET_B'] else 'E%d_'%i+land['net']
        lands.append(dict(layer=land['layer'],net=net,shape=translate(Polygon(land['outer'],land['holes']),cx,0)))
    vias.extend([[x+cx,y] for x,y in art['vias']])
signals={};grounds={}
for pol in 'AB':
    sy=-1 if pol=='A' else 1;yl=sy*18.;signal=[Point(p,yl).buffer(.95,quad_segs=48)];ground=[Point(p,yl).buffer(2.65,quad_segs=48)]
    for sign,cx in zip([-1,1],centers):
        q70=[(p,yl),(p+sign*l70,yl)];q50=[q70[-1],(cx+p,yl),(cx+p,sy*p)]
        signal += [LineString(q70).buffer(w70/2,cap_style='square',join_style='mitre'),LineString(q50).buffer(w50/2,cap_style='square',join_style='mitre')]
        full=q70+q50[1:];ground.append(LineString(full).buffer(3.,join_style='mitre'))
        traces.append(dict(polarizacao=pol,cx=cx,linha70=q70,linha50=q50,comprimento_mm=LineString(full).length,largura_transformador_mm=w70,largura_linha50_mm=w50))
    obstacles=unary_union([l['shape'] for l in lands if l['layer']=='B' and l['net']!='RET_'+pol])
    half=box(-60,-30,60,-.1) if pol=='A' else box(-60,.1,60,30)
    grounds[pol]=unary_union(ground).intersection(half).difference(obstacles.buffer(.2,join_style='mitre'))
    signals[pol]=unary_union(signal);inputs.append(dict(name=pol,x=p,y=yl,sig='SIG_'+pol,ret='RET_'+pol))
mirror=lambda s:scale(s,xfact=1,yfact=-1,origin=(0,0))
common=grounds['A'].intersection(mirror(grounds['B']));grounds={'A':common,'B':mirror(common)}
sym=dict(sinal_A_vs_B_espelhado_mm2=signals['A'].symmetric_difference(mirror(signals['B'])).area,
    retorno_A_vs_B_espelhado_mm2=grounds['A'].symmetric_difference(mirror(grounds['B'])).area,
    comprimentos_ramos_mm=[t['comprimento_mm'] for t in traces],escopo='Novos divisores e retornos espelhados em Y=0; quatro ramos de mesmo comprimento; transicoes dos radiadores originais preservadas.')
assert sym['sinal_A_vs_B_espelhado_mm2']<1e-8 and sym['retorno_A_vs_B_espelhado_mm2']<1e-8
assert max(sym['comprimentos_ramos_mm'])-min(sym['comprimentos_ramos_mm'])<1e-10
for pol in 'AB':
    ip=next(x for x in inputs if x['name']==pol);pt=Point(ip['x'],ip['y'])
    gr=grounds[pol].intersection(Polygon(outline).buffer(-.2)).difference(pt.buffer(1.516,quad_segs=96))
    lands += [dict(layer='F',net='SIG_'+pol,shape=signals[pol]),dict(layer='B',net='RET_'+pol,shape=gr),dict(layer='B',net='SIG_'+pol,shape=pt.buffer(.8,quad_segs=48).difference(pt.buffer(.55,quad_segs=48)))]
merged=[]
for layer,net in sorted({(l['layer'],l['net']) for l in lands}):
    sh=set_precision(unary_union([l['shape'] for l in lands if l['layer']==layer and l['net']==net]),1e-6).simplify(1e-6,preserve_topology=True)
    assert sh.is_valid and Polygon(outline).contains(sh),(layer,net)
    merged.append(dict(layer=layer,net=net,shape=sh))
clear=100.;shorts=[]
for i,a in enumerate(merged):
    for b in merged[i+1:]:
        if a['layer']!=b['layer']:continue
        clear=min(clear,a['shape'].distance(b['shape']))
        if a['shape'].intersection(b['shape']).area>1e-8:shorts.append((a['net'],b['net']))
assert not shorts and clear>=.15-1e-5,(shorts,clear)
g=dict(radiadores=2,centros_HFSS_X_mm=centers,passo_vertical_mm=48.,outline=outline,placa_largura_altura_mm=[50.,88.],distancia_pcb_refletor_mm=14.949,nucleo_mm=.76,cobre_mm=.035,inputs=inputs,vias=vias,lines=lines,traces=traces,simetria=sym,folga_planar_minima_mm=clear,shorts=shorts,
    transformador_mm=dict(largura=w70,comprimento=l70),
    fonte_C12=str(SRC),fonte_radiador_sha256=hashlib.sha256(artfile.read_bytes()).hexdigest(),
    topologia='1:2 por polarizacao derivado das etapas locais C12; transformadores parametrizados em transformador_mm; retorno6mm; sem raiz1:4 nem meandros assimetricos; sem resistores de isolamento.',
    limites='Geometria inicial simetrica; nao pressupor casamento/fase eletrica validada antes do HFSS.',
    lands=[dict(layer=l['layer'],net=l['net'],geometry=mapping(l['shape'])) for l in merged])
(OUT/'geometria.json').write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'simetria.json').write_text(json.dumps(sym,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
code=(SRC/'criar_cad.py').read_text(encoding='utf-8');old="root=Path('D:/dev/EMBRAER/P2M21/R13_Casamento_Banda/c12_raiz_intermediaria')";assert old in code
code=code.replace(old,'root=Path('+repr(OUT.as_posix())+')').replace("'4_elementos.FCStd'","'2_elementos_simetrica.FCStd'").replace("'Quatro_Elementos'","'Dois_Elementos_Simetricos'")
(OUT/'criar_cad.py').write_text(code,encoding='utf-8')
def patch(poly,ax,color):
    if poly.geom_type=='MultiPolygon':
        for part in poly.geoms:patch(part,ax,color)
        return
    from shapely.geometry.polygon import orient
    poly=orient(poly,sign=1);v=[];codes=[]
    for ring in [poly.exterior]+list(poly.interiors):
        pts=list(ring.coords);v += [(y,x) for x,y in pts];codes += [MP.MOVETO]+[MP.LINETO]*(len(pts)-2)+[MP.CLOSEPOLY]
    ax.add_patch(PathPatch(MP(v,codes),fc=color,ec='none'))
fig,axs=plt.subplots(1,2,figsize=(8,7))
for ax,layer in zip(axs,'FB'):
    ax.add_patch(plt.Rectangle((-25,-44),50,88,fc='#eef1ed',ec='black'))
    for l in merged:
        if l['layer']==layer:patch(l['shape'],ax,'#176a9b' if l['net']=='SIG_A' else '#d17b26' if l['net']=='SIG_B' else '#6c8589')
    ax.set(xlim=(-27,27),ylim=(-46,46),aspect='equal',title=layer+'.Cu',xlabel='Y horizontal (mm)',ylabel='X vertical (mm)');ax.grid(alpha=.15)
fig.suptitle('P2S13 — nova placa de dois elementos\nDivisores 1:2 e retornos simetricos derivados das etapas locais C12\n50 x 88 mm | passo48 mm | RO4350B0,76 mm | ainda nao validada',fontsize=11)
fig.tight_layout(rect=(0,0,1,.87));fig.savefig(OUT/'layout.png',dpi=170);plt.close(fig)
print(json.dumps(dict(pasta=str(OUT),simetria=sym,folga_mm=clear)))
