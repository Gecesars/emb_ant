"""Compara seis e oito passes da mesma PCB2, sem modificar resultados de origem."""
from pathlib import Path
import json,sys,re,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
REPO=Path(__file__).resolve().parents[3];ROOT=Path('D:/dev/EMBRAER/P2S13/R03_Continuacao_M00')
sys.path.insert(0,str(REPO/'automacao/r05'));from rede_carregada import read_pattern
folders=[ROOT/'referencia6',ROOT];rows=[]
assert json.loads((ROOT/'continuidade_auditada.json').read_text())['aprovado']
for p in folders:
    r=json.loads((p/'resultado.json').read_text());hist=json.loads((p/'historico_passes.json').read_text())['historico'];conv=(p/'convergencia.txt').read_text()
    idx=[i for i,n in enumerate(r['ordem_portas']) if n.startswith('R2_')]
    vs=[r[k][i] for k in ['VSWR_ativo','VSWR_casado'] for i in idx];good=max(vs)<=1.25
    rows.append(dict(passes=r['passes'],DeltaS=r['delta_s'],passes_consecutivos=int(re.search(r'Current Consecutive Passes\s*:\s*(\d+)',conv)[1]),
      convergiu_S=r['convergiu'],campos_estaveis=r['estavel_nove_sondas'],auditoria=r['fisica_ok'],VSWR_meta_numerica=good,casamento_validado=bool(good and r['validado_numericamente']),
      VSWR2_ativo_A=vs[0],VSWR2_ativo_B=vs[1],VSWR2_casado_A=vs[2],VSWR2_casado_B=vs[3],VSWR_todas_ativo_max=max(r['VSWR_ativo']),
      ganho_frontal_dBi=r['cortes']['H']['ganho_frontal_dBi'],H_graus=r['cortes']['H']['abertura_graus'],V_graus=r['cortes']['V']['abertura_graus'],
      pico_H_graus=r['cortes']['H']['pico_graus'],pico_V_graus=r['cortes']['V']['pico_graus'],SLL_V_dB=r['cortes']['V']['SLL']['nivel_dB'],
      delta_G_ultimo_passe_dB=hist[-1]['campos_dBi']['P2S13_Campo_00']-hist[-2]['campos_dBi']['P2S13_Campo_00'],delta_campo_max_ultimo_passe_dB=hist[-1]['delta_campo_max_dB']))
delta={k:rows[1][k]-rows[0][k] for k in ['ganho_frontal_dBi','H_graus','V_graus','VSWR2_ativo_A','VSWR2_ativo_B','VSWR2_casado_A','VSWR2_casado_B','SLL_V_dB']}
result=dict(resultados=rows,delta_8_menos_6=delta,configuracao='Mesma geometria e malha continuada; quatro entradas 0.25W/0graus, 5.17GHz, 14nucleos, sem sweep, novos passes7e8.',limite='VSWR refere-se as duas entradas PCB2 do conjunto4+2. Ganho e campos sao totais. Nao qualifica banda nem medicao.')
(ROOT/'comparacao.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
with (ROOT/'comparacao.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
fig,axs=plt.subplots(1,2,figsize=(12,5.7))
for p,row in zip(folders,rows):
    for ax,axis in zip(axs,'HV'):
        t,e=read_pattern(p/('ALL_'+axis+'.csv'));g=10*np.log10(np.sum(abs(e)**2,axis=1));ax.plot(t,g,label='%d passes | %.3f dBi'%(row['passes'],row['ganho_frontal_dBi']))
for ax,axis in zip(axs,'HV'):
    ax.set(xlim=(-90,90) if axis=='H' else (-40,40),ylim=(-20,18),title=axis,xlabel='Angulo (graus)',ylabel='Ganho realizado total (dBi)');ax.grid(alpha=.25);ax.legend(loc='lower center')
fig.suptitle('P2S13 — continuacao da malha: 6 para 8 passes\n5,17 GHz | quatro entradas iguais/em fase | sem alteracao de geometria')
fig.tight_layout(rect=(0,0,1,.87));fig.savefig(ROOT/'comparacao_HV.png',dpi=170);plt.close(fig)
print(json.dumps(result,indent=2))
