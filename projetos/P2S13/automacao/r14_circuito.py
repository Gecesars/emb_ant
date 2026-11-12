"""Interligar S8/S6 e seis coaxiais por ondas complexas, para conferir no Nexxim."""
from pathlib import Path
import sys,json,csv,hashlib
import numpy as np
import skrf as rf
from skrf.circuit import Circuit
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).parent;REPO=HERE.parents[2];sys.path[:0]=[str(HERE),str(REPO/'automacao/r05'),str(REPO/'projetos/P2M21/automacao')]
from r14_auditar_em import run,read
from rede_carregada import read_pattern
from oito_celulas_analisar import metrics
ROOT=Path('D:/dev/EMBRAER/P2S13/R14_Compacto_Simetrico_SemRadome/c00');ANT=ROOT/'antena';DIV=ROOT/'divisor';OUT=ROOT/'circuito';OUT.mkdir(exist_ok=True)
cfg=read(ROOT/'configuracao.json');aa,an=run(ANT,'centro.s6p');da,dn=run(DIV,'divisor.s8p')
assert aa['fisicamente_consistente'] and da['fisicamente_consistente'],'Bloco EM inconsistente; nao sintetizar resultado aprovado'
names=['R1_A','R1_B','R2_A','R2_B','R3_A','R3_B'];wanted=['IN_A','IN_B']+names
def order(net,labels):
    orig=[x.strip().removesuffix(':1') for x in net.port_names];assert set(orig)==set(labels)
    ix=[orig.index(x) for x in labels];return net.s[0][np.ix_(ix,ix)]
sa=order(an,names);sd=order(dn,wanted)
f=5.17e9;omega=2*np.pi*f;mu=4e-7*np.pi;eps=8.8541878128e-12;ri=.45975e-3;rd=1.515e-3;er=2.036363533774732;td=.00027683054882040843;sigma=5.8e7
rs=np.sqrt(np.pi*f*mu/sigma);rr=rs/(2*np.pi)*(1/ri+1/rd);ll=mu/(2*np.pi)*np.log(rd/ri);cc=2*np.pi*eps*er/np.log(rd/ri);gg=omega*cc*td
gamma=np.sqrt((rr+1j*omega*ll)*(gg+1j*omega*cc));zc=np.sqrt((rr+1j*omega*ll)/(gg+1j*omega*cc));length=cfg['cabos']['comprimento_entre_portas_EM_mm']/1000
medium=rf.media.DefinedGammaZ0(an.frequency,gamma=gamma,z0=zc,z0_port=50);tl=medium.line(length,unit='m');st=tl.s[0]
r1,t12,t21,r2=st[0,0],st[0,1],st[1,0],st[1,1];eye=np.eye(6);F=np.linalg.inv(eye-sd[2:,2:]*r1)
sb=np.zeros((8,8),complex);sb[:2,:2]=sd[:2,:2]+sd[:2,2:]@F@sd[2:,:2]*r1
sb[:2,2:]=sd[:2,2:]@(r1*F@sd[2:,2:]*t12+t12*eye)
sb[2:,:2]=t21*F@sd[2:,:2];sb[2:,2:]=t21*F@sd[2:,2:]*t12+r2*eye
transfer=np.linalg.solve(eye-sb[2:,2:]@sa,sb[2:,:2]);s2=sb[:2,:2]+sb[:2,2:]@sa@transfer
incident=np.ones(2)/np.sqrt(2);a=transfer@incident;ba=sa@a;refl=s2@incident;x=F@(sd[2:,:2]@incident+sd[2:,2:]@ba*t12);y=r1*x+t12*ba
pa=float(np.sum(abs(a)**2-abs(ba)**2));pd=float(np.sum(abs(x)**2-abs(y)**2));pr=float(np.sum(abs(refl)**2));ld=1-pr-pd;lc=pd-pa
assert min(pr,pa,ld,lc)>-1e-8 and abs(pr+pa+ld+lc-1)<1e-10
def export(name,s,labels):
    n=rf.Network(frequency=an.frequency,s=np.asarray(s)[None],z0=50,name=name);n.port_names=labels;n.write_touchstone(str(OUT/name),form='ri')
    back=rf.Network(str(OUT/(name+'.s%dp'%len(labels))));np.testing.assert_allclose(back.s,n.s,atol=1e-13,rtol=0)
export('divisor',sd,wanted);export('antena',sa,names);export('coaxial',st,['DIV','ANT']);export('conjunto',s2,['IN_A','IN_B'])
# Segundo algoritmo de conexao, com cada um dos seis cabos explicitamente separado.
nd=rf.Network(frequency=an.frequency,s=sd[None],z0=50,name='DIV');na=rf.Network(frequency=an.frequency,s=sa[None],z0=50,name='ANT')
nodes=[[(nd,i),(Circuit.Port(an.frequency,'IN_'+p),0)] for i,p in enumerate('AB')]
for i in range(6):
    cable=tl.copy();cable.name='C%d'%i;nodes.extend([[(nd,i+2),(cable,0)],[(cable,1),(na,i)]])
independent=Circuit(nodes).network.s[0];error=float(np.max(abs(independent-s2)));assert error<1e-10
cuts={};curves={};uniform_error={}
for axis in ['H','V','V_fino']:
    theta,euniform=read_pattern(ANT/('ALL_'+axis+'.csv'));efields=np.stack([read_pattern(ANT/(n+'_'+axis+'.csv'))[1] for n in names],axis=-1)
    uniform_error[axis]=float(np.max(abs(efields@np.ones(6)/np.sqrt(6)-euniform)));assert uniform_error[axis]<1e-10
    g=10*np.log10(np.maximum(np.sum(abs(efields@a)**2,axis=1),1e-30));curves[axis]=(theta,g)
    if axis!='V_fino':
        cuts[axis]=metrics(theta,g)
        if not cuts[axis]['SLL']['lobos']:cuts[axis]['SLL']['nivel_dB']=None
    with (OUT/('diagrama_'+axis+'.csv')).open('w',newline='') as fcsv:
        w=csv.writer(fcsv);w.writerow(['angulo_graus','ganho_realizado_total_dBi','E_Emax']);w.writerows(zip(theta,g,10**((g-g.max())/20)))
tf,gf=curves['V_fino'];ip=np.argmax(gf);assert 0<ip<len(tf)-1;p=np.polyfit(tf[ip-1:ip+2],gf[ip-1:ip+2],2);vp=float(-p[1]/(2*p[0]));half=min(abs(x) for x in cuts['V']['cruzamentos_graus']);angles=np.arange(0,half+.00001,.01)
asym=float(np.max(abs(np.interp(angles,tf,gf)-np.interp(-angles,tf,gf))));vs=lambda g:((1+abs(g))/(1-abs(g))).tolist()
active=vs(s2@np.ones(2));matched=vs(np.diag(s2))
th,gh=curves['H'];ih=int(np.argmax(gh));hglobal=dict(angulo_graus=float(th[ih]),ganho_dBi=float(gh[ih]))
depression=hglobal['ganho_dBi']-cuts['H']['ganho_frontal_dBi']
criteria=dict(VSWR_ativo=max(active)<=1.25,ganho_frontal=cuts['H']['ganho_frontal_dBi']>=12,H_frontal_ate_05dB=depression<=.5,
    maximo_vertical=abs(vp)<=.5,simetria_vertical=asym<=.2)
branch_info=[dict(porta=n,potencia_incidente_W=float(abs(a[i])**2),fase_relativa_R2A_graus=float(np.angle(a[i]/a[2],deg=True))) for i,n in enumerate(names)]
field_history=aa['monitoramento_campos']['historico']
field_deltas=[p['delta_campo_max_dB'] for p in field_history[-2:]]
field_stable=all(x is not None and x<=.1 for x in field_deltas)
matched_div={}
for ip,pol in enumerate('AB'):
    inds=[2+ip,4+ip,6+ip];trans=sd[inds,ip];phase=np.angle(trans/trans[0],deg=True)
    matched_div[pol]=dict(VSWR=float(vs(np.array([sd[ip,ip]]))[0]),perda_excedente_dB=float(-10*np.log10(np.sum(abs(trans)**2))),
      dispersao_amplitude_dB=float(np.ptp(20*np.log10(abs(trans)))),dispersao_fase_graus=float(np.ptp(phase)),fase_relativa_graus=phase.tolist(),
      maior_acoplamento_entre_saidas_dB=float(20*np.log10(max(abs(sd[i,j]) for i in inds for j in inds if i!=j))))
result=dict(revisao='R14_C09_sem_radome',frequencia_GHz=5.17,entradas_W=[.5,.5],fases_graus=[0,0],VSWR_ativo=active,VSWR_outra_casada=matched,
    cortes=cuts,pico_H_global=hglobal,queda_H_0_vs_pico_dB=depression,pico_V_fino_graus=vp,assimetria_principal_V_dB=asym,divisor_casado=matched_div,ramais_carregados=branch_info,
    isolamento_entradas_divisor_dB=float(-20*np.log10(abs(sd[0,1]))),
    potencia=dict(incidente_W=1,refletida_W=pr,aceita_antena_W=pa,perda_divisor_W=ld,perda_cabos_W=lc,balanco_aprovado=True),
    cabo=dict(comprimento_mm=length*1000,perda_insercao_dB=float(-20*np.log10(abs(st[1,0]))),fase_graus=float(np.angle(st[1,0],deg=True)),RLGC_por_m=dict(R_ohm=rr,L_H=ll,G_S=gg,C_F=cc),eps_r=er,tand=td,condutividade_S_m=sigma),
    convergencia=dict(antena={k:aa[k] for k in ['passes','delta_s','convergiu']},divisor={k:da[k] for k in ['passes','delta_s','convergiu']}),
    metas={k:bool(v) for k,v in criteria.items()},metas_numericas_atendidas=bool(all(criteria.values())),nexxim_pendente=True,
    campos_monitorados=dict(ultimos_deltas_max_dB=field_deltas,referencia_dB=.1,estabilidade_observada=field_stable,criterio_somente_monitoramento=True),
    erro_circuito_independente=error,recomposicao_uniforme_erro=uniform_error,
    limites='HFSS separado: acoplamento entre radiadores incluido no S6; nao inclui acoplamento espacial antena-divisor, radiacao dos cabos nem contribuicao direta do campo do divisor. Cabos somente RLGC no circuito; sem radome e sem conectores N.')
(OUT/'resultado.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
np.savez(OUT/'ondas.npz',incidente_antena=a,refletida_antena=ba,saida_divisor=x,retorno_divisor=y,transferencia=transfer)
fig,axs=plt.subplots(1,2,figsize=(12,6),subplot_kw={'projection':'polar'})
for ax,axis in zip(axs,'HV'):
    theta,g=curves[axis];ax.plot(np.deg2rad(theta),10**((g-g.max())/20));ax.set_theta_zero_location('N');ax.set_theta_direction(-1);ax.set_ylim(0,1.05);ax.set_rticks([.25,.5,.75,1]);ax.set_rlabel_position(70)
    ax.set_title('%s: %.2f° | pico %+.3f°'%(axis,cuts[axis]['abertura_graus'],vp if axis=='V' else cuts[axis]['pico_graus']),pad=20)
fig.suptitle('C09 compacto — antena sem radome — 5,17 GHz\nDuas entradas 0,5 W / 0° | cabos iguais no circuito | E/Emax')
if not (aa['convergiu'] and da['convergiu'] and field_stable and all(criteria.values())):fig.text(.5,.88,'PRELIMINAR — conferir metas e estabilidade de campo no relatório',ha='center',color='#a44b00')
fig.text(.5,.025,'G frontal %.3f dBi | VSWR %.3f / %.3f | H(0) %.3f dB abaixo do pico'%(cuts['H']['ganho_frontal_dBi'],*active,depression),ha='center')
fig.subplots_adjust(top=.72,bottom=.12,wspace=.24);fig.savefig(OUT/'polar_HV.png',dpi=170);plt.close(fig)
print(json.dumps(result,indent=2,ensure_ascii=False))
