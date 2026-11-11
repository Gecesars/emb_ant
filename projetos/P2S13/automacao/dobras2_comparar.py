"""Compara solucoes reais de dobras e decompoe campos; nao altera excitacoes."""
from pathlib import Path
import json,sys,csv,re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
REPO=Path(__file__).resolve().parents[3];sys.path.insert(0,str(REPO/'automacao/r05'))
from rede_carregada import read_pattern
ROOT=Path('D:/dev/EMBRAER/P2S13/R04_Dobras_Ajustadas');REF=Path('D:/dev/EMBRAER/P2S13/R03_Continuacao_M00')
folders=[REF]+[p.parent for p in sorted(ROOT.glob('d*/resultado.json'))];rows=[];diagnostics=[]
for p in folders:
    r=json.loads((p/'resultado.json').read_text());c=json.loads((p/'configuracao.json').read_text());h,v=r['cortes']['H'],r['cortes']['V']
    vs=max(r['VSWR_ativo']+r['VSWR_casado'])
    row=dict(caso='referencia_b10_a90_8passes' if p==REF else p.name,b_mm=c['inicio_dobra_y_mm'],angulo_graus=c['angulo_dobra_graus'],G_frontal_dBi=h['ganho_frontal_dBi'],G_pico_V_dBi=v['ganho_pico_dBi'],H_graus=h['abertura_graus'],V_graus=v['abertura_graus'],pico_H_graus=h['pico_graus'],pico_V_graus=v['pico_graus'],SLL_V_dB=v['SLL']['nivel_dB'],VSWR_ativo_max=max(r['VSWR_ativo']),VSWR_casado_max=max(r['VSWR_casado']),passes=r['passes'],DeltaS=r['delta_s'],convergencia_S=r['convergiu'],campos_estaveis=r['estavel_nove_sondas'],auditoria=r['fisica_ok'],meta_H=99<=h['abertura_graus']<=121,meta_G=h['ganho_frontal_dBi']>=13,meta_VSWR=vs<=1.25)
    row['metas_RF']=all(row[k] for k in ['meta_H','meta_G','meta_VSWR']);row['aprovado']=row['metas_RF'] and r['validado_numericamente']
    row['consecutivos']=int(re.search(r'Current Consecutive Passes\s*:\s*(\d+)',(p/'convergencia.txt').read_text())[1])
    rows.append(row);module={}
    for pre in ['R1','R2']:
        t,a=read_pattern(p/(pre+'_A_H.csv'));_,b=read_pattern(p/(pre+'_B_H.csv'));module[pre]=(a+b)/2
    idx=np.argmin(abs(t));e4,e2=module['R1'][idx],module['R2'][idx];corr=np.vdot(e4,e2)
    diag=dict(caso=row['caso'],fase_relativa_projecao_placa2_vs_placa4_graus=float(np.angle(corr,deg=True)),correlacao_polarizacoes=float(abs(corr)/(np.linalg.norm(e4)*np.linalg.norm(e2))),G_recomposto_dBi=float(10*np.log10(np.linalg.norm(e4+e2)**2)),limite_fase_alinhada_campos_congelados_dBi=float(10*np.log10(np.linalg.norm(e4)**2+np.linalg.norm(e2)**2+2*abs(corr))),nota='Diagnostico de campos embutidos no mesmo painel acoplado. Limite de fase e estimativa algebrica, nao simulacao de nova alimentacao. Fontes externas permanecem iguais/em fase.')
    assert abs(diag['G_recomposto_dBi']-h['ganho_frontal_dBi'])<1e-7;diagnostics.append(diag)
(ROOT/'comparacao.json').write_text(json.dumps(dict(resultados=rows,contribuicoes=diagnostics,metas='Gfrontal>=13dBi, H99-121graus, VSWR<=1.25 ativo e casado nas quatro entradas; V registrada. Limite6passes para novos casos; referencia8passes historica. Sem sweep.'),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
with (ROOT/'comparacao.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
fig,axs=plt.subplots(1,2,figsize=(12,6))
for p,r in zip(folders,rows):
    for ax,axis in zip(axs,'HV'):
        t,e=read_pattern(p/('ALL_'+axis+'.csv'));g=10*np.log10(np.sum(abs(e)**2,axis=1));ax.plot(t,g-g.max(),label='b%g / %g° | %.2f dBi'%(r['b_mm'],r['angulo_graus'],r['G_frontal_dBi']))
for ax,axis in zip(axs,'HV'):
    ax.axhline(-3,c='#777',ls='--');ax.set(xlim=(-90,90) if axis=='H' else (-35,35),ylim=(-30,1),xlabel='Ângulo (graus)',ylabel='Diagrama normalizado (dB)',title=axis);ax.grid(alpha=.2);ax.legend(fontsize=8,loc='lower center')
for sign in [-1,1]:axs[0].axvspan(min(sign*49.5,sign*60.5),max(sign*49.5,sign*60.5),color='#359f83',alpha=.12)
fig.suptitle('P2S13 — refletor do conjunto 4+2, PCBs ajustadas preservadas\n5,17 GHz | quatro entradas iguais/em fase | convergência e ressalvas na tabela',fontsize=12)
fig.tight_layout(rect=(0,.03,1,.89));fig.savefig(ROOT/'comparacao_HV.png',dpi=170);plt.close(fig)
print(json.dumps(rows,indent=2))
