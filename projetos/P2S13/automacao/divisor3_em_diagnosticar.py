"""Comparacao quantitativa de linhas ideais distribuidas e divisor EM real."""
from pathlib import Path
import sys,json,os
import numpy as np
import skrf as rf
from skrf.circuit import Circuit
from shapely.geometry import LineString
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0,str(Path(__file__).parent))
from divisor_duplo3_planejar import medium,F
ROOT=Path(os.environ.get('P2S13_DIV3_ROOT','D:/dev/EMBRAER/P2S13/R08_Divisor_HFSS'));cfg=json.loads((ROOT/'configuracao.json').read_text());result=json.loads((ROOT/'resultado.json').read_text())
traces={t['name'].removeprefix('A_'):t for t in cfg['traces'] if t['name'].startswith('A_')}
mapping=[('INPUT',0,1),('QH',1,2),('QL',1,3),('MH',2,4),('ML',3,5),('BYPASS',4,6),('DELAY',5,7),('E1',7,8),('E2',7,9),('OUT1',6,10),('OUT2',8,11),('OUT3',9,12)]
nodes=[[] for _ in range(13)]
for name,i,j in mapping:
    t=traces[name];n=medium(t['Z_ohm']).line(t['length_mm']/1000,unit='m',name=name);nodes[i].append((n,0));nodes[j].append((n,1))
for tag,i,j,R in [('R106',2,3,cfg['resistores'][0]['R']),('R100',8,9,100.)]:
    n=Circuit.SeriesImpedance(F,R,tag);nodes[i].append((n,0));nodes[j].append((n,1))
for tag,i in zip(['IN','R1','R2','R3'],[0,10,11,12]):nodes[i].append((Circuit.Port(F,tag),0))
nom=Circuit(nodes).network;nom.port_names=['IN','R1','R2','R3'];nom.write_touchstone(str(ROOT/'referencia_linhas'),form='ri')
np.testing.assert_allclose(abs(nom.s[0,1:,0]),cfg['nominal_saida_modulo'],atol=1e-12)
em=rf.Network(str(ROOT/'divisor_ordenado.s8p')).s[0]
rows=[]
for pol,inp,ix in [('A',0,[2,4,6]),('B',1,[3,5,7])]:
    vals=em[ix,inp];nomv=nom.s[0,1:,0]
    for i,(value,ideal) in enumerate(zip(vals,nomv),1):
        rows.append(dict(porta='R%d_%s'%(i,pol),HFSS_modulo_dB=float(20*np.log10(abs(value))),
            HFSS_fase_relativa_graus=float(np.angle(value/vals[1],deg=True)),
            linhas_modulo_dB=float(20*np.log10(abs(ideal))),linhas_fase_relativa_graus=float(np.angle(ideal/nomv[1],deg=True))))
delay=traces['DELAY'];poly=LineString(delay['points']).buffer(delay['width_mm']/2,cap_style=2,join_style=2)
overlap={name:LineString(traces[name]['points']).intersection(poly).length for name in ['E1','E2']}
diagnosis=dict(saidas_casadas_50ohm=rows,sobreposicao_linha_central_com_juncao_entrada_segundo_estagio_mm=overlap,
    nota=('Juncao corrigida: nenhuma sobreposicao da linha central dos ramos E1/E2 com a linha DELAY; contato somente no ponto de inicio.' if max(overlap.values())<1e-6 else 'A entrada lateral do segundo estagio cobre comprimentos diferentes dos ramos. Candidato a correcao, nao causa RF isolada demonstrada.'),
    resultado_carregado=dict(potencias_W=result['ondas_incidentes_antena_potencia_W'],fases_graus=result['ondas_incidentes_antena_fase_relativa_graus'],dispersao_amplitude_dB=result['dispersao_amplitude_dB'],dispersao_fase_graus=result['dispersao_fase_graus']),
    alerta=('O divisor convergiu em S; sem estudo de sensibilidade nao atribuir toda a diferenca a uma unica juncao ou componente. As pendencias da antena permanecem.' if result['convergiu'] else 'Sem convergencia completa e sem estudo de sensibilidade nao atribuir toda a diferenca a uma unica juncao ou componente.'))
(ROOT/'diagnostico_divisao.json').write_text(json.dumps(diagnosis,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
fig,axs=plt.subplots(1,2,figsize=(11,4.7));x=np.arange(6)
axs[0].bar(x,result['ondas_incidentes_antena_potencia_W']);axs[0].axhline(1/6,color='gray',ls='--',label='Referência direta: 1/6 W');axs[0].set_ylabel('Potência incidente na antena (W)');axs[0].legend(fontsize=8)
axs[1].bar(x,result['ondas_incidentes_antena_fase_relativa_graus']);axs[1].set_ylabel('Fase relativa a R2_A (graus)')
for ax in axs:ax.set_xticks(x,['R1_A','R1_B','R2_A','R2_B','R3_A','R3_B']);ax.grid(axis='y',alpha=.2)
fig.suptitle('Distribuição real com a antena conectada — resultado preliminar\nDuas fontes iguais/em fase: desequilíbrio de %.2f dB e %.2f°'%(result['dispersao_amplitude_dB'],result['dispersao_fase_graus']))
fig.tight_layout(rect=(0,0,1,.85));fig.savefig(ROOT/'distribuicao.png',dpi=180);plt.close(fig)
print(json.dumps(diagnosis,indent=2))
