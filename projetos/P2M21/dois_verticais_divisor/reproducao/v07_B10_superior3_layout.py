"""Placa de dois radiadores verticais e dois divisores impressos, sem solver."""
from pathlib import Path
import json, math
import numpy as np
from shapely.geometry import Polygon,Point,LineString,mapping
from shapely.affinity import translate
from shapely.ops import unary_union
from shapely import set_precision
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MP

repo=Path(__file__).resolve().parents[3]
root=Path('D:\\dev\\EMBRAER\\P2M21\\R09_Divisor_Simetria')
art=json.loads((repo/'automacao/P1H/KiCad_Antenas/elemento_hfss.json').read_text())
old=json.loads(Path('D:/dev/EMBRAER/P2M21/R06_Integrada_1x2/geometria.json').read_text())
lines=old['lines'];w50=lines['50']['w_mm'];w70=lines[str(math.sqrt(2)*50)]['w_mm'];l70=lines[str(math.sqrt(2)*50)]['l90_mm']
p=art['ports']['B'][0]

def patch(poly,ax,color):
    if poly.geom_type=='MultiPolygon':
        for x in poly.geoms:patch(x,ax,color)
        return
    from shapely.geometry.polygon import orient
    poly=orient(poly,sign=1);vs=[];codes=[]
    for r in [poly.exterior]+list(poly.interiors):
        pts=np.asarray(r.coords);vs.extend(pts[:,[1,0]]);codes.extend([MP.MOVETO]+[MP.LINETO]*(len(pts)-2)+[MP.CLOSEPOLY])
    ax.add_patch(PathPatch(MP(vs,codes),fc=color,ec='none'))

for pitch in [48.]:
    dest=root/'v07_B10_superior3';dest.mkdir(exist_ok=True)
    lands=[];traces=[];inputs=[];vias=[]
    for i,cx in enumerate([-pitch/2,pitch/2],1):
        for land in art['lands']:
            net=land['net'] if land['net'] in ('SIG_A','SIG_B','RET_A','RET_B') else 'E%d_'%i+land['net']
            lands.append(dict(layer=land['layer'],net=net,shape=translate(Polygon(land['outer'],land['holes']),cx,0)))
        vias.extend([[x+cx,y] for x,y in art['vias']])
    for pol in 'AB':
        tx,ty=(p,-18.) if pol=='A' else (p,18.)
        signal=[Point(tx,ty).buffer(.95,quad_segs=24)];ret=[Point(tx,ty).buffer(2.65,quad_segs=24)]
        for sign in [-1,1]:
            cx=sign*pitch/2
            pts70=[(tx,ty),(tx+sign*l70,ty)]
            depth=(10.0/2 if pol=='B' else 0.)+(3.0/2 if sign>0 else 0.0/2)
            if depth>0:
                ym=ty+(depth if pol=='B' else -depth)
                pts50=[pts70[-1],(tx+sign*(l70+1),ty),(tx+sign*(l70+1),ym),
                    (tx+sign*(l70+5),ym),(tx+sign*(l70+5),ty),(cx+p,ty),(cx+p,-p if pol=='A' else p)]
            else:pts50=[pts70[-1],(cx+p,ty),(cx+p,-p if pol=='A' else p)]
            pts=pts70+pts50[1:]
            signal.extend([LineString(pts70).buffer(w70/2,cap_style='square',join_style='mitre'),LineString(pts50).buffer(w50/2,cap_style='square',join_style='mitre')])
            ret.append(LineString(pts).buffer(1.8,cap_style='round',join_style='mitre',quad_segs=20))
            traces.append(dict(polarizacao=pol,elemento=1 if sign<0 else 2,linha70=pts70,linha50=pts50,comprimento_mm=LineString(pts).length))
        ground=unary_union(ret).difference(Point(tx,ty).buffer(1.516,quad_segs=48))
        obstacles=unary_union([l['shape'] for l in lands if l['layer']=='B' and l['net']!='RET_'+pol])
        ground=ground.difference(obstacles.buffer(.2,join_style='mitre'))
        ground=ground.intersection(Polygon([[-pitch/2-14.8,-21],[pitch/2+20,-21],[pitch/2+20,28],[-pitch/2-14.8,28]]).buffer(-.2))
        lands.extend([dict(layer='F',net='SIG_'+pol,shape=unary_union(signal)),dict(layer='B',net='RET_'+pol,shape=ground),
          dict(layer='B',net='SIG_'+pol,shape=Point(tx,ty).buffer(.8,quad_segs=32).difference(Point(tx,ty).buffer(.55,quad_segs=32)))])
        inputs.append(dict(name=pol,x=tx,y=ty,sig='SIG_'+pol,ret='RET_'+pol))
    merged=[]
    for layer,net in sorted(set((l['layer'],l['net']) for l in lands)):
        s=set_precision(unary_union([l['shape'] for l in lands if l['layer']==layer and l['net']==net]),1e-6).simplify(1e-6,preserve_topology=True)
        merged.append(dict(layer=layer,net=net,shape=s))
    shorts=[];near=[];clear=100.
    for i,a in enumerate(merged):
        for b in merged[i+1:]:
            if a['layer']!=b['layer'] or a['net']==b['net']:continue
            distance=a['shape'].distance(b['shape']);clear=min(clear,distance)
            if distance<.15-1e-6:near.append([a['net'],b['net'],distance])
            if a['shape'].intersection(b['shape']).area>1e-8:shorts.append([a['layer'],a['net'],b['net']])
    outline=[[-pitch/2-14.8,-21],[pitch/2+20,-21],[pitch/2+20,28],[-pitch/2-14.8,28]]
    inside=all(Polygon(outline).contains(l['shape']) for l in merged)
    g=dict(pitch=pitch,outline=outline,lands=[dict(layer=l['layer'],net=l['net'],geometry=mapping(l['shape'])) for l in merged],
      inputs=inputs,vias=vias,traces=traces,lines=lines,h=.76,cu=.035,refletor_z=0,pcb_z=16.61,
      cabo=dict(tipo='coaxial semirrigido nominal UT141',comprimento_reto_mm=50,raio_vivo_mm=.45975,raio_interno_blindagem_mm=1.515,raio_externo_mm=1.7905,
        epsilon=2.036363533774732,tand=.00027683054882040843,limite='Cabo de ensaio reto, sem conector N; perdas nominais fisicas incluidas.'),
      verificacao=dict(shorts=shorts,folga_minima_mm=clear,abaixo_015=near,cobre_dentro_contorno=inside,comprimentos=[t['comprimento_mm'] for t in traces]))
    (dest/'geometria.json').write_text(json.dumps(g,indent=2)+'\n',encoding='utf-8')
    fig,axs=plt.subplots(1,2,figsize=(8,8))
    for ax,layer in zip(axs,['F','B']):
        ax.set_facecolor('#eef4f4')
        for l in merged:
            if l['layer']==layer:patch(l['shape'],ax,'#b57f33' if 'SIG' in l['net'] else '#6a8b93')
        for ip in inputs:ax.text(ip['y'],ip['x']+2,ip['name'],ha='center',fontsize=10);ax.add_patch(plt.Circle((ip['y'],ip['x']),.55,color='white'))
        ax.set_xlim(-21,28);ax.set_ylim(outline[0][0],outline[2][0]);ax.set_aspect('equal');ax.set_title(layer+'.Cu');ax.set_xlabel('Y (mm)');ax.set_ylabel('X vertical (mm)')
    fig.suptitle('Dois elementos verticais | d = %g mm\nDois divisores 1:2 impressos e duas entradas'%pitch)
    fig.tight_layout();fig.savefig(dest/'layout.png',dpi=170);plt.close(fig)
    print(pitch,g['verificacao'])
    assert not shorts and inside and not near,'Revisar roteamento'
