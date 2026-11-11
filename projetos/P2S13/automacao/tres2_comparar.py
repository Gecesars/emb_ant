"""Resultados do novo arranjo3xPCB2, com fontes iguais e alvoH100graus."""
from pathlib import Path
import json,sys,csv,re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
REPO=Path(__file__).resolve().parents[3];sys.path.insert(0,str(REPO/'automacao/r05'))
from rede_carregada import read_pattern
ROOT=Path('D:/dev/EMBRAER/P2S13/R05_Tres_Placas2');rows=[];details=[];folders=[]
for p in sorted(ROOT.glob('t*/resultado.json')):
    folder=p.parent;r=json.loads(p.read_text());c=json.loads((folder/'configuracao.json').read_text());h,v=r['cortes']['H'],r['cortes']['V']
    row=dict(caso=folder.name,b_mm=c['inicio_dobra_y_mm'],angulo_graus=c['angulo_dobra_graus'],G_frontal_dBi=h['ganho_frontal_dBi'],G_pico_V_dBi=v['ganho_pico_dBi'],H_graus=h['abertura_graus'],erro_H_frente_100_graus=h['abertura_graus']-100,V_graus=v['abertura_graus'],pico_H_graus=h['pico_graus'],pico_V_graus=v['pico_graus'],SLL_V_dB=v['SLL']['nivel_dB'],VSWR_ativo_max=max(r['VSWR_ativo']),VSWR_casado_max=max(r['VSWR_casado']),passes=r['passes'],DeltaS=r['delta_s'],convergiu_S=r['convergiu'],campos_estaveis=r['estavel_nove_sondas'],auditoria=r['fisica_ok'],H_100_mais_menos_1grau=abs(h['abertura_graus']-100)<=1,meta_G=h['ganho_frontal_dBi']>=13,meta_VSWR=max(r['VSWR_ativo']+r['VSWR_casado'])<=1.25,aprovado=r['aprovado'])
    row['consecutivos']=int(re.search(r'Current Consecutive Passes\s*:\s*(\d+)',(folder/'convergencia.txt').read_text())[1])
    row['perda_frente_pico_H_dB']=h['ganho_pico_dBi']-h['ganho_frontal_dBi']
    row['centro_cruzamentos_H_graus']=sum(h['cruzamentos_graus'])/2
    rows.append(row);folders.append(folder)
    fields=[]
    for name in ['R1','R2','R3']:
        t,a=read_pattern(folder/(name+'_A_H.csv'));_,b=read_pattern(folder/(name+'_B_H.csv'));i=np.argmin(abs(t));fields.append((a[i]+b[i])/np.sqrt(6))
    phases=[float(np.angle(np.vdot(fields[1],e),deg=True)) for e in fields]
    g=float(10*np.log10(np.linalg.norm(sum(fields))**2));assert abs(g-h['ganho_frontal_dBi'])<1e-7
    details.append(dict(caso=folder.name,fases_campos_frontais_vs_placa_central_graus=phases,G_recomposto_dBi=g,nota='Campos embutidos na montagem acoplada. Entradas externas iguais/em fase; nao representa fase medida diretamente em cada radiador.'))
assert rows
(ROOT/'comparacao.json').write_text(json.dumps(dict(resultados=rows,contribuicoes=details,alvo_H_graus=100,aproximacao_nominal_de_busca_graus=1,nota='Todos ensaios5.17GHz,14nucleos,sem sweep,max6passes. MetasG13 eVSWR1.25 mantidas; nenhum resultado nao convergido vira validado por atingir valor nominal.'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (ROOT/'comparacao.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
fig,axs=plt.subplots(1,2,figsize=(12,6))
for folder,r in zip(folders,rows):
    for ax,axis in zip(axs,'HV'):
        t,e=read_pattern(folder/('ALL_'+axis+'.csv'));g=10*np.log10(np.sum(abs(e)**2,axis=1));ax.plot(t,g-g.max(),label='b%g / %g° | G%.2f dBi'%(r['b_mm'],r['angulo_graus'],r['G_frontal_dBi']))
for ax,axis in zip(axs,'HV'):
    ax.axhline(-3,c='#777',ls='--');ax.set(xlim=(-90,90),ylim=(-30,1),title=axis,xlabel='Ângulo (graus)',ylabel='Diagrama normalizado (dB)');ax.grid(alpha=.2);ax.legend(fontsize=8,loc='lower center')
for x in [-50,50]:axs[0].axvline(x,c='#26826a',ls=':',lw=1)
status='PRELIMINAR — ensaios sem convergência' if not any(r['convergiu_S'] for r in rows) else 'Consultar convergência e auditorias no relatório'
fig.suptitle('P2S13 — três PCBs idênticas de dois elementos\n5,17 GHz | seis entradas iguais/em fase | alvo horizontal 100°\n'+status)
fig.tight_layout(rect=(0,.03,1,.88));fig.savefig(ROOT/'comparacao_HV.png',dpi=170);plt.close(fig)
print(json.dumps(rows,indent=2))
