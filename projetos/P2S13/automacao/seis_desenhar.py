"""Vistas dimensionais a partir dos mesmos poligonos das PCBs, sem sintese de imagem."""
from pathlib import Path
import json,math
import numpy as np
from shapely.geometry import shape
from shapely.geometry.polygon import orient
from shapely.affinity import translate
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MP
from matplotlib.patches import PathPatch,Rectangle
ROOT=Path('D:/dev/EMBRAER/P2S13/R01_Seis_Elementos');cfg=json.loads((ROOT/'s00_b20_a60/configuracao.json').read_text())
def patch(poly,ax,color):
    if poly.geom_type=='MultiPolygon':
        for part in poly.geoms:patch(part,ax,color)
        return
    poly=orient(poly,sign=1);v=[];codes=[]
    for ring in [poly.exterior]+list(poly.interiors):
        pts=list(ring.coords);v += [(y,x) for x,y in pts];codes += [MP.MOVETO]+[MP.LINETO]*(len(pts)-2)+[MP.CLOSEPOLY]
    ax.add_patch(PathPatch(MP(v,codes),fc=color,ec='none'))
fig,axs=plt.subplots(1,3,figsize=(13,9),gridspec_kw={'width_ratios':[.8,.8,1.3]})
for ax,layer in zip(axs[:2],'FB'):
    alpha=math.radians(cfg['angulo_dobra_graus']);b=cfg['inicio_dobra_y_mm'];tail=45-b-alpha*2.8
    half=b+4*math.sin(alpha)+tail*math.cos(alpha)
    ax.add_patch(Rectangle((-half,-148),2*half,296,fc='#dfe1e4',ec='#999'))
    for c in cfg['celulas']:
        g=json.loads((Path(c['fonte'])/'geometria.json').read_text());o=np.array(g['outline']);xmin,xmax=o[:,0].min()+c['x'],o[:,0].max()+c['x'];ymin,ymax=o[:,1].min(),o[:,1].max()
        ax.add_patch(Rectangle((ymin,xmin),ymax-ymin,xmax-xmin,fc='#eff2e9',ec='#405b3a',lw=1.2))
        for l in g['lands']:
            if l['layer']==layer:patch(translate(shape(l['geometry']),xoff=c['x']),ax,'#176a9b' if l['net']=='SIG_A' else '#d17b26' if l['net']=='SIG_B' else '#718584')
        for p in g['inputs']:ax.plot(p['y'],p['x']+c['x'],'o',mfc='white',mec='black',ms=3)
        ax.text(0,xmax+3,'%d elementos'%c['radiadores'],ha='center',fontsize=9)
    for b in [-20,20]:ax.axvline(b,c='#a45a29',ls='--',lw=.8)
    ax.set(aspect='equal',xlim=(-50,50),ylim=(-154,154),xlabel='Y horizontal (mm)',ylabel='X vertical (mm)',title=layer+'.Cu — refletor b20/60');ax.grid(alpha=.12)
ax=axs[2]
for name,color in [('s00_b20_a60','#aa592a'),('s01_b20_a90','#346c9d'),('s02_b10_a90','#8b5199')]:
    c=json.loads((ROOT/name/'configuracao.json').read_text());b=c['inicio_dobra_y_mm'];a=math.radians(c['angulo_dobra_graus']);r=4;tail=45-b-a*2.8;t=np.linspace(0,a,60)
    yr=np.r_[0,b+r*np.sin(t),b+r*math.sin(a)+tail*math.cos(a)];zr=np.r_[0,-r+r*np.cos(t),-r+r*math.cos(a)-tail*math.sin(a)]
    ax.plot(np.r_[-yr[::-1],yr[1:]],np.r_[zr[::-1],zr[1:]],c=color,lw=2,label='b=%d mm / %d graus'%(b,c['angulo_dobra_graus']))
ax.plot([-35,35],[14.949,14.949],c='#365c36',lw=4,label='Placa4: 70 mm de largura')
ax.plot([-25,25],[16.5,16.5],c='#81a25f',lw=3,label='Placa2: 50 mm (deslocada na vista)')
for y in [-32,32,-18,18]:ax.plot([y,y],[-35.051,14.949],ls=':',c='#555',lw=.8)
ax.annotate('Frente +Z',xy=(0,38),xytext=(0,27),ha='center',arrowprops={'arrowstyle':'->'})
ax.set(aspect='equal',xlim=(-50,50),ylim=(-40,42),xlabel='Y (mm)',ylabel='Z (mm)',title='Secao do refletor — perfis em estudo');ax.grid(alpha=.2)
ax.legend(loc='upper center',bbox_to_anchor=(.5,-.15),fontsize=8)
fig.suptitle('P2S13 — seis niveis: placa4 C12 + placa2 com alimentacao simetrica\nPasso48 mm | vao entre placas8 mm | Al2 mm, comprimento296 mm | quatro cabos50 mm\nAs quatro entradas externas permanecem iguais e em fase. Desenho preliminar.',fontsize=12)
fig.tight_layout(rect=(0,.05,1,.89));fig.savefig(ROOT/'montagem_6elementos.png',dpi=170);plt.close(fig)
print('VISTAS_GERADAS')
