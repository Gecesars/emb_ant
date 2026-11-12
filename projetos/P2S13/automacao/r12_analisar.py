"""Audita a solucao integral R11, sem impor convergencia pelo limite de passes."""
from pathlib import Path
import os,sys,json,re,csv,hashlib
import numpy as np
import skrf as rf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
REPO=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(REPO/'projetos/P2M21/automacao'),str(REPO/'automacao/r05'),str(REPO/'automacao/r06')]
from divisor_variantes_comparar import profile_matrix_solves
from rede_carregada import read_pattern
from oito_celulas_analisar import metrics
from auditar_malha import audit
from oito_celulas_monitorar import progress
ROOT=Path(os.environ['P2S13_ROOT'])
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(n,v):(ROOT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cfg=read(ROOT/'configuracao.json');conv=(ROOT/'convergencia.txt').read_text()
grab=lambda x:re.search(x,conv)[1]
passes=int(grab(r'Completed\s*:\s*(\d+)'));consec=int(grab(r'Current Consecutive Passes\s*:\s*(\d+)'))
assert passes<=int(grab(r'Maximum\s*:\s*(\d+)'))==6
assert abs(float(re.search(r'^Target\s*:\s*([\d.eE+-]+)',conv,re.M)[1])-.05)<1e-10
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
hist=[by_pass[k] for k in sorted(by_pass)];assert len(hist)==passes
# AEDT usa IDs de variacao distintos para o perfil de recursos e EMConvData.
# Vincular por design/setup, unicidade, passes e identidades dos tetraedros.
prefix=re.fullmatch(r'(DV\d+_S\d+)_V\d+',mp.stem)[1]
profiles=list(mp.parent.glob(prefix+'_V*.profile'));assert len(profiles)==1,profiles
profile_path=profiles[0];profile=profile_path.read_text(errors='replace').replace("\\'","'")
tet_records={};solver_warnings=[]
for m in re.finditer(r"Name='Adaptive Pass (\d+)'(.*?)(?=Name='Adaptive Pass |\Z)",profile,re.S):
    line=next(x for x in m[2].splitlines() if x.strip().startswith("ProfileItem('Simulation Setup '"))
    tet_records[int(m[1])]=int(re.search(r"'Tetrahedra', (\d+)",line)[1])
    for w in re.finditer(r'Matrix solver warning: [^\r\n]+',m[2]):
        residual=re.search(r'maximum residual = ([\d.eE+-]+), average residual = ([\d.eE+-]+)',w[0])
        solver_warnings.append(dict(passe=int(m[1]),mensagem=w[0].rstrip('\\'),
            residuo_maximo=float(residual[1]) if residual else None,
            residuo_medio=float(residual[2]) if residual else None))
assert tet_records=={x['passe']:x['tetraedros'] for x in hist},tet_records
save('conferencia_perfil.json',dict(convergencia=mp.name,perfil=profile_path.name,tetraedros_por_passe=tet_records,aprovado=True))
delta=hist[-1]['delta_s'];recs=profile_matrix_solves(profile)
adap=[x for x in recs if x['passe_adaptativo'] is not None];assert [x['passe_adaptativo'] for x in adap]==list(range(1,passes+1)) and all(x['nucleos']==14 for x in adap)
messages=read(ROOT/'mensagens.json')
if list(results.rglob('nominalmesh.g3derr')):mesh=audit(results)
else:
    assert not any(re.search(r'mesh repair|mesh leak|non-planar mesh|outlines.*preserv',m,re.I) for m in messages)
    mesh=dict(reparos_major=0,reparos_minor=0,arquivo_avisos_presente=False)
save('malha.json',mesh);save('historico_passes.json',hist);save('recursos_matriz.json',recs)
cache=progress(ROOT);save('convergencia_campos.json',cache)
last_fields=[x.get('delta_campo_max_dB') for x in cache['historico'][-2:]]
fields_stable=len(last_fields)==2 and all(x is not None and x<=.1 for x in last_fields)
native=(ROOT/cfg['native']).read_text(errors='replace');sources=re.findall(r'SourceEntry\([^\n]+',native)
assert len(sources)==2 and all("Magnitude='0.5W'" in x and "Phase='0deg'" in x for x in sources)
residual_target=float(re.search(r'IterativeResidual=([\d.eE+-]+)',native)[1])
solver_audit=dict(perfil=profile_path.name,perfil_sha256=sha(profile_path),residuo_configurado=None,tipo='Direct Solver',basis_order=cfg['basis_order'],
    avisos=solver_warnings,aprovado=not solver_warnings,
    nota='Auditoria do perfil de recursos; avisos do solver matricial podem nao aparecer em GetMessages.')
save('auditoria_solver_matricial.json',solver_audit)
n=rf.Network(str(ROOT/'centro.s2p'));assert len(n.f)==1 and n.f[0]==5.17e9
assert [x.strip().removesuffix(':1') for x in n.port_names]==['IN_A','IN_B'];np.testing.assert_allclose(n.z0,50)
s=n.s[0];ai=np.ones(2)/np.sqrt(2);reflected=float(np.sum(abs(s@ai)**2));accepted=1-reflected
sigma=float(np.linalg.svd(s,compute_uv=False)[0]);reciprocity=float(np.max(abs(s-s.T)))
assert sigma<=1+1e-8 and 0<accepted<=1
vs=lambda g:((1+abs(g))/(1-abs(g))).tolist()
cuts={};curves={};recompose={}
for axis in 'HV':
    theta,e=read_pattern(ROOT/('ALL_'+axis+'.csv'))
    individual=np.stack([read_pattern(ROOT/(p+'_'+axis+'.csv'))[1] for p in ['IN_A','IN_B']],axis=-1)
    recompose[axis]=float(np.max(abs(individual@ai-e)));assert recompose[axis]<1e-8
    g=10*np.log10(np.maximum(np.sum(abs(e)**2,axis=1),1e-30));cuts[axis]=metrics(theta,g);curves[axis]=(theta,g)
    with (ROOT/('diagrama_'+axis+'.csv')).open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['angulo_graus','ganho_realizado_total_dBi','E_Emax']);w.writerows(zip(theta,g,10**((g-g.max())/20)))
tf,ef=read_pattern(ROOT/'ALL_V_fino.csv');gf=10*np.log10(np.sum(abs(ef)**2,axis=1));ip=int(np.argmax(gf))
assert 0<ip<len(tf)-1
parab=np.polyfit(tf[ip-1:ip+2],gf[ip-1:ip+2],2);peak_interp=float(-parab[1]/(2*parab[0]))
half=min(abs(x) for x in cuts['V']['cruzamentos_graus']);a=np.arange(0,half+.00001,.01)
asym=float(np.max(abs(np.interp(a,tf,gf)-np.interp(-a,tf,gf))))
converged='Converged : Yes' in conv and delta<=.05 and consec>=2
power=read(ROOT/'potencia.json') if (ROOT/'potencia.json').exists() else None
power_ok=False
if power:
    pa=power['AcceptedPower']['real'][0];pi=power['IncidentPower']['real'][0];pr=power['RadiatedPower']['real'][0]
    power_ok=abs(pi-1)<1e-6 and abs(pa-accepted)<1e-4 and 0<pr<pa+1e-3
    power['balanco_S']=dict(incidente_W=1,refletida_W=reflected,aceita_W=accepted,radiada_W=pr,dissipada_W=pa-pr,aprovado=power_ok)
    save('potencia_conferida.json',power)
active=vs(s@np.ones(2));matched=vs(np.diag(s));g0=cuts['H']['ganho_frontal_dBi']
rfmet=dict(VSWR_ativo=bool(max(active)<=1.25),VSWR_outra_casada=bool(max(matched)<=1.25),ganho=bool(g0>=12),
           pico_vertical=bool(abs(peak_interp)<=.5),simetria_lobo_principal=bool(asym<=.2))
r=dict(revisao=cfg['revisao'],frequencia_GHz=5.17,passes=passes,delta_s=delta,consecutivos=consec,convergiu=converged,
       nucleos=[x['nucleos'] for x in adap],fontes_W=[.5,.5],fontes_fase_graus=[0,0],VSWR_ativo=active,VSWR_outra_casada=matched,
       cortes=cuts,vertical_fino=dict(passo_graus=.01,pico_grade_graus=float(tf[ip]),pico_interpolado_graus=peak_interp,
          assimetria_max_dB=asym,intervalo_simetria_graus=[-half,half],criterio_simetria_dB=.2,criterio_pico_graus=.5),
       passividade_sigma_max=sigma,reciprocidade_erro=reciprocity,recomposicao_erro=recompose,potencia_balanco_aprovado=power_ok,
       malha_major=mesh['reparos_major'],malha_minor=mesh['reparos_minor'],metas=rfmet,
       metas_operacionais=all(rfmet[k] for k in ['VSWR_ativo','ganho','pico_vertical','simetria_lobo_principal']),
       criterio_VSWR_operacional='Duas entradas iguais e em fase; VSWR com outra casada e verificacao adicional, reportada separadamente.',
       validacao_nominal=bool(not solver_warnings and converged and all(rfmet[k] for k in ['VSWR_ativo','ganho','pico_vertical','simetria_lobo_principal']) and power_ok and fields_stable and mesh['reparos_major']==0 and reciprocity<1e-5),
       solver_matricial=solver_audit,
       resultados_fisicamente_consistentes=bool(not solver_warnings and power_ok and reciprocity<1e-5),
       nota_metas='Comparacoes numericas dos valores exportados; uma solucao fisicamente inconsistente nao aprova qualquer meta RF.',
       estabilidade_campos_ultimos_dB=last_fields,estabilidade_campos_aprovada=fields_stable,
       tolerancia_reciprocidade_absoluta=1e-5,nota_reciprocidade='Mantido limiar de auditoria historico. Afericao absoluta reportada; nao equivale a erro de VSWR ou de ganho.',
       limites='Simulacao nominal em um ponto; FR4 isotropico tipico, portas internas ideais. Nao inclui conectores externos, vedacao, cola nem tolerancias de lote.',
       fontes_sha256={n:sha(ROOT/n) for n in ['configuracao.json',cfg['native'],'centro.s2p']})
save('resultado.json',r)
fig,axs=plt.subplots(1,2,figsize=(12,6),subplot_kw={'projection':'polar'})
for ax,axis in zip(axs,'HV'):
    t,g=curves[axis];ax.plot(np.deg2rad(t),10**((g-g.max())/20));ax.set_theta_zero_location('N');ax.set_theta_direction(-1);ax.set_ylim(0,1.05);ax.set_rticks([.25,.5,.75,1]);ax.set_rlabel_position(70)
    ax.set_title('%s: largura %.2f° | pico %+.2f°'%(axis,cuts[axis]['abertura_graus'],cuts[axis]['pico_graus']),pad=20)
fig.suptitle('R12 curvilinear — antena + C08 + radome FR-4 2 mm — 5,17 GHz\nE/Emax | duas entradas 0,5 W / 0° | %d passes | ΔS %.5f'%(passes,delta))
if not r['resultados_fisicamente_consistentes']:
    fig.text(.5,.84,'SOLUÇÃO INVÁLIDA — curvas apenas para diagnóstico',ha='center',color='firebrick',weight='bold')
fig.text(.5,.03,'G frontal %.3f dBi | VSWR ativo %.3f / %.3f | %s'%(g0,*active,'CONVERGIU' if converged else 'NAO CONVERGIU'),ha='center')
fig.subplots_adjust(top=.72,bottom=.12,wspace=.24);fig.savefig(ROOT/'polar_HV.png',dpi=170);plt.close(fig)
fig,ax=plt.subplots(figsize=(8,5));ax.plot(tf,gf-gf.max(),label='V(θ)');ax.plot(tf,gf[::-1]-gf.max(),'--',label='V(−θ)');ax.axvline(0,color='gray',lw=.8);ax.set(xlim=(-10,10),ylim=(-12,.2),xlabel='Ângulo (°)',ylabel='Ganho normalizado (dB)',title='Simetria vertical — pico interpolado %+.4f°'%peak_interp);ax.grid(alpha=.3);ax.legend()
if not r['resultados_fisicamente_consistentes']:
    fig.suptitle('SOLUÇÃO INVÁLIDA — apenas diagnóstico',color='firebrick',weight='bold')
fig.tight_layout();fig.savefig(ROOT/'simetria_vertical.png',dpi=170);plt.close(fig)
print(json.dumps(r,indent=2,ensure_ascii=False))
