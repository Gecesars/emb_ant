"""Guia local de casamento C09: alteracao comum das duas secoes, EM obrigatorio."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
import skrf as rf
from skrf.media import MLine
from scipy.optimize import differential_evolution
HERE=Path(__file__).parent;REPO=HERE.parents[2]
sys.path[:0]=[str(REPO/'automacao/r05'),str(REPO/'projetos/P2M21/automacao')]
from rede_carregada import read_pattern
from oito_celulas_analisar import metrics
BASE=Path('D:/dev/EMBRAER/P2S13/R14_Compacto_Simetrico_SemRadome/c00')
ROOT=Path('D:/dev/EMBRAER/P2S13/R15_Casamento_C09');ROOT.mkdir(exist_ok=True)
dc=json.loads((BASE/'divisor/configuracao.json').read_text());p=dc['parametros'];total=p['comprimento_por_ramal_mm']
dn=rf.Network(str(BASE/'circuito/divisor.s8p'));sd0=dn.s[0];sa=rf.Network(str(BASE/'circuito/antena.s6p')).s[0];tl=rf.Network(str(BASE/'circuito/coaxial.s2p')).s[0]
fields={};theta={}
for axis in ['H','V','V_fino']:
    theta[axis]=read_pattern(BASE/'antena'/('ALL_'+axis+'.csv'))[0]
    fields[axis]=np.stack([read_pattern(BASE/'antena'/(n+'_'+axis+'.csv'))[1] for n in ['R1_A','R1_B','R2_A','R2_B','R3_A','R3_B']],axis=-1)
# Interpolacao dos parametros de linha reduz custo da busca; nao substitui HFSS.
ws=np.linspace(.3,4.8,901)
ms=[MLine(frequency=dn.frequency,w=w/1000,h=.00152,t=.000035,ep_r=2.94,tand=.0016,rho=1/5.8e7,rough=.5e-6,diel='frequencyinvariant',z0_port=50) for w in ws]
gs=np.array([m.gamma[0] for m in ms]);zs=np.array([m.z0[0] for m in ms])
def interp(w,data):return np.interp(w,ws,data.real)+1j*np.interp(w,ws,data.imag)
def line(w,l):
    g=interp(w,gs)*l/1000;z=interp(w,zs);c,s=np.cosh(g),np.sinh(g)
    return np.array([[c,z*s],[s/z,c]])
def ideal(x):
    w1,w2,l1=x;t=line(w1,l1)@line(w2,total-l1);yy=np.array([[t[1,1],-1],[-1,t[0,0]]])/t[0,1]
    y=np.zeros((4,4),complex)
    for i in range(1,4):y[np.ix_([0,i],[0,i])]+=yy
    s=np.linalg.solve((np.eye(4)+50*y).T,(np.eye(4)-50*y).T).T
    s8=np.zeros((8,8),complex)
    for ids in [[0,2,4,6],[1,3,5,7]]:s8[np.ix_(ids,ids)]=s
    return s8
x0=np.array([p['W1_mm'],p['W2_mm'],p['L1_mm']]);si0=ideal(x0)
def load(sd):
    r1,t12,t21,r2=tl[0,0],tl[0,1],tl[1,0],tl[1,1];eye=np.eye(6);F=np.linalg.inv(eye-sd[2:,2:]*r1)
    sb=np.zeros((8,8),complex);sb[:2,:2]=sd[:2,:2]+sd[:2,2:]@F@sd[2:,:2]*r1
    sb[:2,2:]=sd[:2,2:]@(r1*F@sd[2:,2:]*t12+t12*eye)
    sb[2:,:2]=t21*F@sd[2:,:2];sb[2:,2:]=t21*F@sd[2:,2:]*t12+r2*eye
    tr=np.linalg.solve(eye-sb[2:,2:]@sa,sb[2:,:2]);s=sb[:2,:2]+sb[:2,2:]@sa@tr
    return s,tr@np.ones(2)/np.sqrt(2)
def net(x):return sd0+ideal(x)-si0
def evaluate(x,detail=False):
    sd=net(x);s,a=load(sd);ga=abs(s@np.ones(2));gm=abs(np.diag(s));sigma=float(np.linalg.svd(sd,compute_uv=False)[0])
    # Mantem todas as portas nos mesmos lugares: comprimento total e cabos fixos.
    loss=1-float(np.sum(abs(s@np.ones(2)/np.sqrt(2))**2))-float(np.sum(abs(a)**2-abs(sa@a)**2))
    cost=300*np.sum(np.maximum(np.r_[ga,gm]-.085,0)**2)+.01*np.sum(ga**2+gm**2)
    cost+=10000*max(sigma-.9995,0)**2+10000*max(-loss,0)**2
    cost+=.00002*np.sum(((x-x0)/[.5,1,2])**2)
    if not detail:return float(cost)
    curves={axis:10*np.log10(np.maximum(np.sum(abs(e@a)**2,axis=1),1e-30)) for axis,e in fields.items()}
    cuts={axis:metrics(theta[axis],curves[axis]) for axis in 'HV'}
    vf=curves['V_fino'];tv=theta['V_fino'];ip=int(np.argmax(vf));q=np.polyfit(tv[ip-1:ip+2],vf[ip-1:ip+2],2)
    vs=lambda z:((1+z)/(1-z)).tolist()
    return dict(W1_mm=float(x[0]),W2_mm=float(x[1]),L1_mm=float(x[2]),L2_mm=float(total-x[2]),VSWR_ativo_estimado=vs(ga),VSWR_casado_estimado=vs(gm),
      sigma_max_aproximado=sigma,perda_total_estimada_W=loss,ganho_frontal_estimado_dBi=cuts['H']['ganho_frontal_dBi'],pico_V_estimado_graus=float(-q[1]/(2*q[0])),custo=float(cost))
def main():
    np.testing.assert_allclose(load(sd0)[0],rf.Network(str(BASE/'circuito/nexxim.s2p')).s[0],atol=1e-12,rtol=0)
    opt=differential_evolution(evaluate,[(.4,1.35),(1.3,4.2),(7.2,12.3)],seed=51715,maxiter=130,popsize=10,tol=1e-8,polish=True)
    r=dict(metodo='Diferenca local entre linhas distribuidas somada ao S8 HFSS inicial. Somente guia; confirmar cada candidato no HFSS e Nexxim.',
      antena_S6_reutilizada_sha256=hashlib.sha256((BASE/'antena/centro.s6p').read_bytes()).hexdigest(),referencia=str(BASE),base=evaluate(x0,True),candidato=evaluate(opt.x,True))
    (ROOT/'guia.json').write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(r,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
