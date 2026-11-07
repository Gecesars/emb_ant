"""Figuras cientificas do resultado real R06; sem interpolar uma banda nao resolvida."""
import argparse,csv,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);args=parser.parse_args()
root=args.root;output=root/'imagens';output.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
z=np.load(root/'circuito/campos.npz');metrics=json.loads((root/'circuito/resultado.json').read_text())['corrigida']
fig,axes=plt.subplots(1,2,figsize=(9.6,3.5),layout='constrained')
for ax,axis,width in zip(axes,'HV',[110,15]):
    ax.plot(z['theta'],z[axis],color='#106d95',lw=1.8,label='Ganho realizado total')
    peak=max(z[axis][abs(z['theta'])<=90]);ax.axhline(peak-3,color='#da7b32',ls='--',label='Pico frontal −3 dB')
    ax.set(xlim=(-width,width),ylim=(-3,19),xlabel='Ângulo (graus)',ylabel='Ganho (dBi)',title='Horizontal' if axis=='H' else 'Vertical')
    ax.grid(alpha=.2)
axes[0].legend(fontsize=8);fig.suptitle('5,17 GHz · duas entradas de 0,5 W / 0° · cabos sem atenuação')
fig.savefig(output/'diagramas.png',dpi=210);plt.close(fig)
conv=json.loads((root/'antena/auditoria_convergencia.json').read_text())['historico']
fig,axes=plt.subplots(1,2,figsize=(9.6,3.3),layout='constrained')
axes[0].semilogy([r['passe'] for r in conv[1:]],[r['delta_s'] for r in conv[1:]],'o-',color='#106d95')
axes[0].axhline(.008,color='#da7b32',ls='--');axes[0].set(ylabel='ΔS máximo',xlabel='Passe adaptativo',title='Parâmetros S')
axes[1].semilogy([r['passe'] for r in conv[1:]],[r['delta_campo_max_dB'] for r in conv[1:]],'o-',color='#106d95')
axes[1].axhline(.05,color='#da7b32',ls='--')
axes[1].set(ylabel='Variação máxima (dB)',xlabel='Passe adaptativo',title='Campo nas nove direções')
for ax in axes:ax.grid(alpha=.2)
fig.savefig(output/'convergencia.png',dpi=210);plt.close(fig)
with (root/'circuito/divisores_cargas50.csv').open(encoding='utf8') as f:rows=list(csv.DictReader(f))
fig,ax=plt.subplots(figsize=(9.6,3.2),layout='constrained')
for board,stage in [('inferior','1x2'),('inferior','1x5'),('superior','1x5')]:
    rr=[r for r in rows if r['placa']==board and r['estagio']==stage]
    ax.plot([float(r['frequencia_MHz'])/1000 for r in rr],[float(r['perda_excedente_dB']) for r in rr],label=board+' · '+stage)
ax.set(xlabel='Frequência (GHz)',ylabel='Perda excedente (dB)',title='Divisores completos · saídas casadas em 50 Ω')
ax.grid(alpha=.2);ax.legend();fig.savefig(output/'perdas_divisores.png',dpi=210);plt.close(fig)
print('GRAFICOS_R06_OK')
