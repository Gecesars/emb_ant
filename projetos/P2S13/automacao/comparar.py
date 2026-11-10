"""Compara somente os casos que realmente terminaram; nao preenche dados ausentes."""
from pathlib import Path
import sys,json,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
REPO=Path(__file__).resolve().parents[3];sys.path.insert(0,str(REPO/'automacao/r05'))
from rede_carregada import read_pattern
ROOT=Path('D:/dev/EMBRAER/P2S13/R00_Refletor_Dobrado')
rows=[];curves=[]
for path in sorted(ROOT.glob('v*/resultado.json')):
    r=json.loads(path.read_text());cfg=json.loads((path.parent/'configuracao.json').read_text());h,v=r['cortes']['H'],r['cortes']['V']
    rows.append(dict(variante=cfg['revisao'],metodo_malha=cfg.get('mesh_method','AnsoftClassic'),inicio_dobra_mm=cfg['inicio_dobra_y_mm'],angulo_graus=cfg['angulo_dobra_graus'],ganho_dBi=h['ganho_frontal_dBi'],H_graus=h['abertura_graus'],V_graus=v['abertura_graus'],pico_H=h['pico_graus'],pico_V=v['pico_graus'],VSWR_ativo_max=max(r['VSWR_ativo']),delta_s=r['delta_s'],passes=r['passes'],convergiu=r['convergiu'],fisica_ok=r['fisica_ok'],estavel=r['estavel_nove_sondas'],aprovado=r['aprovado']))
    curves.append((path.parent,r))
assert rows,'Nenhum resultado disponivel'
(ROOT/'comparacao.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (ROOT/'comparacao.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
fig,axs=plt.subplots(1,2,figsize=(12,5))
for ax,axis in zip(axs,'HV'):
    for root,r in curves:
        t,e=read_pattern(root/('ALL_'+axis+'.csv'));g=10*np.log10(np.sum(abs(e)**2,axis=1));ax.plot(t,g,label=root.name+('' if r['validado_numericamente'] else ' (preliminar)'))
    ax.set(xlim=(-90,90) if axis=='H' else (-30,30),ylim=(-20,18),title=axis,xlabel='Angulo (graus)',ylabel='Ganho realizado total (dBi)');ax.grid(alpha=.25);ax.legend(fontsize=8)
fig.suptitle('P2S13 — dois modulos em coluna — 5,17 GHz\nQuatro fontes iguais / 0 graus, 1 W total; sem rede externa')
fig.tight_layout(rect=(0,0,1,.89));fig.savefig(ROOT/'comparacao_HV.png',dpi=180);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(12,5))
for ax,axis,half_bounds in zip(axs,'HV',[(49.5,60.5),(8.1,9.9)]):
    for root,r in curves:
        t,e=read_pattern(root/('ALL_'+axis+'.csv'));g=10*np.log10(np.sum(abs(e)**2,axis=1))
        cfg=json.loads((root/'configuracao.json').read_text())
        label='Plano' if cfg['angulo_dobra_graus']==0 else f"b={cfg['inicio_dobra_y_mm']} mm, {cfg['angulo_dobra_graus']} graus"
        ax.plot(t,g-g.max(),label=label)
    for sign in [-1,1]:
        bounds=sorted(sign*x for x in half_bounds)
        ax.axvspan(*bounds,color='#78c2a4',alpha=.25)
    ax.axhline(-3,c='#666',ls='--',lw=.9)
    ax.set(xlim=(-90,90) if axis=='H' else (-30,30),ylim=(-30,.5),title=axis,
           xlabel='Angulo (graus)',ylabel='Diagrama normalizado (dB)')
    ax.grid(alpha=.25);ax.legend(fontsize=8)
fig.suptitle('P2S13 — comparacao dos diagramas em 5,17 GHz\nFaixas verdes: posicoes desejadas das bordas a -3 dB para feixe centrado em 0 graus')
fig.text(.5,.015,'Estudo preliminar; consultar o DeltaS de cada caso. As faixas verdes nao sao resultados de simulacao.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.05,1,.89));fig.savefig(ROOT/'comparacao_normalizada.png',dpi=180);plt.close(fig)
print(json.dumps(rows,indent=2))
