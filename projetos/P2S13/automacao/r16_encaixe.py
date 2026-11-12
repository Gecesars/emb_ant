"""Envoltoria conservadora a partir dos bounding boxes otimos do CAD."""
from pathlib import Path
import json,numpy as np
from scipy.optimize import minimize_scalar
from scipy.spatial import ConvexHull
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path('D:/dev/EMBRAER/P2S13/R16_Tubo_PVC')
rows=json.loads((ROOT/'envelopes_montagem.json').read_text());pts=[]
for item in rows:
 b=item['bbox'];pts += [(y,z) for y in [b[1],b[4]] for z in [b[2],b[5]]]
pts=np.unique(pts,axis=0);fit=json.loads((ROOT/'encaixe_preliminar.json').read_text());zc=fit['centro_z_mm']
f=lambda c:float(np.max(np.linalg.norm(pts-[0,c],axis=1)))
best=minimize_scalar(f,bounds=(-30,0),method='bounded',options={'xatol':1e-9})
assert abs(round(float(best.x),3)-zc)<1e-8 and abs(f(zc)-fit['raio_conservador_montagem_mm'])<1e-8
hull=pts[ConvexHull(pts).vertices]
fig,axs=plt.subplots(1,2,figsize=(10,6))
for ax,t in zip(axs,fit['tubos'][1:3]):
 ax.add_patch(plt.Circle((0,zc),t['De_mm']/2,fc='#c0c7ce',ec='#6b7681'))
 ax.add_patch(plt.Circle((0,zc),t['Di_mm']/2,fc='white',ec='#4082ae',lw=1.8))
 ax.fill(hull[:,0],hull[:,1],color='#536a55',alpha=.8,label='Envelope conservador da montagem')
 ax.plot(0,zc,'+',color='#c63b38',label='Eixo do tubo')
 ax.set_aspect('equal');ax.set_xlim(-82,82);ax.set_ylim(zc-82,zc+82);ax.grid(alpha=.2)
 ax.set(xlabel='Y (mm)',ylabel='Z (mm)',title=f"DN{t['DN']} | De {t['De_mm']:g} / e {t['parede_mm']:g} mm\nDi {t['Di_mm']:g} mm | folga ≥ {t['folga_radial_conservadora_mm']:.2f} mm")
fig.suptitle('Encaixe nominal no tubo PVC — projeção transversal\nInclui o divisor e os cabos da montagem mecânica; não inclui tampas')
handles,labels=axs[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.5,.01),ncol=2)
fig.tight_layout(rect=(0,.13,1,.9));fig.savefig(ROOT/'comparacao_encaixe.png',dpi=160)
print('ENCAIXE_CONSERVADOR_CONFERIDO')
