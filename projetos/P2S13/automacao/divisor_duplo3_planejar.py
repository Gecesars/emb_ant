"""Plano de circuito 1:3 duplo; carrega S6 real, sem novo solve FEM ou sweep.

Modelo microstrip distribuido, nao geometria EM do divisor. Nunca altera S6.
"""
from pathlib import Path
import json,sys,hashlib,csv
from functools import lru_cache
import numpy as np
import skrf as rf
from skrf.media import MLine,DefinedGammaZ0
from skrf.circuit import Circuit
from scipy.optimize import brentq,differential_evolution
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyArrowPatch

REPO=Path(__file__).resolve().parents[3]
SOURCE=Path('D:/dev/EMBRAER/P2S13/R06_Continuacao_Tres2')
ROOT=Path('D:/dev/EMBRAER/P2S13/R07_Divisor_Duplo3')
ROOT.mkdir(exist_ok=True)
sys.path[:0]=[str(REPO/'automacao/r05'),str(REPO/'projetos/P2M21/automacao')]
from rede_carregada import read_pattern
from oito_celulas_analisar import metrics
F=rf.Frequency(5.17,5.17,1,'ghz')
PORTS=['R1_A','R1_B','R2_A','R2_B','R3_A','R3_B']
@lru_cache(maxsize=2048)
def medium(z):
    def m(w):return MLine(frequency=F,w=w,h=.00152,t=.000035,ep_r=2.94,
        tand=.0016,rho=1/5.8e7,rough=.5e-6,diel='frequencyinvariant',z0_port=50)
    w=brentq(lambda w:m(w).z0[0].real-z,.0001,.02,xtol=1e-13)
    return m(w)
M50=medium(50.);MQ=medium(float(50*np.sqrt(3)));LQ=float(np.pi/(2*MQ.beta[0]))

def parts(z=50.,lin=5.,lout=100.,isolated=True):
    components=[('IN',0,1,medium(float(z)).line(lin/1000,unit='m',name='IN'))]
    for i in range(3):
        components.extend([(f'Q{i}',1,2+i,MQ.line(LQ,unit='m',name=f'Q{i}')),
            (f'O{i}',2+i,5+i,M50.line(lout/1000,unit='m',name=f'O{i}'))])
    if isolated:
        for i,j in [(2,3),(3,4),(4,2)]:
            name=f'R{i}{j}'
            components.append((name,i,j,Circuit.SeriesImpedance(F,150,name)))
    return components

def nodal(components):
    y=np.zeros((8,8),complex)
    for name,i,j,net in components:
        y[np.ix_([i,j],[i,j])]+=net.y[0]
    ext=[0,5,6,7];internal=[1,2,3,4]
    yr=y[np.ix_(ext,ext)]-y[np.ix_(ext,internal)]@np.linalg.solve(y[np.ix_(internal,internal)],y[np.ix_(internal,ext)])
    return rf.Network(frequency=F,y=yr[None],z0=50,name='Divisor_1x3')

def independent(components):
    nodes=[[] for _ in range(8)]
    for name,i,j,net in components:nodes[i].append((net,0));nodes[j].append((net,1))
    for name,node in zip(['EXT_IN','EXT_O1','EXT_O2','EXT_O3'],[0,5,6,7]):nodes[node].append((Circuit.Port(F,name),0))
    return Circuit(nodes).network

def dual(n):
    s=np.zeros((8,8),complex)
    for ix in [[0,2,4,6],[1,3,5,7]]:s[np.ix_(ix,ix)]=n.s[0]
    return s

ant=rf.Network(str(SOURCE/'centro.s6p'))
assert ant.nports==6 and list(ant.f)==[5.17e9]
names=[p.strip().removesuffix(':1') for p in ant.port_names]
assert names==PORTS
np.testing.assert_allclose(ant.z0,50)
SA=ant.s[0]
fields={}
for axis in 'HV':
    fields[axis]=np.stack([read_pattern(SOURCE/(p+'_'+axis+'.csv'))[1] for p in PORTS],axis=-1)
angles=read_pattern(SOURCE/'ALL_H.csv')[0]
for axis in 'HV':
    np.testing.assert_allclose(fields[axis]@np.ones(6)/np.sqrt(6),read_pattern(SOURCE/('ALL_'+axis+'.csv'))[1],atol=2e-13,rtol=2e-12)

def load(sd):
    transfer=np.linalg.solve(np.eye(6)-sd[2:,2:]@SA,sd[2:,:2])
    se=sd[:2,:2]+sd[:2,2:]@SA@transfer
    a=transfer@np.ones(2)/np.sqrt(2)
    return se,a

def vs(g):return ((1+np.abs(g))/(1-np.abs(g))).tolist()

def evaluate(n):
    sd=dual(n);s,a=load(sd);active=s@np.ones(2)
    refl=float(np.sum(abs(s@np.ones(2)/np.sqrt(2))**2))
    accepted=float(np.sum(abs(a)**2-abs(SA@a)**2))
    loss=1-refl-accepted
    assert refl>=0 and accepted>=0 and loss>=-1e-9
    curves={axis:10*np.log10(np.maximum(np.sum(abs(e@a)**2,axis=1),1e-30)) for axis,e in fields.items()}
    c={axis:metrics(angles,g) for axis,g in curves.items()}
    phase=np.angle(a/a[2],deg=True)
    r=dict(VSWR_ativo=vs(active),VSWR_outra_casada=vs(np.diag(s)),
        ganho_frontal_dBi=c['H']['ganho_frontal_dBi'],H_graus=c['H']['abertura_graus'],V_graus=c['V']['abertura_graus'],
        pico_H_graus=c['H']['pico_graus'],pico_V_graus=c['V']['pico_graus'],SLL_V_dB=c['V']['SLL']['nivel_dB'],
        potencia_refletida_W=refl,potencia_aceita_antena_W=accepted,dissipacao_divisor_W=loss,
        potencia_incidente_antena_W=(abs(a)**2).tolist(),fase_incidente_relativa_graus=phase.tolist(),
        dispersao_amplitude_dB=float(np.ptp(20*np.log10(abs(a)))),dispersao_fase_graus=float(np.ptp(phase)),
        maior_singular_divisor=float(np.linalg.svd(sd,compute_uv=False)[0]),
        maior_singular_conjunto=float(np.linalg.svd(s,compute_uv=False)[0]),
        reciprocidade_divisor=float(np.max(abs(sd-sd.T))),reciprocidade_conjunto=float(np.max(abs(s-s.T))))
    return r,s,sd,curves,a

def export(name,s,names):
    n=rf.Network(frequency=F,s=s[None],z0=50,name=name);n.port_names=names
    n.write_touchstone(str(ROOT/name),form='ri')
    recovered=rf.Network(str(ROOT/(name+'.s%dp'%len(s))))
    np.testing.assert_allclose(recovered.s,n.s,atol=1e-13,rtol=0)

def save(name,data):
    (ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    # Benchmark analitico independente: Wilkinson ideal 3 vias em lambda/4.
    m=DefinedGammaZ0(F,z0_port=50,z0=50*np.sqrt(3),gamma=1j)
    nets=[m.line(np.pi/2,unit='m',name=f'q{i}') for i in range(3)]
    nodes=[[(n,0) for n in nets]+[(Circuit.Port(F,'P0'),0)]]
    res=[Circuit.SeriesImpedance(F,150,f'r{i}') for i in range(3)]
    for i in range(3):nodes.append([(nets[i],1),(Circuit.Port(F,f'P{i+1}'),0),(res[i],0),(res[(i-1)%3],1)])
    ideal=Circuit(nodes).network.s[0];target=np.zeros((4,4),complex);target[0,1:]=target[1:,0]=-1j/np.sqrt(3)
    np.testing.assert_allclose(ideal,target,atol=1e-13)
    cases={};models={}
    for name,iso in [('T_nao_isolado',False),('Wilkinson_sem_ajuste',True)]:
        p=parts(isolated=iso);n=nodal(p);error=float(np.max(abs(n.s-independent(p).s)));assert error<1e-10
        cases[name]=evaluate(n)[0];models[name]=n;cases[name]['erro_validacao_nodal_circuit']=error
    def objective(x):
        s,_=load(dual(nodal(parts(z=x[0],lin=x[1]))))
        return max(abs(s@np.ones(2)).max(),abs(np.diag(s)).max())
    opt=differential_evolution(objective,[(35,80),(1,20)],seed=5170,popsize=10,maxiter=90,tol=1e-7,polish=True)
    # Dimensoes praticas arredondadas, sem relatar o otimo matematico como fabricacao.
    z=float(opt.x[0]);lin=round(float(opt.x[1]),2);w=round(float(medium(z).w*1000),3)
    zround=brentq(lambda zz:float(medium(float(zz)).w)*1000-w,35.,80.)
    p=parts(z=zround,lin=lin);n=nodal(p);error=float(np.max(abs(n.s-independent(p).s)));assert error<1e-10
    result,s,sd,curves,a=evaluate(n);cases['Wilkinson_ajustado']=result;models['Wilkinson_ajustado']=n
    result['erro_validacao_nodal_circuit']=error
    for name,model in models.items():
        rr,ss,dd,_,_=evaluate(model);export(name+'_duplo',dd,['IN_A','IN_B']+PORTS);export(name+'_conjunto',ss,['IN_A','IN_B'])
    export('Wilkinson_ajustado_1x3',n.s[0],['IN','R1','R2','R3'])
    # Sensibilidade ao resultado anterior: mesma rede, sem corrigir matrizes.
    sa6=rf.Network(str(SOURCE/'referencia6/centro.s6p')).s[0]
    tr6=np.linalg.solve(np.eye(6)-sd[2:,2:]@sa6,sd[2:,:2])
    ss6=sd[:2,:2]+sd[:2,2:]@sa6@tr6
    save('sensibilidade_6_8.json',dict(rede_identica=True,
        passes6_VSWR_ativo=vs(ss6@np.ones(2)),passes6_VSWR_casado=vs(np.diag(ss6)),
        passes8_VSWR_ativo=result['VSWR_ativo'],passes8_VSWR_casado=result['VSWR_outra_casada'],
        nota='Comparacao de dados preliminares; nao e tolerancia ou validacao de convergencia.'))
    # Interconexao completa conferida por segundo algoritmo scikit-rf Circuit.
    dn=rf.Network(frequency=F,s=sd[None],z0=50,name='DIV');an=ant.copy();an.name='ANT'
    connections=[[(Circuit.Port(F,'IN_A'),0),(dn,0)],[(Circuit.Port(F,'IN_B'),0),(dn,1)]]
    connections.extend([[(dn,i+2),(an,i)] for i in range(6)])
    alternate=Circuit(connections).network.s[0]
    err_loaded=float(np.max(abs(alternate-s)));assert err_loaded<1e-12
    measured=models['Wilkinson_ajustado'].s[0]
    nominal_power=abs(measured[1:,0])**2
    param=dict(frequencia_GHz=5.17,modelo='MLine Hammerstad-Jensen + Kirschning-Jansen; diel frequencyinvariant',
        material='ZYF300CA-C nominal',espessura_dieletrica_mm=1.52,epsilon_r=2.94,tan_delta=.0016,cobre_um=35,
        condutividade_cobre_S_m=5.8e7,rugosidade_RMS_assumida_um=.5,
        Z_saida_ohm=50.,largura_saida_mm=float(M50.w*1000),comprimento_saida_mm=100.,
        Z_quarto_onda_ohm=float(50*np.sqrt(3)),largura_quarto_onda_mm=float(MQ.w*1000),comprimento_quarto_onda_mm=LQ*1000,
        resistores_delta_por_polarizacao_ohm=[150,150,150],quantidade_total_resistores=6,
        Z_ajuste_entrada_ohm=zround,largura_ajuste_entrada_mm=w,comprimento_ajuste_entrada_mm=lin,
        potencia_nominal_por_saida_W=(.5*nominal_power).tolist(),
        perda_excedente_nominal_dB=(-10*np.log10(3*nominal_power)).tolist(),
        desbalanceamento_nominal_amplitude_dB=float(np.ptp(20*np.log10(abs(measured[1:,0])))),
        desbalanceamento_nominal_fase_graus=float(np.ptp(np.angle(measured[1:,0],deg=True))),
        placa_reserva_mm=[220,60],centros_saidas_X_mm=[-93.49083158696,2.50916841304,98.50916841304],centros_saidas_Y_mm=[-18,18],
        nota_mecanica='Reserva de envelope, nao layout roteado. Saidas alinhadas aos seis cabos existentes de 50mm; verificar espaco traseiro/curvas/soldas no CAD antes de fabricar.',
        limitacoes=['Divisor modelado em circuito, nao simulado em HFSS; ENIG, T-juncoes, curvas, acoplamento de trilhas, parasitas dos resistores/soldas nao modelados.',
            'S6 tem DeltaS convergido, mas nove campos e auditoria estrita de reciprocidade pendentes. Resultado carregado preliminar.',
            'Seis cabos de 50mm e perdas das PCBs radiantes ja incluidos em S6. N e alimentacao externa ideais. Nao adicionados outros cabos.',
            'Somente 5.17GHz; nao representa banda ou tolerancias de fabricacao.'])
    audit=dict(benchmark_3vias_ideal_erro=float(np.max(abs(ideal-target))),interconexao_segundo_algoritmo_erro=err_loaded,
        S6_sha256=hashlib.sha256((SOURCE/'centro.s6p').read_bytes()).hexdigest(),S6_alterada=False,
        S6_auditoria_aprovada=False,sem_novo_solve_HFSS=True,sem_sweep=True,
        frequencia_GHz=5.17,entradas_W=[.5,.5],fases_graus=[0,0],modelo_distribuidor_EM_validado=False)
    save('parametros.json',param);save('comparacao_circuitos.json',cases);save('verificacao.json',audit)
    for axis,g in curves.items():
        with (ROOT/('diagrama_'+axis+'.csv')).open('w',newline='') as f:
            cw=csv.writer(f);cw.writerow(['angulo_graus','ganho_realizado_total_dBi','E_Emax']);cw.writerows(zip(angles,g,10**((g-g.max())/20)))
    make_plots(cases,curves,param)
    print(json.dumps(dict(casos=cases,parametros=param,auditoria=audit),indent=2))

def make_plots(cases,curves,param):
    fig,axs=plt.subplots(1,2,figsize=(11,6.2),subplot_kw={'projection':'polar'})
    for ax,axis in zip(axs,'HV'):
        t,e=read_pattern(SOURCE/('ALL_'+axis+'.csv'));g0=10*np.log10(np.sum(abs(e)**2,axis=1));g=curves[axis]
        ax.plot(np.deg2rad(angles),10**((g0-g0.max())/20),label='Seis entradas diretas',lw=1.2)
        ax.plot(np.deg2rad(angles),10**((g-g.max())/20),label='Divisor duplo: modelo de circuito',lw=1.2)
        ax.set_theta_zero_location('N');ax.set_theta_direction(-1);ax.set_ylim(0,1.05);ax.set_rticks([.25,.5,.75,1]);ax.set_rlabel_position(75);ax.set_title(axis,pad=18)
    fig.suptitle('Planejamento preliminar — divisor duplo 1:3 carregado pelo S6\n5,17 GHz | duas entradas de 0,5 W / 0° | E/Emax\nDivisor ainda sem validação EM; limitações da antena preservadas',fontsize=11)
    fig.legend(*axs[0].get_legend_handles_labels(),loc='lower center',ncol=2,fontsize=9)
    fig.subplots_adjust(top=.74,bottom=.15,wspace=.25);fig.savefig(ROOT/'polar_conjunto.png',dpi=170);plt.close(fig)
    fig,ax=plt.subplots(figsize=(12,7));ax.set_xlim(0,12);ax.set_ylim(0,7);ax.axis('off')
    ax.text(6,6.8,'DIVISOR DUPLO 1:3 — PLANO DE CIRCUITO',ha='center',fontsize=15,weight='bold')
    ax.text(6,6.38,'Dois circuitos idênticos e independentes; uma entrada por polarização',ha='center',fontsize=11)
    for pol,y,color in [('A',4.9,'#175786'),('B',2.8,'#bb6030')]:
        ax.text(.2,y,f'IN_{pol}\n50 Ω\n0,5 W / 0°',ha='left',va='center',color=color)
        ax.add_patch(Rectangle((1.55,y-.46),2.5,.92,fill=False,ec=color,lw=1.8))
        ax.text(2.8,y,f'Ajuste comum\n{param["Z_ajuste_entrada_ohm"]:.2f} Ω / {param["comprimento_ajuste_entrada_mm"]:.2f} mm',ha='center',va='center',fontsize=10)
        ax.plot([1.1,1.55],[y,y],c=color)
        ax.add_patch(Rectangle((4.5,y-.67),2.7,1.34,fill=False,ec=color,lw=1.8))
        ax.text(5.85,y,'Wilkinson 1:3\n3 × 86,60 Ω / 90°\nΔ: 3 × 150 Ω',ha='center',va='center',fontsize=10)
        ax.plot([4.05,4.5],[y,y],c=color)
        for i,dy in enumerate([.5,0,-.5]):
            yy=y+dy;ax.plot([7.2,10.25],[yy,yy],c=color)
            ax.text(8.65,yy+.07,'50 Ω / 100 mm',ha='center',fontsize=9,color=color)
            ax.text(10.4,yy,f'R{i+1}_{pol}',va='center',fontsize=11,color=color)
    ax.text(6,1.3,'Seis saídas → cabos físicos existentes de 50 mm → três placas de dois elementos\nCabos, divisores 1:2 e acoplamento entre placas já fazem parte do S6 do HFSS.',ha='center',va='center',fontsize=10)
    ax.text(6,.42,'PRELIMINAR: microstrip distribuído + resistores ideais. Sem EM de junções, curvas, ENIG e resistores.\nReserva mecânica: PCB traseira 220 × 60 mm; roteamento e fixação ainda a detalhar.',ha='center',fontsize=9,color='#8b2626')
    fig.tight_layout();fig.savefig(ROOT/'plano_divisor.png',dpi=170);plt.close(fig)

if __name__=='__main__':main()
