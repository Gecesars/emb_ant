"""Figura de cobre derivada da configuracao; nao altera CAD/nativo."""
from pathlib import Path
import os,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
ROOT=Path(os.environ['P2S13_DIV3_ROOT']);c=json.loads((ROOT/'configuracao.json').read_text())
fig,ax=plt.subplots(figsize=(12,4.7));ax.add_patch(Rectangle((-110,-32),220,64,color='#e3e8dd'))
for pol,shape in c['signals'].items():
    pts=shape['exterior'];ax.fill([p[0] for p in pts],[p[1] for p in pts],color='#bb7b28')
    for hole in shape['holes']:ax.fill([p[0] for p in hole],[p[1] for p in hole],color='#e3e8dd')
if c.get('mask_windows'):
    for l,r in c['mask_windows']['x_relative_to_center_mm']:
        ax.add_patch(Rectangle((2.50916841304+l,-32),r-l,64,color='#237a4a',alpha=.32))
if c.get('shield'):
    ax.add_patch(Rectangle((-111,-33),222,66,fill=False,color='#315b87',ls='--',lw=1.4))
for p in c['portas']:
    ax.plot(p['x'],p['y'],'o',ms=3,color='navy')
    ax.annotate(p['name'],(p['x'],p['y']),xytext=(0,6 if p['y']>0 else -13),textcoords='offset points',ha='center',fontsize=8)
qs=[t for t in c['traces'] if t['name'].startswith('A_Q')]
os=[t for t in c['traces'] if t['name'].startswith('A_O')]
foot='Transformadores Q1/Q2/Q3: '+ ' / '.join('%.3f mm'%t['width_mm'] for t in qs)
foot+=' | Saídas O1/O2/O3: '+' / '.join('%.3f mm'%t['length_mm'] for t in os)
title=ROOT.name+' — divisor duplo 1:3 — PCB 220 × 64 mm'
subtitle='ZYF300CA-C 1,52 mm; Cu 35 µm; duas polarizações A/B espelhadas'
if c.get('shield'):subtitle+=' | tampa retirada da vista; folga %.1f mm'%c['shield']['gap_above_copper_mm']
ax.set(xlim=(-114,114),ylim=(-36,36),xlabel='X longitudinal da antena (mm)',ylabel='Y (mm)',title=title+'\n'+subtitle)
ax.set_aspect('equal');fig.text(.5,.025,foot,ha='center',fontsize=8)
fig.tight_layout(rect=(0,.055,1,1));fig.savefig(ROOT/'layout.png',dpi=180);plt.close(fig)
