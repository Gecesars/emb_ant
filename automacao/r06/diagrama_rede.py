"""Diagrama funcional do circuito separado; nao representa um novo calculo RF."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path)
root=parser.parse_args().root
input_mm,trunk_mm,branch_mm=json.loads((root/'configuracao_circuito.json').read_text(encoding='utf8'))['comprimentos_mm']
fig,ax=plt.subplots(figsize=(10,8));ax.set(xlim=(0,10),ylim=(0,8));ax.axis('off')
navy='#13374b';blue='#176e93'
def box(x,y,w,h,text,face='#eef4f7',edge=blue,size=11):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.04,rounding_size=0.06',
                              linewidth=1.5,edgecolor=edge,facecolor=face))
    ax.text(x+w/2,y+h/2,text,ha='center',va='center',color=navy,fontsize=size)
def arrow(points,color=blue):
    for a,b in zip(points[:-2],points[1:-1]):ax.plot([a[0],b[0]],[a[1],b[1]],color=color,lw=1.5)
    ax.add_patch(FancyArrowPatch(points[-2],points[-1],arrowstyle='-|>',mutation_scale=12,color=color,lw=1.5))
box(.3,6.8,2.5,.8,'N_A e N_B\n0,5 W / 0° em cada entrada')
box(3.35,6.8,2.25,.8,'Duas bobinas\nS2_A e S2_B')
arrow([(2.8,7.2),(3.35,7.2)])
box(.45,3.0,4.5,3.1,'',face='#eaf2f8')
ax.text(2.7,5.8,'PCB INFERIOR · S18 completo',ha='center',fontsize=12,color=navy,weight='bold')
box(.9,4.65,3.6,.75,'RA / RB: divisão 1:2',face='white')
box(.9,3.25,3.6,.75,'A / B: divisão 1:5',face='white')
arrow([(4.47,6.8),(4.47,6.4),(.7,6.4),(.7,5.025),(.9,5.025)])
arrow([(2.1,4.65),(2.1,4.0)])
ax.text(2.3,4.31,'2 enlaces de %g mm'%trunk_mm,fontsize=9,va='center',color=navy)
box(5.7,3.0,3.85,1.75,'PCB SUPERIOR · S12\n\nA / B: divisão 1:5')
arrow([(4.5,5.0),(7.65,5.0),(7.65,4.75)])
ax.text(7.15,5.22,'2 enlaces de %g mm'%trunk_mm,ha='center',fontsize=9,color=navy)
box(.45,.35,9.1,1.6,'',face='#fff3e6',edge='#c98037')
ax.text(5,1.68,'PCB CONTÍNUA · uma única matriz S20 com acoplamento',ha='center',fontsize=12,color=navy,weight='bold')
box(.85,.65,3.7,.6,'E01–E05 · dez terminais A/B',face='white',edge='#c98037')
box(5.45,.65,3.7,.6,'E06–E10 · dez terminais A/B',face='white',edge='#c98037')
arrow([(2.7,3.25),(2.7,1.95)])
arrow([(7.65,3.0),(7.65,1.95)])
ax.text(2.9,2.48,'10 ramais de %g mm'%branch_mm,fontsize=9,color=navy)
ax.text(7.45,2.48,'10 ramais\nde %g mm'%branch_mm,ha='right',fontsize=9,color=navy)
fig.text(.5,.015,'Setas agrupam os dois caminhos de polarização. Não há união elétrica entre A e B.',ha='center',fontsize=10,color=navy)
fig.tight_layout(rect=(0,.02,1,1))
out=root/'imagens';out.mkdir(exist_ok=True)
fig.savefig(out/'circuito_funcional.png',dpi=210,bbox_inches='tight');plt.close(fig)
