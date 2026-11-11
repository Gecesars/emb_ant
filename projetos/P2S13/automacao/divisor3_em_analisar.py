"""Conecta o S8 EM ao S6 da antena; calcula duas entradas e campos H/V."""
from pathlib import Path
import sys,json,re,csv,hashlib,os
import numpy as np
import skrf as rf
from skrf.circuit import Circuit
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
REPO=Path(__file__).resolve().parents[3];ROOT=Path(os.environ.get('P2S13_DIV3_ROOT','D:/dev/EMBRAER/P2S13/R08_Divisor_HFSS'));ANT=Path('D:/dev/EMBRAER/P2S13/R06_Continuacao_Tres2')
sys.path[:0]=[str(REPO/'projetos/P2M21/automacao'),str(REPO/'automacao/r05'),str(REPO/'automacao/r06')]
from rede_carregada import read_pattern
from oito_celulas_analisar import metrics
from divisor_variantes_comparar import profile_matrix_solves
from auditar_malha import audit
def save(n,v):(ROOT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
cfg=json.loads((ROOT/'configuracao.json').read_text());assert json.loads((ROOT/'estado.json').read_text())['estado']=='CONCLUIDO_AGUARDA_ANALISE'
conv=(ROOT/'convergencia.txt').read_text();grab=lambda patt:re.search(patt,conv)[1]
passes=int(grab(r'Completed\s*:\s*(\d+)'));assert passes<=int(grab(r'Maximum\s*:\s*(\d+)'))==6
assert abs(float(re.search(r'^Target\s*:\s*([\d.eE+-]+)',conv,re.M)[1])-.05)<1e-10
delta=float(grab(r'Current\s*:\s*([\d.eE+-]+)'));consec=int(grab(r'Current Consecutive Passes\s*:\s*(\d+)'))
results=(ROOT/cfg['native']).with_suffix('.aedtresults');metas=[]
for p in results.rglob('*.EMConvData'):
    t=p.read_text()
    if "MaxPasses='6'" in t and "MinPasses='2'" in t and abs(float(re.search("ConvTarget='([^']+)'",t)[1])-.05)<1e-10:metas.append((p,t))
assert len(metas)==1
mp,mt=metas[0];by_pass={}
for b in mt.split("$begin 'QuantityValues'")[1:]:
    b=b.split("$end 'QuantityValues'",1)[0];ds=re.search(r'MaxMagDeltaS\(([^,]+)',b)
    row=dict(passe=int(re.search(r'PassNo=(\d+)',b)[1]),tetraedros=int(float(re.search(r'SolvedElements\(([^,]+)',b)[1])),delta_s=float(ds[1]) if ds else None)
    assert row['passe'] not in by_pass or row==by_pass[row['passe']]
    by_pass[row['passe']]=row
hist=[by_pass[k] for k in sorted(by_pass)];assert len(hist)==passes and abs(hist[-1]['delta_s']-delta)<5e-6
recs=profile_matrix_solves(mp.with_suffix('.profile').read_text(errors='replace'))
adap=[x for x in recs if x['passe_adaptativo'] is not None];assert [x['passe_adaptativo'] for x in adap]==list(range(1,passes+1)) and all(x['nucleos']==14 for x in adap)
messages=json.loads((ROOT/'mensagens.json').read_text())
if list(results.rglob('nominalmesh.g3derr')):mesh=audit(results)
else:
    assert not any(re.search(r'mesh repair|mesh leak|non-planar mesh|outlines.*preserv',m,re.I) for m in messages)
    mesh=dict(reparos_major=0,reparos_minor=0,arquivo_avisos_presente=False,nota='Classic sem g3derr nominal e sem avisos de reparo nas mensagens exportadas.')
save('malha.json',mesh);save('historico_passes.json',hist);save('recursos_matriz.json',recs)
dn=rf.Network(str(ROOT/'divisor.s8p'));an=rf.Network(str(ANT/'centro.s6p'))
names=[p.strip().removesuffix(':1') for p in an.port_names];assert names==['R1_A','R1_B','R2_A','R2_B','R3_A','R3_B']
wanted=['IN_A','IN_B']+names;actual=[p.strip().removesuffix(':1') for p in dn.port_names]
assert set(wanted)==set(actual) and len(dn.f)==len(an.f)==1 and dn.f[0]==an.f[0]==5.17e9
np.testing.assert_allclose(dn.z0,50);np.testing.assert_allclose(an.z0,50)
ix=[actual.index(n) for n in wanted];sd=dn.s[0][np.ix_(ix,ix)];sa=an.s[0]
transfer=np.linalg.solve(np.eye(6)-sd[2:,2:]@sa,sd[2:,:2]);s2=sd[:2,:2]+sd[:2,2:]@sa@transfer
ai=np.ones(2)/np.sqrt(2);a=transfer@ai;b=s2@ai
vs=lambda g:((1+abs(g))/(1-abs(g))).tolist()
pr=float(np.sum(abs(b)**2));pa=float(np.sum(abs(a)**2-abs(sa@a)**2));loss=1-pr-pa
assert pr>=0 and pa>=0 and loss>-1e-8
curves={};cuts={};recomposition={}
for axis in 'HV':
    theta,uniform=read_pattern(ANT/('ALL_'+axis+'.csv'))
    e=np.stack([read_pattern(ANT/(n+'_'+axis+'.csv'))[1] for n in names],axis=-1)
    recomposition[axis]=float(np.max(abs(e@np.ones(6)/np.sqrt(6)-uniform)));assert recomposition[axis]<1e-10
    g=10*np.log10(np.maximum(np.sum(abs(e@a)**2,axis=1),1e-30));curves[axis]=g;cuts[axis]=metrics(theta,g)
    with (ROOT/('diagrama_'+axis+'.csv')).open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['angulo_graus','ganho_realizado_total_dBi','E_Emax']);w.writerows(zip(theta,g,10**((g-g.max())/20)))
convok='Converged : Yes' in conv and delta<=.05 and consec>=2
def export(name,s,ports):
    n=rf.Network(frequency=an.frequency,s=s[None],z0=50,name=name);n.port_names=ports;n.write_touchstone(str(ROOT/name),form='ri')
    np.testing.assert_allclose(rf.Network(str(ROOT/(name+'.s%dp'%len(ports)))).s,n.s,atol=1e-13,rtol=0)
export('divisor_ordenado',sd,wanted);export('conjunto',s2,['IN_A','IN_B'])
dn2=rf.Network(frequency=an.frequency,s=sd[None],z0=50,name='DIV');an.name='ANT'
connections=[[(Circuit.Port(an.frequency,'IN_A'),0),(dn2,0)],[(Circuit.Port(an.frequency,'IN_B'),0),(dn2,1)]]+ [[(dn2,i+2),(an,i)] for i in range(6)]
check=Circuit(connections).network.s[0];error=float(np.max(abs(s2-check)));assert error<1e-12
r=dict(frequencia_GHz=5.17,passes=passes,delta_s=hist[-1]['delta_s'],convergiu=convok,hfss_flag_converged_yes='Converged : Yes' in conv,consecutivos=consec,consecutivos_exigidos=2,nucleos_por_passe=[x['nucleos'] for x in adap],
    fontes_W=[.5,.5],fontes_fase_graus=[0,0],ordem_S8_exportada=actual,ordem_S8_circuito=wanted,
    VSWR_ativo=vs(s2@np.ones(2)),VSWR_outra_casada=vs(np.diag(s2)),cortes=cuts,
    potencia_refletida_W=pr,potencia_aceita_antena_W=pa,perda_divisor_dissipacao_mais_radiacao_W=loss,
    ondas_incidentes_antena_potencia_W=(abs(a)**2).tolist(),ondas_incidentes_antena_fase_relativa_graus=np.angle(a/a[2],deg=True).tolist(),
    dispersao_amplitude_dB=float(np.ptp(20*np.log10(abs(a)))),dispersao_fase_graus=float(np.ptp(np.angle(a/a[2],deg=True))),
    passividade_divisor=float(np.linalg.svd(sd,compute_uv=False)[0]),reciprocidade_divisor=float(np.max(abs(sd-sd.T))),
    passividade_conjunto=float(np.linalg.svd(s2,compute_uv=False)[0]),reciprocidade_conjunto=float(np.max(abs(s2-s2.T))),
    erro_interconexao_scikit=error,recomposicao_uniforme=recomposition,malha_major=mesh['reparos_major'],malha_minor=mesh['reparos_minor'],
    S8_sha256=hashlib.sha256((ROOT/'divisor.s8p').read_bytes()).hexdigest(),S6_sha256=hashlib.sha256((ANT/'centro.s6p').read_bytes()).hexdigest(),
    meta_VSWR_1p25=all(x<=1.25 for x in vs(s2@np.ones(2))+vs(np.diag(s2))),meta_VSWR_ativo_1p25=all(x<=1.25 for x in vs(s2@np.ones(2))),
    meta_ganho_12dBi=cuts['H']['ganho_frontal_dBi']>=12,
    meta_ganho_13dBi=cuts['H']['ganho_frontal_dBi']>=13,antena_auditoria_previa_aprovada=False,
    qualificacao_completa=False,limitacao='Ganho recomposto dos campos da antena; radiacao e interacao espacial direta do divisor/antena nao somadas. S6 previo com pendencias de estabilidade e reciprocidade. '+('Resistor nominal, sem caracterizacao de lote.' if cfg['resistores'] else 'Divisao direta sem isolamento resistivo entre saidas.'))
save('resultado.json',r)
fig,axs=plt.subplots(1,2,figsize=(11,6.5),subplot_kw={'projection':'polar'})
for ax,axis in zip(axs,'HV'):
    g=curves[axis];ax.plot(np.deg2rad(theta),10**((g-g.max())/20));ax.set_theta_zero_location('N');ax.set_theta_direction(-1);ax.set_ylim(0,1.05);ax.set_rticks([.25,.5,.75,1]);ax.set_rlabel_position(75)
    ax.set_title('%s: %.2f° | máximo %+.2f°'%(axis,cuts[axis]['abertura_graus'],cuts[axis]['pico_graus']),pad=22,fontsize=10)
fig.suptitle('Divisor duplo 1:3 HFSS + antena S6 — 5,17 GHz — E/Emax\nDuas entradas de 0,5 W / 0° | %d passes | ΔS %.5f\nPRELIMINAR: divisor com %d/2 passes consecutivos; antena com auditoria pendente'%(passes,hist[-1]['delta_s'],consec),fontsize=11)
fig.text(.5,.025,'G frontal %.3f dBi | VSWR ativo A/B %.3f / %.3f'%(cuts['H']['ganho_frontal_dBi'],*r['VSWR_ativo']),ha='center')
fig.text(.5,.065,'Picos e cortes nesta figura: grade de 0,25°. A verificacao vertical fina usa grade de 0,01° em arquivo separado.',ha='center',fontsize=8)
fig.subplots_adjust(top=.73,bottom=.14,wspace=.26);fig.savefig(ROOT/'polar_HV.png',dpi=180);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(12,5))
for ax,axis in zip(axs,'HV'):
    _,e=read_pattern(ANT/('ALL_'+axis+'.csv'));ax.plot(theta,10*np.log10(np.sum(abs(e)**2,axis=1)),label='Seis fontes diretas');ax.plot(theta,curves[axis],label='Divisor HFSS + S6')
    ax.set(xlim=(-90,90),ylim=(-25,16),title=axis,xlabel='Ângulo (°)',ylabel='Ganho realizado total (dBi)');ax.grid(alpha=.2);ax.legend(fontsize=9)
fig.suptitle('Comparação — 5,17 GHz — 1 W incidente total\nAcoplamento conduzido e perdas da rede incluídos; campos da antena recompostos')
fig.tight_layout(rect=(0,0,1,.87));fig.savefig(ROOT/'comparacao_HV.png',dpi=180);plt.close(fig)
print(json.dumps({k:r[k] for k in ['passes','delta_s','convergiu','VSWR_ativo','VSWR_outra_casada','cortes','dispersao_fase_graus']},indent=2))
