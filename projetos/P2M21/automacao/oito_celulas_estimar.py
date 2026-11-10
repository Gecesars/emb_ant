"""Geometria e estimativa por campos complexos C12; nao substitui o painel FEM."""
from pathlib import Path
import json,sys,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch,Rectangle
from matplotlib.path import Path as MplPath
from shapely.geometry import shape
from shapely.geometry.polygon import orient
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'automacao/r05'))
from rede_carregada import read_pattern,beam
ROOT=Path('D:/dev/EMBRAER/P2M21/R14_Oito_Celulas')
cfg=json.loads((ROOT/'configuracao.json').read_text());source=Path(cfg['fonte'])
g=json.loads((source/'geometria.json').read_text());result={}
fig,axs=plt.subplots(1,2,figsize=(11,5))
for axis,ax in zip('HV',axs):
    theta,e=read_pattern(source/('AB_'+axis+'.csv'))
    offsets=np.array([c['y' if axis=='H' else 'x'] for c in cfg['celulas']])/1000
    af=np.exp(1j*2*np.pi*5.17e9/299792458*np.sin(np.deg2rad(theta))[:,None]*offsets).sum(axis=1)/np.sqrt(8)
    field=e*af[:,None];gain=10*np.log10(np.maximum(np.sum(abs(field)**2,axis=1),1e-30))
    front=np.flatnonzero(abs(theta)<=90);peak=front[np.argmax(gain[front])]
    width,left,right=beam(theta,gain)
    result[axis]=dict(ganho_frontal_dBi=float(gain[np.argmin(abs(theta))]),pico_graus=float(theta[peak]),abertura_graus=float(width))
    with (ROOT/('estimativa_'+axis+'.csv')).open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['theta_deg','gain_dBi']);w.writerows(zip(theta,gain))
    ax.plot(theta,gain,label='Oito celulas isoladas + fator de arranjo')
    ax.set(xlim=(-90,90),ylim=(-20,24),xlabel='Angulo (graus)',ylabel='Ganho estimado (dBi)',title=axis);ax.grid(alpha=.25)
fig.suptitle('Estimativa inicial SEM acoplamento entre celulas — 5,17 GHz\n16 portas iguais / 0 graus, 1 W total; nao e resultado do painel FEM')
fig.tight_layout(rect=(0,0,1,.88));fig.savefig(ROOT/'estimativa_inicial.png',dpi=160);plt.close(fig)
(ROOT/'estimativa.json').write_text(json.dumps(dict(metodo='Campos complexos da C12 isolada x AF / sqrt(8); sem acoplamento entre celulas, sem efeito do novo refletor comum.',validacao=False,cortes=result),ensure_ascii=False,indent=2)+'\n')

def draw_face(ax,layer):
    ax.add_patch(Rectangle((-81,-388),162,776,facecolor='#dce1e6',edgecolor='#555'))
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
    ax.set_aspect('equal');ax.set_xlim(-95,95);ax.set_ylim(-400,400)
    ax.set_xlabel('Horizontal Y HFSS [mm]');ax.set_ylabel('Vertical X HFSS [mm]')
for layers,filename in [('F','montagem_frontal.png'),('FB','montagem_duas_faces.png')]:
    fig,axs=plt.subplots(1,len(layers),figsize=(6.6*len(layers),12),squeeze=False)
    for layer,ax in zip(layers,axs[0]):
        draw_face(ax,layer);ax.set_title('Cobre '+('superior (F.Cu)' if layer=='F' else 'inferior (B.Cu), projetado na vista frontal'))
    fig.suptitle('R14 — oito PCBs C12 / 32 radiadores'+ ('\n' if len(layers)==1 else ' — ')+'16 niveis × 2 colunas | 16 conexoes')
    fig.text(.5,.025,'Passos: 48 mm vertical / 72 mm horizontal\nPlacas: 4 × 2, centros verticais a 192 mm; refletor comum 162 × 776 mm',ha='center',fontsize=10)
    fig.tight_layout(rect=(0,.07,1,.95));fig.savefig(ROOT/filename,dpi=180);plt.close(fig)
print(json.dumps(result,indent=2))
