"""Compara a distancia laminado-refletor a partir de solucoes HFSS exportadas."""
from pathlib import Path
import json,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from divisor_variantes_comparar import read_pattern

ROOT=Path('D:/dev/EMBRAER/P2M21/R11_Divisor_Ajustes')
plan=json.loads((ROOT/'plano_alturas.json').read_text())
records=[]
fig,axs=plt.subplots(1,2,figsize=(12,5.8),sharey=True)
for name in plan['variantes']:
    folder=ROOT/name
    r=json.loads((folder/'resultado.json').read_text());cfg=json.loads((folder/'configuracao.json').read_text())
    h=cfg.get('distancia_face_inferior_laminado_ao_refletor_mm',16.61)
    assert cfg['espacamento_vertical_mm']==plan['passo_mm'] and r['fisica_ok']
    records.append(dict(variante=name,distancia_laminado_mm=h,distancia_cobre_inferior_mm=h-.035,
        ganho_frontal_dBi=r['cortes']['H']['ganho_frontal_dBi'],
        maximo_H_graus=r['cortes']['H']['pico_graus'],maximo_V_graus=r['cortes']['V']['pico_graus'],
        abertura_H_graus=r['cortes']['H']['abertura_graus'],abertura_V_graus=r['cortes']['V']['abertura_graus'],
        VSWR_ativo=r['VSWR_ativo'],VSWR_casado=r['VSWR_casado'],SLL_V_dB=r['SLL_V']['nivel_dB'],
        DeltaS=r['delta_s'],passes=r['passes'],consecutivos=r['passes_consecutivos'],convergiu=r['convergiu'],aprovado=r['aprovado']))
    for ax,axis in zip(axs,'HV'):
        t,e=read_pattern(folder/('AB_'+axis+'.csv'));gain=10*np.log10(np.sum(abs(e)**2,axis=1))
        ax.plot(t,gain,lw=1.6,label=f"{h:.3f} mm | G0 {r['cortes']['H']['ganho_frontal_dBi']:.2f} dBi | ΔS {100*r['delta_s']:.2f}%")
for ax,axis in zip(axs,'HV'):
    ax.set(xlim=(-90,90),ylim=(-20,16),xlabel='Ângulo (graus)',title='Corte '+axis)
    ax.axvline(0,c='gray',lw=.7);ax.grid(alpha=.25);ax.legend(fontsize=8)
axs[0].set_ylabel('Ganho realizado total (dBi)')
status='Convergência completa em todos os casos' if all(q['convergiu'] for q in records) else 'Inclui resultados sem convergência completa'
fig.suptitle(f"Distância PCB–refletor ±10% | passo {plan['passo_mm']:g} mm | 5,17 GHz\nA=B=0,5 W / 0° — {status}")
fig.tight_layout(rect=(0,0,1,.89));fig.savefig(ROOT/'alturas_HFSS.png',dpi=180);plt.close(fig)
result=dict(casos=records,referencia_distancia='Face superior do refletor em Z=0 ate a face inferior do laminado. Cobre inferior35um fica0.035mm mais perto.',
 controles='Mesmos radiadores, passo, contornos, materiais, divisores e caminhos impressos. PCB e cabos de50mm deslocados juntos emZ; refletor fixo. Duas fontes iguais emfase; sem suportes plasticos.',
 limite='Cada nova geometria respeitou maximo6passes. Nao constitui varredura de frequencia ou prova de otimo global.')
(ROOT/'alturas_HFSS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
