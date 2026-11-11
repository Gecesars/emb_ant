"""Desenha perfis fisicos do refletor, com cotas de inicio e angulo."""
from pathlib import Path
import json,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
ROOT=Path('D:/dev/EMBRAER/P2S13/R04_Dobras_Ajustadas')
files=[Path('D:/dev/EMBRAER/P2S13/R03_Continuacao_M00/configuracao.json')]+sorted(ROOT.glob('d*/configuracao.json'))
cols=min(3,len(files));rows=math.ceil(len(files)/cols)
fig,grid=plt.subplots(rows,cols,figsize=(4.5*cols,4.2*rows+1.5),sharex=True,sharey=True)
axs=np.atleast_1d(grid).ravel()
for ax,p in zip(axs,files):
    c=json.loads(p.read_text());a=math.radians(c['angulo_dobra_graus']);b=c['inicio_dobra_y_mm'];t=c['espessura_mm'];ri=c['raio_interno_mm'];ro=ri+t;tail=c['refletor_desenvolvido_largura_mm']/2-b-a*(ri+c['K_dobra']*t);theta=np.linspace(0,a,80)
    yo=np.r_[0,b+ro*np.sin(theta),b+ro*np.sin(a)+tail*np.cos(a)];zo=np.r_[0,-ro+ro*np.cos(theta),-ro+ro*np.cos(a)-tail*np.sin(a)]
    yi=np.r_[0,b+ri*np.sin(theta),b+ri*np.sin(a)+tail*np.cos(a)];zi=np.r_[-t,-ro+ri*np.cos(theta),-ro+ri*np.cos(a)-tail*np.sin(a)]
    for s in [-1,1]:ax.add_patch(Polygon(np.c_[np.r_[s*yo,s*yi[::-1]],np.r_[zo,zi[::-1]]],fc='#b5bcc3',ec='#39434b',lw=.8))
    ax.plot([-35,35],[14.949,14.949],c='#467146',lw=3,label='PCB4 70 mm')
    ax.plot([-25,25],[17,17],c='#8ba56f',lw=2,label='PCB2 50 mm (deslocada na vista)')
    for y in [-32,32,-18,18]:ax.plot([y,y],[-35.051,14.949],':',c='#777',lw=.8)
    ax.annotate('',xy=(b,4),xytext=(0,4),arrowprops={'arrowstyle':'<->','lw':.9});ax.text(b/2,6,'b=%g mm'%b,ha='center',fontsize=9)
    suffix=' — apenas CAD' if not (p.parent/'resultado.json').exists() else ''
    ax.set(aspect='equal',xlim=(-50,50),ylim=(-48,32),xlabel='Y horizontal (mm)',title=('b=%g mm | dobra %g°'%(b,c['angulo_dobra_graus']))+suffix);ax.grid(alpha=.2)
for i,ax in enumerate(axs):
    if i>=len(files):ax.set_visible(False)
    elif i%cols==0:ax.set_ylabel('Z frontal (mm)')
handles,labels=axs[0].get_legend_handles_labels();fig.legend(handles,labels,fontsize=8,loc='lower center',bbox_to_anchor=(.5,.02),ncol=2)
fig.suptitle('Cortes do refletor: abas dobradas para trás (−Z)\nAlumínio 2 mm | largura desenvolvida 90 mm | comprimento 296 mm | raio interno 2 mm',fontsize=12)
fig.tight_layout(rect=(0,.07,1,.91),h_pad=3.2,w_pad=1.8);fig.savefig(ROOT/'perfis_refletor.png',dpi=160);plt.close(fig)
