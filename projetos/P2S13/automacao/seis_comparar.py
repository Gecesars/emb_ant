"""Compara somente os ensaios 4+2 realmente calculados; campos com fontes iguais."""
from pathlib import Path
import json,csv,sys,re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
REPO=Path(__file__).resolve().parents[3];sys.path.insert(0,str(REPO/'automacao/r05'))
from rede_carregada import read_pattern
ROOT=Path('D:/dev/EMBRAER/P2S13/R01_Seis_Elementos');rows=[];details=[];curves=[]
for p in sorted(ROOT.glob('s*/resultado.json')):
    folder=p.parent;r=json.loads(p.read_text());c=json.loads((folder/'configuracao.json').read_text());h,v=r['cortes']['H'],r['cortes']['V']
    row=dict(caso=folder.name,inicio_dobra_mm=c['inicio_dobra_y_mm'],angulo_dobra_graus=c['angulo_dobra_graus'],ganho_frontal_dBi=h['ganho_frontal_dBi'],H_graus=h['abertura_graus'],V_graus=v['abertura_graus'],pico_H_graus=h['pico_graus'],pico_V_graus=v['pico_graus'],VSWR_ativo_max=max(x for x in r['VSWR_ativo'] if x is not None),VSWR_casado_max=max(x for x in r['VSWR_casado'] if x is not None),passes=r['passes'],DeltaS=r['delta_s'],convergiu=r['convergiu'],auditoria=r['fisica_ok'],H_meta=r['metas_numericas']['horizontal_99_121'],ganho_meta=r['metas_numericas']['ganho_13dBi'])
    row['passes_consecutivos_S']=int(re.search(r'Current Consecutive Passes\s*:\s*(\d+)',(folder/'convergencia.txt').read_text())[1])
    rows.append(row);curves.append((folder,row));module={}
    for prefix in ['R1','R2']:
        t,a=read_pattern(folder/(prefix+'_A_H.csv'));_,b=read_pattern(folder/(prefix+'_B_H.csv'))
        module[prefix]=(a+b)/2
    idx=int(np.argmin(abs(t)));e4,e2=module['R1'][idx],module['R2'][idx];corr=np.vdot(e4,e2)
    diagnostic=dict(caso=folder.name,angulo_referencia_graus=float(t[idx]),fase_relativa_projecao_placa2_vs_placa4_graus=float(np.angle(corr,deg=True)),correlacao_polarizacoes=float(abs(corr)/(np.linalg.norm(e4)*np.linalg.norm(e2))),contribuicao4_linear=float(np.vdot(e4,e4).real),contribuicao2_linear=float(np.vdot(e2,e2).real),termo_interferencia_linear=float(2*corr.real),ganho_conjunto_recomposto_dBi=float(10*np.log10(np.vdot(e4+e2,e4+e2).real)),nota='Contribuicoes embutidas no painel acoplado, com quatro fontes0.25W/0graus. Fase relativa vetorial em boresight nao mede diretamente a fase em cada radiador. Nenhuma fase externa ajustada.')
    assert abs(diagnostic['ganho_conjunto_recomposto_dBi']-h['ganho_frontal_dBi'])<1e-7
    (folder/'contribuicoes_placas.json').write_text(json.dumps(diagnostic,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');details.append(diagnostic)
assert rows,'Nenhum resultado RF real'
(ROOT/'comparacao.json').write_text(json.dumps(dict(resultados=rows,contribuicoes=details,prioridade='Horizontal99–121graus, meta nominal110; ganho13dBi e vertical18graus continuam relatados',limite='Nao escolher uma geometria como validada quando DeltaS/auditoria nao atendem.'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (ROOT/'comparacao.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
fig,axs=plt.subplots(1,2,figsize=(12,5.8))
for folder,row in curves:
    label='b%d/%d | G%.2f dBi | DS%.3f'%(row['inicio_dobra_mm'],row['angulo_dobra_graus'],row['ganho_frontal_dBi'],row['DeltaS'])
    for ax,axis in zip(axs,'HV'):
        t,e=read_pattern(folder/('ALL_'+axis+'.csv'));g=10*np.log10(np.sum(abs(e)**2,axis=1));ax.plot(t,g-g.max(),label=label)
for ax,axis in zip(axs,'HV'):
    half=(49.5,60.5) if axis=='H' else (8.1,9.9)
    for sign in [-1,1]:ax.axvspan(min(sign*half[0],sign*half[1]),max(sign*half[0],sign*half[1]),color='#359f83',alpha=.12)
    ax.axhline(-3,c='#777',ls='--');ax.set(xlim=(-90,90) if axis=='H' else (-35,35),ylim=(-30,1),xlabel='Angulo (graus)',ylabel='Diagrama normalizado (dB)',title=axis);ax.grid(alpha=.2);ax.legend(fontsize=8,loc='lower center')
fig.suptitle('P2S13 — seis niveis, placa4 + placa2 simetrica — 5,17 GHz\nQuatro fontes iguais/em fase; verde = bordas-alvo a -3 dB; resultados preliminares',fontsize=12)
fig.tight_layout(rect=(0,.03,1,.89));fig.savefig(ROOT/'comparacao_HV.png',dpi=170);plt.close(fig)
print(json.dumps(rows,indent=2))
