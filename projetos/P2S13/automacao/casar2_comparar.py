"""Analisa casamento PCB2 nos ensaios completos4+2 realmente finalizados."""
from pathlib import Path
import json,sys,csv,re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path('D:/dev/EMBRAER/P2S13/R02_Casamento_Placa2');REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'automacao/r05'));from rede_carregada import read_pattern
base=REPO/'projetos/P2S13/seis_elementos/s02_b10_a90'
folders=[base]+[p.parent for p in sorted(ROOT.glob('m*/resultado.json'))]
rows=[];allr=[]
for folder in folders:
    r=json.loads((folder/'resultado.json').read_text());c=json.loads((folder/'configuracao.json').read_text())
    cell=next(x for x in c['celulas'] if x['radiadores']==2);g=json.loads((Path(cell['fonte'])/'geometria.json').read_text());t=g['traces'][0]
    idx=[i for i,n in enumerate(r['ordem_portas']) if n.startswith(cell['nome']+'_')]
    maxvs=max(r[k][i] for k in ['VSWR_ativo','VSWR_casado'] for i in idx)
    row=dict(caso='referencia' if folder==base else folder.name,largura_mm=t['largura_transformador_mm'],comprimento_mm=abs(t['linha70'][1][0]-t['linha70'][0][0]),
      VSWR2_ativo_A=r['VSWR_ativo'][idx[0]],VSWR2_ativo_B=r['VSWR_ativo'][idx[1]],VSWR2_casado_A=r['VSWR_casado'][idx[0]],VSWR2_casado_B=r['VSWR_casado'][idx[1]],
      VSWR_todas_ativo_max=max(r['VSWR_ativo']),ganho_frontal_dBi=r['cortes']['H']['ganho_frontal_dBi'],H_graus=r['cortes']['H']['abertura_graus'],V_graus=r['cortes']['V']['abertura_graus'],
      pico_H_graus=r['cortes']['H']['pico_graus'],pico_V_graus=r['cortes']['V']['pico_graus'],SLL_V_dB=r['cortes']['V']['SLL']['nivel_dB'],passes=r['passes'],DeltaS=r['delta_s'],convergiu_S=r['convergiu'],campos_estaveis=r['estavel_nove_sondas'],auditoria=r['fisica_ok'],
      VSWR2_meta_numerica=maxvs<=1.25,casamento_validado=bool(maxvs<=1.25 and r['validado_numericamente']))
    conv=(folder/'convergencia.txt').read_text();hist=json.loads((folder/'historico_passes.json').read_text())['historico']
    row.update(passes_consecutivos=int(re.search(r'Current Consecutive Passes\s*:\s*(\d+)',conv)[1]),rotulo_HFSS_converged='Converged : Yes' in conv,
       delta_G_ultimo_passe_dB=hist[-1]['campos_dBi']['P2S13_Campo_00']-hist[-2]['campos_dBi']['P2S13_Campo_00'],delta_campo_max_ultimo_passe_dB=hist[-1]['delta_campo_max_dB'])
    rows.append(row);allr.append(r)
    if folder!=base:(folder/'casamento.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
result=dict(resultados=rows,limites='VSWR2<=1.25 com quatro entradas iguais/em fase e com outras entradas casadas. Limite6passes nao equivale a convergencia. Campo/G/H/V de todos os quatro acessos. Refletor b10/90 fixo, cabos50mm fisicos com perdas.')
(ROOT/'comparacao.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (ROOT/'comparacao.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
fig,axs=plt.subplots(1,2,figsize=(12,5.7))
for folder,row in zip(folders,rows):
    for ax,axis in zip(axs,'HV'):
        t,e=read_pattern(folder/('ALL_'+axis+'.csv'));gain=10*np.log10(np.sum(abs(e)**2,axis=1));ax.plot(t,gain,label=row['caso']+' | %.2f dBi'%row['ganho_frontal_dBi'])
for ax,axis in zip(axs,'HV'):
    ax.set(xlim=(-90,90) if axis=='H' else (-40,40),ylim=(-20,18),xlabel='Angulo (graus)',ylabel='Ganho realizado total (dBi)',title=axis);ax.grid(alpha=.25);ax.legend(loc='lower center')
fig.suptitle('P2S13 — ajuste simetrico dos transformadores da placa2\n5,17 GHz | quatro entradas iguais/em fase | classificacao de convergencia na tabela')
fig.tight_layout(rect=(0,0,1,.87));fig.savefig(ROOT/'comparacao_HV.png',dpi=170);plt.close(fig)
print(json.dumps(rows,indent=2))
