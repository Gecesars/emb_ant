"""Triagem analitica com a celula C12; nao substitui FEM do novo refletor."""
from pathlib import Path
import json,csv,sys,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'automacao/r05'))
from rede_carregada import read_pattern,beam
ROOT=Path('D:/dev/EMBRAER/P2S13/R00_Refletor_Dobrado')
ROOT.mkdir(parents=True,exist_ok=True)
SRC=REPO/'projetos/P2M21/quatro_elementos_casamento_banda/c12_raiz_intermediaria'
cases={'C12 isolada':[(0,0)],'Duas em coluna, passo 192 mm':[(-96,0),(96,0)],'Duas lado a lado, passo 78 mm':[(0,-39),(0,39)]}
results={};fig,axes=plt.subplots(1,2,figsize=(12,5))
for axis,ax,limit in zip('HV',axes,[(99,121),(16.2,19.8)]):
    th,e=read_pattern(SRC/('AB_'+axis+'.csv'))
    for label,coords in cases.items():
        pos=np.array([c[1 if axis=='H' else 0] for c in coords])/1000
        af=np.exp(1j*2*np.pi*5.17e9/299792458*np.sin(np.deg2rad(th))[:,None]*pos).sum(axis=1)/np.sqrt(len(pos))
        ef=e*af[:,None];g=10*np.log10(np.maximum(np.sum(abs(ef)**2,axis=1),1e-30))
        width,l,r=beam(th,g);front=float(g[np.argmin(abs(th))]);results.setdefault(label,{})[axis]={'ganho_frontal_estimado_dBi':front,'abertura_graus':float(width)}
        ax.plot(th,g,label=label)
    ax.set(xlim=(-90,90) if axis=='H' else (-35,35),ylim=(-15,20),xlabel='Ângulo (graus)',ylabel='Ganho estimado (dBi)',title=f'Corte {axis} — meta {limit[0]}° a {limit[1]}°')
    ax.grid(alpha=.25);ax.legend(fontsize=8)
fig.suptitle('Triagem analítica — 5,17 GHz — potência incidente total 1 W\nCélula C12 e fator de arranjo, sem acoplamento ou novo refletor dobrado')
fig.tight_layout(rect=(0,0,1,.90));fig.savefig(ROOT/'estimativa_arranjos.png',dpi=170);plt.close(fig)
out={'metodo':'Campos complexos C12 x fator de arranjo / sqrt(N). Usa refletor original; ignora acoplamento e alteracoes de refletor. Ganho estimado, nao validacao do painel.','casos':results,'frequencia_GHz':5.17,'fontes_iguais_em_fase':True,'potencia_total_W':1,'fontes_sha256':{n:hashlib.sha256((SRC/n).read_bytes()).hexdigest() for n in ['AB_H.csv','AB_V.csv','4_elementos.FCStd']}}
(ROOT/'estimativa_arranjos.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(results,ensure_ascii=False,indent=2))
