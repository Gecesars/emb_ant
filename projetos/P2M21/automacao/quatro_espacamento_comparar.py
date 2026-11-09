"""Compara somente solucoes HFSS reais das variantes de espacamento."""
from pathlib import Path
import json,argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from divisor_variantes_comparar import read_pattern

ROOT=Path('D:/dev/EMBRAER/P2M21/R11_Divisor_Ajustes')
parser=argparse.ArgumentParser();parser.add_argument('--grupo',choices=['reduzidos','505254'],default='reduzidos');args=parser.parse_args()
names=['v09_transformadores','v10_passo42','v11_passo44','v12_passo42_compensado'] if args.grupo=='reduzidos' else ['v09_transformadores','v13_passo50_ajustado','v14_passo52_ajustado','v15_passo54_ajustado']
if args.grupo=='505254' and (ROOT/'selecoes_505254.json').exists():
    chosen=json.loads((ROOT/'selecoes_505254.json').read_text())['variantes']
    assert set(chosen)=={'50','52','54'}
    names=['v09_transformadores']+[chosen[k] for k in ['50','52','54']]
stem='espacamento_HFSS' if args.grupo=='reduzidos' else 'espacamento_505254'
fig,axs=plt.subplots(1,2,figsize=(12,5.5))
records=[]
for name in names:
    f=ROOT/name
    if not (f/'resultado.json').exists():continue
    r=json.loads((f/'resultado.json').read_text());cfg=json.loads((f/'configuracao.json').read_text())
    pitch=cfg['espacamento_vertical_mm']
    t,e=read_pattern(f/'AB_V.csv');gain=10*np.log10(np.sum(abs(e)**2,axis=1))
    front=abs(t)<=90;peak=max(gain[front])
    comp=' compensado' if cfg['parametros'].get('root_extra',0) else ''
    for ax,values in zip(axs,[gain,gain-peak]):ax.plot(t,values,lw=1.6,label=f"{pitch:g} mm{comp}: G0 {r['cortes']['V']['ganho_frontal_dBi']:.2f} dBi; SLL {r['SLL_V']['nivel_dB']:.2f} dB")
    records.append(dict(variante=name,passo_mm=pitch,comprimentos_compensados=bool(comp),ganho_frontal_dBi=r['cortes']['V']['ganho_frontal_dBi'],
        pico_H_graus=r['cortes']['H']['pico_graus'],pico_V_graus=r['cortes']['V']['pico_graus'],
        abertura_H_graus=r['cortes']['H']['abertura_graus'],abertura_V_graus=r['cortes']['V']['abertura_graus'],
        VSWR_ativo=r['VSWR_ativo'],VSWR_casado=r['VSWR_casado'],SLL_V_dB=r['SLL_V']['nivel_dB'],
        DeltaS=r['delta_s'],passes=r['passes'],consecutivos=r['passes_consecutivos'],convergiu=r['convergiu']))
for ax in axs:
    ax.set(xlim=(-90,90),xlabel='Elevação (graus)');ax.axvline(0,lw=.7,c='gray');ax.grid(alpha=.25);ax.legend(fontsize=8)
axs[0].set(ylim=(-20,16),ylabel='Ganho realizado total (dBi)',title='Ganho absoluto')
axs[1].set(ylim=(-30,1),ylabel='Ganho relativo ao máximo frontal (dB)',title='Comparação dos lóbulos')
fig.suptitle('Espaçamento vertical — HFSS completo em 5,17 GHz\nA=B=0,5 W / 0°; dois cabos físicos; conferir convergência de cada ensaio')
fig.tight_layout(rect=(0,0,1,.9));fig.savefig(ROOT/(stem+'.png'),dpi=180);plt.close(fig)
data=dict(resultados=records,controles='Mesmos radiadores, materiais, largura dos retornos, dimensoes externas e transformadores; centros e redes reposicionados. Caminhos iguais entre os quatro radiadores e A/B. Na variante compensada, meandros iguais restauram o comprimento geometrico da referencia48; isso nao prova igualdade de fase real por causa de descontinuidades e acoplamento.',
    limite='Convergencia indicada individualmente; nenhuma variante foi estendida alem de seis passes. Resultados nao sao uma varredura de frequencia nem uma prova de otimo global.')
if args.grupo=='505254':
    data['controles']='50/52/54: PCB70x202mm e refletor90x218mm comuns; radiadores, materiais e largura dos retornos iguais. Rotas e transformadores reajustados por passo. Referencia48:PCB70x184/refletor90x200; nao isola apenas o espacamento. Cada modulo tem quatro caminhos iguais e fontes A/B iguais em fase.'
(ROOT/(stem+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(data,ensure_ascii=False,indent=2))
