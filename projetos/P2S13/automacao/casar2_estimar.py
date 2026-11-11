"""Triagem MLine de duas dimensoes; carga acoplada Z4 congelada, exige novo HFSS."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
import skrf as rf
from skrf.media import MLine
from scipy.optimize import differential_evolution

def estimate(source,out):
    source=Path(source);cfg=json.loads((source/'configuracao.json').read_text())
    cell=next(c for c in cfg['celulas'] if c['radiadores']==2)
    g=json.loads((Path(cell['fonte'])/'geometria.json').read_text())
    trace=g['traces'][0];w0=trace['largura_transformador_mm'];l0=abs(trace['linha70'][1][0]-trace['linha70'][0][0]);total=trace['comprimento_mm'];w50=trace['largura_linha50_mm']
    net=rf.Network(str(source/'centro.s4p'));assert net.nports==4 and len(net.f)==1 and net.f[0]==5.17e9
    names=[n.removesuffix(':1') for n in net.port_names];indices=[i for i,n in enumerate(names) if n.startswith(cell['nome']+'_')];assert len(indices)==2
    ident=np.eye(4);z0=net.z[0]
    def section(w,length):
        m=MLine(frequency=net.frequency,w=w/1000,h=.00076,t=.000035,ep_r=3.66,tand=.0037,diel='frequencyinvariant',rho=1/5.8e7,rough=.5e-6)
        q=m.gamma[0]*length/1000;z=m.z0[0]
        return np.array([[np.cosh(q),z*np.sinh(q)],[np.sinh(q)/z,np.cosh(q)]])
    beta=2*np.pi*5.17e9/299792458*np.sqrt(2.036363533774732);q=1j*beta*.05
    coax=np.array([[np.cosh(q),50*np.sinh(q)],[np.sinh(q)/50,np.cosh(q)]])
    def network(w,length):
        branch=section(w,length)@section(w50,total-length)
        parallel=branch.copy();parallel[0,1]/=2;parallel[1,0]*=2
        return coax@parallel
    def apply(m,z):
        abcd=[ident.astype(complex).copy(),np.zeros((4,4),complex),np.zeros((4,4),complex),ident.astype(complex).copy()]
        for mat,(row,col) in zip(abcd,[(0,0),(0,1),(1,0),(1,1)]):
            for i in indices:mat[i,i]=m[row,col]
        a,b,c,d=abcd
        return (a@z+b)@np.linalg.inv(c@z+d)
    frozen=apply(np.linalg.inv(network(w0,l0)),z0)
    def scattering(x):
        z=apply(network(*x),frozen)
        return (z-50*ident)@np.linalg.inv(z+50*ident)
    assert abs(scattering([w0,l0])-net.s[0]).max()<1e-12
    def values(x):
        s=scattering(x);gam=np.r_[s@np.ones(4),np.diag(s)];a=abs(gam)
        return (1+a)/(1-a) if a.max()<1 else np.full(8,1e6)
    def objective(x):
        v=values(x);return max(v[i] for i in indices+list(np.array(indices)+4))
    limits=[(.4,2.2),(3.,22.)]
    opt=differential_evolution(objective,limits,seed=57,popsize=10,maxiter=120,tol=1e-7,workers=1)
    def summary(x):
        v=values(x);return dict(largura_mm=float(x[0]),comprimento_mm=float(x[1]),VSWR_ativo=v[:4].tolist(),VSWR_casado=v[4:].tolist(),pior_placa2=float(objective(x)))
    result=dict(estado='ESTIMATIVA_NAO_VALIDADA',fonte=str(source),sha256_s4p=hashlib.sha256((source/'centro.s4p').read_bytes()).hexdigest(),portas=names,
      metodo='Retira cascata coaxial50mm e equivalente par de ramos da PCB2. Mantem matriz Z4 efetiva e acoplamento congelados; recoloca transformadores iguais A/B. Coax ideal de fase APENAS na triagem; HFSS preserva perdas fisicas. Nao preve variacao de campos ou de acoplamento geometricos.',
      limites_mm=limits,referencia=summary([w0,l0]),candidato=summary(opt.x),erro_recomposicao_S=float(abs(scattering([w0,l0])-net.s[0]).max()))
    Path(out).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('fonte');p.add_argument('saida');a=p.parse_args();estimate(a.fonte,a.saida)
