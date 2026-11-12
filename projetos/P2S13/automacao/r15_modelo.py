"""Guia passivo: ajustar descontinuidades comuns ao S8 real e sintonizar secoes."""
from pathlib import Path
import json,itertools,os
import numpy as np
import skrf as rf
import shutil
from scipy.optimize import least_squares,differential_evolution
from r15_guia import BASE,ROOT,sd0,sa,tl,x0,total,line,load,fields,theta
ANCHOR=Path(os.environ.get('P2S13_R15_ANCHOR',str(BASE)))
if ANCHOR!=BASE:
    sd0=rf.Network(str(ANCHOR/'circuito/divisor.s8p')).s[0]
    cp=json.loads((ANCHOR/'divisor/configuracao.json').read_text())['parametros']
    x0=np.array([cp['W1_mm'],cp['W2_mm'],cp['L1_mm']])
ROOT=Path(os.environ.get('P2S13_MODEL_DEST',str(ROOT)));ROOT.mkdir(exist_ok=True)
omega=2*np.pi*5.17e9
SREF=(sd0[np.ix_([0,2,4,6],[0,2,4,6])]+sd0[np.ix_([1,3,5,7],[1,3,5,7])])/2
SREF=sum(SREF[np.ix_([0]+list(p),[0]+list(p))] for p in itertools.permutations([1,2,3]))/6
def one(x,p):
    li,lo,cj,co,ri,ro=p;zi=ri+1e-8+1j*omega*li*1e-9;zo=ro+1j*omega*lo*1e-9
    y=np.zeros((5,5),complex);y[np.ix_([0,1],[0,1])]+=np.array([[1,-1],[-1,1]])/zi;y[1,1]+=1j*omega*cj*1e-12
    t=line(x[0],x[2])@line(x[1],total-x[2])@np.array([[1,0],[1j*omega*co*1e-12,1]])@np.array([[1,zo],[0,1]])
    yy=np.array([[t[1,1],-1],[-1,t[0,0]]])/t[0,1]
    for i in [2,3,4]:y[np.ix_([1,i],[1,i])]+=yy
    ix=[0,2,3,4];yr=y[np.ix_(ix,ix)]-np.outer(y[ix,1],y[1,ix])/y[1,1]
    return np.linalg.solve((np.eye(4)+50*yr).T,(np.eye(4)-50*yr).T).T
def dual(s):
    d=np.zeros((8,8),complex)
    for ix in [[0,2,4,6],[1,3,5,7]]:d[np.ix_(ix,ix)]=s
    return d
def resid(p):
    delta=one(x0,p)-SREF
    return np.r_[delta.real.ravel(),delta.imag.ravel()]
best=None
for guess in [[.7,.7,.05,.05,.2,.2],[1,1,.1,.1,.05,.2],[.1,.1,.05,.1,.1,.1],[1.5,.5,.02,.2,.1,.1]]:
    fit=least_squares(resid,guess,bounds=([0,0,0,0,0,0],[4,4,.8,.8,3,3]),xtol=1e-12,ftol=1e-12,gtol=1e-12,max_nfev=600)
    if best is None or fit.cost<best.cost:best=fit
p=best.x;error=float(np.max(abs(one(x0,p)-SREF)))
residual=sd0-dual(one(x0,p)) if ANCHOR!=BASE else np.zeros((8,8),complex)
def candidate_net(x):return dual(one(x,p))+residual
def evaluate(x,detail=False):
    sd=candidate_net(x);s,a=load(sd);ga=abs(s@np.ones(2));gm=abs(np.diag(s));sigma=float(np.linalg.svd(sd,compute_uv=False)[0])
    cost=300*np.sum(np.maximum(np.r_[ga,gm]-.07,0)**2)+np.sum(ga**2+gm**2)
    cost+=100000*max(sigma-.9995,0)**2
    cost+=.00001*np.sum(((x-x0)/[.5,1,2])**2)
    if not detail:return float(cost)
    g=10*np.log10(np.sum(abs(fields['H']@a)**2,axis=1));gv=10*np.log10(np.sum(abs(fields['V_fino']@a)**2,axis=1));tv=theta['V_fino'];i=int(np.argmax(gv));q=np.polyfit(tv[i-1:i+2],gv[i-1:i+2],2)
    vs=lambda v:((1+v)/(1-v)).tolist()
    return dict(W1_mm=float(x[0]),W2_mm=float(x[1]),L1_mm=float(x[2]),L2_mm=float(total-x[2]),VSWR_ativo_estimado=vs(ga),VSWR_casado_estimado=vs(gm),
      sigma_max=sigma,ganho_frontal_estimado_dBi=float(g[np.argmin(abs(theta['H']))]),pico_V_estimado_graus=float(-q[1]/(2*q[0])),custo=float(cost))
bounds=[(.35,1.5),(1.2,4.5),(6.8,12.5)] if ANCHOR==BASE else [(x0[0]*.85,x0[0]*1.15),(x0[1]*.85,x0[1]*1.15),(x0[2]-.4,x0[2]+.4)]
opt=differential_evolution(evaluate,bounds,seed=517151,maxiter=120,popsize=10,tol=1e-8,polish=True)
r=dict(metodo='Modelo passivo de linhas e parasitas LC/R comuns ajustado ao S4 medio do HFSS. Guia de dimensoes; nao valida ganho/VSWR.',
    parasitas_efetivos=dict(zip(['Lin_nH','Lout_nH','Cj_pF','Cout_pF','Rin_ohm','Rout_ohm'],map(float,p))),erro_max_fit_S4=error,
    referencia_HFSS=str(ANCHOR),residuo_S8_local_preservado=ANCHOR!=BASE,base=evaluate(x0,True),candidato=evaluate(opt.x,True))
assert error<.03,(error,p)
assert r['candidato']['sigma_max']<=1
(ROOT/'guia_passiva.json').write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
out=ROOT/'guia_nexxim';out.mkdir(exist_ok=True)
for name,s,labels in [('divisor',candidate_net(opt.x),['IN_A','IN_B','R1_A','R1_B','R2_A','R2_B','R3_A','R3_B']),('conjunto',load(candidate_net(opt.x))[0],['IN_A','IN_B'])]:
    n=rf.Network(f=[5.17e9],s=s[None],z0=50);n.port_names=labels;n.write_touchstone(str(out/name),form='ri')
for file in ['antena.s6p','coaxial.s2p']:shutil.copy2(BASE/'circuito'/file,out/file)
print(json.dumps(r,indent=2,ensure_ascii=False))
