"""Vistas tecnicas renderizadas a partir dos solidos FreeCAD, sem imagem sintetica."""
from pathlib import Path
import os,json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
root=Path(os.environ['P2S13_ROOT']);data=json.loads((root/'visualizacao_local.json').read_text());out=root/'imagens';out.mkdir(exist_ok=True)
colors={'AL5052':'#b6bfcb','RO4350B_R01':'#b4a568','ZYF300':'#8bbd9c','copper':'#d89a41','folha_cu':'#dcb25e','PTFE_terminal':'#ecece3','SAC305':'#b9bfc8','Isola_370HR_nominal':'#bed6cb'}
for mode,elev,azim in [('montagem',20,-35),('traseira',-23,35),('radome',22,-45)]:
    fig=plt.figure(figsize=(12,6));ax=fig.add_subplot(111,projection='3d')
    triangles=[];rgba=[]
    for obj in data:
        if mode!='radome' and obj['nome']=='Radome_FR4_2mm':continue
        p=np.asarray(obj['vertices']);tri=np.asarray(obj['triangulos']);alpha=.15 if obj['nome']=='Radome_FR4_2mm' else 1
        triangles.extend(p[tri]);rgba.extend([matplotlib.colors.to_rgba(colors[obj['material']],alpha)]*len(tri))
    col=Poly3DCollection(triangles,facecolors=rgba,linewidths=0,shade=True,lightsource=matplotlib.colors.LightSource(azdeg=20,altdeg=45));ax.add_collection3d(col)
    ax.set(xlim=(-160,160),ylim=(-44,44),zlim=(-50,40),xlabel='X / vertical (mm)',ylabel='Y / horizontal (mm)',zlabel='Z / frontal (mm)');ax.set_box_aspect((320,88,90));ax.view_init(elev=elev,azim=azim);ax.grid(False)
    ax.set_title({'montagem':'R11 — montagem sem a tampa, para inspecao','traseira':'R11 — divisor e seis cabos na parte traseira','radome':'R11 — radome FR-4 de 2 mm (transparente nesta vista)'}[mode])
    fig.text(.5,.025,'Modelo nominal FreeCAD | 3 placas × 2 elementos | refletor 28,5 mm / 150° | duas entradas em fase',ha='center',fontsize=9);fig.tight_layout();fig.savefig(out/(mode+'.png'),dpi=160);plt.close(fig)
print(out)
