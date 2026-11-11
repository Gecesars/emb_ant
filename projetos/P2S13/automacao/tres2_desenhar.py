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
ROOT=Path('D:/dev/EMBRAER/P2S13/R05_Tres_Placas2')
selected='t00_b3_a90'
if (ROOT/'comparacao.json').exists():
    results=json.loads((ROOT/'comparacao.json').read_text())['resultados'];selected=min(results,key=lambda r:abs(r['erro_H_frente_100_graus']))['caso']
cfg=json.loads((ROOT/selected/'configuracao.json').read_text())
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
    # Projecao frontal: acima de90graus o extremo fica no arco, nao na ponta retornada.
    half=max(b+4*math.sin(min(alpha,math.pi/2)),b+4*math.sin(alpha)+tail*math.cos(alpha))
    ax.add_patch(Rectangle((-half,-148),2*half,296,fc='#dfe1e4',ec='#999'))
    for c in cfg['celulas']:
        g=json.loads((Path(c['fonte'])/'geometria.json').read_text());o=np.array(g['outline']);xmin,xmax=o[:,0].min()+c['x'],o[:,0].max()+c['x'];ymin,ymax=o[:,1].min(),o[:,1].max()
        ax.add_patch(Rectangle((ymin,xmin),ymax-ymin,xmax-xmin,fc='#eff2e9',ec='#405b3a',lw=1.2))
        for l in g['lands']:
            if l['layer']==layer:patch(translate(shape(l['geometry']),xoff=c['x']),ax,'#176a9b' if l['net']=='SIG_A' else '#d17b26' if l['net']=='SIG_B' else '#718584')
        for p in g['inputs']:ax.plot(p['y'],p['x']+c['x'],'o',mfc='white',mec='black',ms=3)
        ax.text(0,xmax+3,'%d elementos'%c['radiadores'],ha='center',fontsize=9)
    for b in [-cfg['inicio_dobra_y_mm'],cfg['inicio_dobra_y_mm']]:ax.axvline(b,c='#a45a29',ls='--',lw=.8)
    ax.set(aspect='equal',xlim=(-50,50),ylim=(-154,154),xlabel='Y horizontal (mm)',ylabel='X vertical (mm)',title=layer+'.Cu — três PCBs2 idênticas');ax.grid(alpha=.12)
ax=axs[2]
for idx,path in enumerate(sorted(ROOT.glob('t*/configuracao.json'))):
    name=path.parent.name;color=plt.get_cmap('tab10')(idx)
    c=json.loads((ROOT/name/'configuracao.json').read_text());b=c['inicio_dobra_y_mm'];a=math.radians(c['angulo_dobra_graus']);r=4;tail=45-b-a*2.8;t=np.linspace(0,a,60)
    yr=np.r_[0,b+r*np.sin(t),b+r*math.sin(a)+tail*math.cos(a)];zr=np.r_[0,-r+r*np.cos(t),-r+r*math.cos(a)-tail*math.sin(a)]
    ax.plot(np.r_[-yr[::-1],yr[1:]],np.r_[zr[::-1],zr[1:]],c=color,lw=2.4 if name==selected else 1.2,alpha=1 if name==selected else .65,label='b=%g mm / %g graus'%(b,c['angulo_dobra_graus']))
ax.plot([-25,25],[14.949,14.949],c='#365c36',lw=4,label='Todas as PCBs: 50 mm')

for y in [-18,18]:ax.plot([y,y],[-35.051,14.949],ls=':',c='#555',lw=.8)
ax.annotate('Frente +Z',xy=(0,38),xytext=(0,27),ha='center',arrowprops={'arrowstyle':'->'})
ax.set(aspect='equal',xlim=(-50,50),ylim=(-48,42),xlabel='Y (mm)',ylabel='Z (mm)',title='Seção: face externa dos refletores');ax.grid(alpha=.2)
ax.legend(loc='lower right',fontsize=8)
fig.suptitle('P2S13 — três placas idênticas de dois elementos, seis níveis\nPasso 48 mm | vão entre placas 8 mm | Al 2 mm, comprimento 296 mm | seis cabos de 50 mm\nSeis entradas de 1/6 W a 0°; 1 W total. Alvo horizontal 100°. Desenho preliminar.\nRefletor frontal exibido: b=%g mm / %g graus.'%(cfg['inicio_dobra_y_mm'],cfg['angulo_dobra_graus']),fontsize=12)
fig.tight_layout(rect=(0,.05,1,.89));fig.savefig(ROOT/'montagem_tres_placas.png',dpi=170);plt.close(fig)
print('VISTAS_GERADAS')
