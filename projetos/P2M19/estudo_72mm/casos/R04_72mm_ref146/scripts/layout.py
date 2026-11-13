"""Geometria e estimativa por campos complexos C12; nao substitui o painel FEM."""
from pathlib import Path
import json,sys,csv,os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch,Rectangle
from matplotlib.path import Path as MplPath
from shapely.geometry import shape
from shapely.geometry.polygon import orient
REPO=Path('D:\\dev\\EMBRAER\\emb_ant')
sys.path.insert(0,str(REPO/'automacao/r05'))
from rede_carregada import read_pattern,beam
ROOT=Path('D:/dev/EMBRAER/P2M19/R04_72mm_ref146')
cfg=json.loads((ROOT/'configuracao.json').read_text());source=Path(cfg['fonte'])
g=json.loads((source/'geometria.json').read_text());result={}

def draw_face(ax,layer):
    rw,rh,_=cfg['refletor_mm'];ax.add_patch(Rectangle((-rw/2,-rh/2),rw,rh,facecolor='#dce1e6',edgecolor='#555'))
    for c in cfg['celulas']:
        ax.add_patch(Rectangle((c['y']-35,c['x']-92),70,184,facecolor='#f4e8c5',edgecolor='#786b44',lw=.7))
        for land in g['lands']:
            if land['layer']!=layer:continue
            geo=shape(land['geometry']);polys=[geo] if geo.geom_type=='Polygon' else list(geo.geoms)
            for poly in polys:
                poly=orient(poly,sign=1);verts=[];codes=[]
                for ring in [poly.exterior,*poly.interiors]:
                    xy=[(y+c['y'],x+c['x']) for x,y in ring.coords]
                    verts.extend(xy);codes.extend([MplPath.MOVETO]+[MplPath.LINETO]*(len(xy)-2)+[MplPath.CLOSEPOLY])
                ax.add_patch(PathPatch(MplPath(verts,codes),facecolor='#ad651b',edgecolor='none'))
        ax.text(c['y'],c['x']+83,c['nome'],ha='center',fontsize=8)
        for p in g['inputs']:
            ax.plot(p['y']+c['y'],p['x']+c['x'],'o',ms=2.5,mfc='white',mec='#222',mew=.4)
    ax.set_aspect('equal');ax.set_xlim(-rw/2-14,rw/2+14);ax.set_ylim(-rh/2-12,rh/2+12)
    ax.set_xlabel('Horizontal Y HFSS [mm]');ax.set_ylabel('Vertical X HFSS [mm]')
for layers,filename in [('F','montagem_frontal.png'),('FB','montagem_duas_faces.png')]:
    fig,axs=plt.subplots(1,len(layers),figsize=(6.6*len(layers),12),squeeze=False)
    for layer,ax in zip(layers,axs[0]):
        draw_face(ax,layer);ax.set_title('Cobre '+('superior (F.Cu)' if layer=='F' else 'inferior (B.Cu), projetado na vista frontal'))
    fig.suptitle(f"{cfg['revisao']} — {len(cfg['celulas'])} PCBs / {cfg['radiadores']} radiadores"+ ('\n' if len(layers)==1 else ' — ')+f"{cfg['niveis_radiadores']} niveis × 2 colunas | {len(cfg['portas'])} conexoes")
    fig.text(.5,.025,f"Passos: 48 mm vertical / {cfg['passo_horizontal_mm']} mm horizontal\nPlacas: {cfg['niveis_placas']} × 2, centros verticais a 192 mm; refletor comum {cfg['refletor_mm'][0]} × {cfg['refletor_mm'][1]} mm",ha='center',fontsize=10)
    fig.tight_layout(rect=(0,.07,1,.95));fig.savefig(ROOT/filename,dpi=180);plt.close(fig)
print('LAYOUT_EXPORTADO')
