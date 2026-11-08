"""Pre-dimensionamento rastreado; nao equivale a uma simulacao EM do painel novo."""
import json,sys,csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
repo=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(repo/'automacao/r06'))
from circuito import Circuit,beam
root=Path('D:/dev/EMBRAER/P2M21/R00_Concepcao');out=root/'planejamento';out.mkdir(parents=True,exist_ok=True)
source=Path('D:/dev/EMBRAER/P1H/R06_sem_cabos')
c=Circuit(source);base={};cuts={}
for pol,e in [('A',[1,0]),('B',[0,1])]:
    r,t,p,feeding=c.calculate(e);base[pol]=r;cuts[pol]=p
rows=[]
for n in [10,12,14,16,18,20]:
    for d in [32,36,40,44,48]:
        af=2*np.cos(np.pi*d/1000/(299792458/5.17e9)*np.sin(np.deg2rad(t)))**2
        hs={p:beam(t,cuts[p]['H']+10*np.log10(np.maximum(af,1e-30)))[0] for p in 'AB'}
        ideal=min(base[p]['ganho_frontal_realizado_dBi'] for p in 'AB')+10*np.log10(2*n/10)
        rows.append(dict(niveis=n,colunas=2,radiadores=2*n,espacamento_colunas_mm=d,
          altura_ativa_mm=(n-1)*52.6+28.3125,ganho_escala_centro_dBi=ideal,
          reserva_projeto_dB=.75,ganho_com_reserva_centro_dBi=ideal-.75,
          horizontal_A_graus=float(hs['A']),horizontal_B_graus=float(hs['B']),
          vertical_estimada_graus=max(base[p]['abertura_V_graus'] for p in 'AB')*10/n))
with (out/'comparacao.csv').open('w',newline='',encoding='utf8') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
selected=next(r for r in rows if r['niveis']==16 and r['espacamento_colunas_mm']==40)
config=dict(nome='P2M21',revisao='R00',estado='PRE_DIMENSIONADO_NAO_QUALIFICADO_EM',
  frequencias_MHz=list(range(5090,5251,10)),meta_ganho_por_entrada_dBi=21,
  criterio_vswr=1.5,novos_adaptativos_max_passes=6,max_delta_s=.02,
  niveis=16,colunas=2,passo_vertical_mm=52.6,passo_horizontal_mm=40,
  radiadores=32,portas_radiadores=64,entradas_MIMO=2,
  polarizacoes=['A','B'],arquitetura='Cada entrada alimenta ambas as colunas na sua polarizacao; a outra entrada e casada em50ohms.',
  modulos=4,niveis_por_modulo=4,pcb_radiadores_mm=[186.1125,68.3125,.76],
  centros_modulos_x_mm=[-315.6,-105.2,105.2,315.6],
  refletor_mm=[850,100,2],z_base_pcb_mm=16.61,
  materiais=dict(radiadores='RO4350B 0.76mm, Dk3.66, Df0.0037',divisores='ZYF300CA-C 1.52mm, Dk2.94, Df0.0016',cobre_um=35),
  rede='Duas entradas -> divisor duplo1:4 central -> quatro divisores locais duplos1:8 ->32 radiadores por polarizacao',
  selecionado=selected,referencia_centro=base,
  limites='Escala de ganho e fator de arranjo no centro, campos de referenciaR06. Nao inclui novo acoplamento, mudanca de refletor/PCB ou rede real; reserva0.75dB e hipotese de projeto, nao perda simulada. Banda nova pendente.')
(root/'configuracao.json').write_text(json.dumps(config,indent=2),encoding='utf8')
(out/'comparacao.json').write_text(json.dumps(dict(configuracao=config,casos=rows),indent=2),encoding='utf8')
fig,axs=plt.subplots(1,2,figsize=(11,4.5));sample=[r for r in rows if r['espacamento_colunas_mm']==40]
axs[0].plot([r['niveis'] for r in sample],[r['ganho_escala_centro_dBi'] for r in sample],'o-',label='Escala ideal a partir da R06')
axs[0].plot([r['niveis'] for r in sample],[r['ganho_com_reserva_centro_dBi'] for r in sample],'o-',label='Com reserva assumida de0,75dB')
axs[0].axhline(21,color='r',ls='--',label='Meta por entrada');axs[0].set(xlabel='Niveis verticais',ylabel='Ganho estimado no centro (dBi)');axs[0].legend(fontsize=8);axs[0].grid()
for d in [32,40,48]:
    a=2*np.cos(np.pi*d/1000/(299792458/5.17e9)*np.sin(np.deg2rad(t)))**2
    g=cuts['A']['H']+10*np.log10(np.maximum(a,1e-30));g-=g[np.argmin(abs(t))]
    axs[1].plot(t,g,label=str(d)+'mm')
axs[1].set(xlim=(-90,90),ylim=(-30,1),xlabel='Angulo horizontal (graus)',ylabel='Ganho relativo estimado (dB)');axs[1].legend(title='Entre colunas');axs[1].grid()
fig.suptitle('P2M21 — pre-dimensionamento, nao resultado EM do painel novo');fig.tight_layout();fig.savefig(out/'predimensionamento.png',dpi=180)
print(json.dumps(selected,indent=2))
