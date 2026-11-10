"""Geometria nominal do estudo, antes de qualquer conclusao RF."""
from pathlib import Path
import json,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
ROOT=Path('D:/dev/EMBRAER/P2S13/R00_Refletor_Dobrado')
fig,(ax,side)=plt.subplots(1,2,figsize=(12,8),gridspec_kw={'width_ratios':[.8,1.2]})
ax.add_patch(Rectangle((-45,-196),90,392,fc='#d8dde3',ec='#777'))
for x in [-96,96]:
    ax.add_patch(Rectangle((-35,x-92),70,184,fc='#e4eddf',ec='#51744b'))
    for dx in [-72,-24,24,72]:ax.plot(0,x+dx,'o',ms=7,c='#b17b34')
for b,c in [(20,'#b8582a'),(30,'#3276a3')]:
    for s in [-1,1]:ax.axvline(s*b,c=c,ls='--',lw=1)
ax.set(aspect='equal',xlim=(-65,65),ylim=(-210,210),xlabel='Horizontal Y (mm)',ylabel='Vertical X (mm)',title='Duas PCBs, uma acima da outra\nOito niveis; quatro entradas iguais/em fase');ax.grid(alpha=.15)
for tag,col in [('v00_plano','#888'),('v01_b20_a60','#b8582a'),('v02_b30_a60','#3276a3'),('v05_b20_a90_tau','#8c4ca5')]:
    if not (ROOT/tag/'configuracao.json').exists():continue
    cfg=json.loads((ROOT/tag/'configuracao.json').read_text());b=cfg['inicio_dobra_y_mm'];a=math.radians(cfg['angulo_dobra_graus']);R=4;tail=45-b-a*2.8
    if a==0:ys=np.array([-45,45]);zs=np.zeros(2)
    else:
        t=np.linspace(0,a,80);yr=np.r_[0,b+R*np.sin(t),b+R*math.sin(a)+tail*math.cos(a)];zr=np.r_[0,-R+R*np.cos(t),-R+R*math.cos(a)-tail*math.sin(a)]
        ys=np.r_[-yr[::-1],yr[1:]];zs=np.r_[zr[::-1],zr[1:]]
    side.plot(ys,zs,c=col,lw=2,label='Plano' if a==0 else f"b={b:g} mm; angulo={cfg['angulo_dobra_graus']:g} graus")
side.plot([-35,35],[14.949,14.949],c='#3c764c',lw=4,label='PCB, face inferior do nucleo')
for y in [-32,32]:side.plot([y,y],[-35.051,14.949],c='#444',ls=':',lw=1.5,label='Eixos dos cabos' if y==32 else None)
side.annotate('Frente +Z',xy=(0,36),xytext=(0,25),ha='center',arrowprops={'arrowstyle':'->'})
side.set(aspect='equal',xlim=(-55,55),ylim=(-40,40),xlabel='Y (mm)',ylabel='Z (mm)',title='Face frontal do refletor em secao\nb = inicio da dobra medido do eixo central')
side.legend(loc='upper center',bbox_to_anchor=(.5,-.13),ncol=2,fontsize=8);side.grid(alpha=.2)
fig.suptitle('P2S13 — geometrias preliminares de estudo, sem liberacao para fabricacao\nAluminio 2 mm; Ri=2 mm; largura desenvolvida 90 mm; altura 392 mm')
fig.tight_layout(rect=(0,.06,1,.92));fig.savefig(ROOT/'geometria_estudo.png',dpi=180,bbox_inches='tight',pad_inches=.25);plt.close(fig)
print('GEOMETRIA_ESTUDO_DESENHADA')
