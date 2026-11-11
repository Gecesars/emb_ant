"""Resumo de resultados reais, sem substituir os dados EM por previsoes."""
from pathlib import Path
import json
import numpy as np
import skrf as rf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path('D:/dev/EMBRAER/P2S13/R09_Correcao_Divisor')
rows=[]
for folder in sorted(ROOT.glob('c*')):
    if not (folder/'resultado.json').exists():continue
    r=json.loads((folder/'resultado.json').read_text());cfg=json.loads((folder/'configuracao.json').read_text())
    s=rf.Network(str(folder/'divisor_ordenado.s8p')).s[0];matched=[]
    for j in [0,1]:
        v=s[[2+j,4+j,6+j],j]
        matched.append(dict(polarizacao='AB'[j],modulo_dB=(20*np.log10(abs(v))).tolist(),fase_relativa_graus=np.angle(v/v[1],deg=True).tolist()))
    row=dict(caso=folder.name,parametros=cfg.get('parametros'),delta_s=r['delta_s'],convergiu=r['convergiu'],passes=r['passes'],
        VSWR_ativo=r['VSWR_ativo'],VSWR_casado=r['VSWR_outra_casada'],G_dBi=r['cortes']['H']['ganho_frontal_dBi'],H=r['cortes']['H']['abertura_graus'],V=r['cortes']['V']['abertura_graus'],
        amplitude_dB=r['dispersao_amplitude_dB'],fase_graus=r['dispersao_fase_graus'],perda_divisor_W=r['perda_divisor_dissipacao_mais_radiacao_W'],saidas_casadas=matched)
    (folder/'diagnostico_balanceamento.json').write_text(json.dumps(row,indent=2)+'\n');rows.append(row)
    fig,axs=plt.subplots(1,2,figsize=(11,4.5));names=r['ordem_S8_circuito'][2:]
    axs[0].bar(names,r['ondas_incidentes_antena_potencia_W']);axs[0].set_ylabel('Potencia incidente na antena (W)')
    axs[1].bar(names,r['ondas_incidentes_antena_fase_relativa_graus']);axs[1].set_ylabel('Fase relativa a R2_A (graus)')
    for ax in axs:ax.grid(axis='y',alpha=.2)
    fig.suptitle('%s — duas entradas 0,5 W / 0° — 5,17 GHz\nDesequilibrio carregado: %.3f dB / %.3f°'%(folder.name,r['dispersao_amplitude_dB'],r['dispersao_fase_graus']))
    fig.tight_layout(rect=(0,0,1,.87));fig.savefig(folder/'balanceamento.png',dpi=180);plt.close(fig)
(ROOT/'comparacao.json').write_text(json.dumps(rows,indent=2)+'\n')
for row in rows:print(json.dumps(row,ensure_ascii=False))
