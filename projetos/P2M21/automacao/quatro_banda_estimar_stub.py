"""Seletor analitico: transformador na raiz e stub aberto simetrico.

Usa somente S2 reais para congelar a carga interna. A previsao nao e HFSS.
"""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
import skrf as rf
from skrf.media.mline import MLine
from scipy.optimize import differential_evolution
from shapely.geometry import LineString

def estimate(folder,out):
    folder=Path(folder);file=folder/'triagem3.s2p';n=rf.Network(str(file));np.testing.assert_allclose(n.f,[5.09e9,5.17e9,5.25e9],rtol=0,atol=.01)
    g=json.loads((folder/'geometria.json').read_text());p=g['parametros'];nom=g['lines']['70.71067811865476'];w50=g['lines']['50']['w_mm']
    assert not p.get('root_stub_l_A',0.) and not any(p.get('root_seg%d_l_A'%i,0.) for i in (2,3,4))
    assert p.get('root_post_w_A',1.)==1.
    t=next(x for x in g['traces'] if x['tipo']=='raiz' and x['polarizacao']=='A');total=LineString(t['linha70']+t['linha50'][1:]).length
    eye=np.broadcast_to(np.eye(2),(3,2,2)).astype(complex)
    def medium(w):return MLine(frequency=n.frequency,w=w/1000,h=.00076,t=.000035,ep_r=3.66,tand=.0037,diel='frequencyinvariant',rho=1/5.8e7,rough=.5e-6)
    def line(w,l):
        med=medium(w);u=med.gamma*l/1000;z=med.z0;m=np.empty((3,2,2),complex);m[:,0,0]=m[:,1,1]=np.cosh(u);m[:,0,1]=z*np.sinh(u);m[:,1,0]=np.sinh(u)/z;return m
    def apply(m,z):
        a,b,c,d=[m[:,i,j,None,None] for i,j in [(0,0),(0,1),(1,0),(1,1)]]
        return (a*z+b*eye)@np.linalg.inv(c*z+d*eye)
    w=nom['w_mm']*p['root_w_A'];l=nom['l90_mm']*p['root_l_A']
    if not p.get('root_flat_sections',False):l+=w/2 if w>w50 else -w50/2
    phase=np.exp(2j*2*np.pi*n.f/299792458*np.sqrt(2.036363533774732)*.05)[:,None,None]
    s=n.s*phase;z=50*(eye+s)@np.linalg.inv(eye-s)
    load=apply(np.linalg.inv(line(w,l)@line(w50,total-l)),2*z)
    def scattering(x):
        wr,lr,ws,ls=x
        zin=apply(line(wr,lr)@line(w50,total-lr),load)/2
        med=medium(ws)
        # Correcao aproximada da extremidade aberta; verificacao final em HFSS.
        ee=(3.66+1)/2+(3.66-1)/2/np.sqrt(1+12*.76/ws)
        dl=.412*.76*(ee+.3)*(ws/.76+.264)/((ee-.258)*(ws/.76+.8))
        ystub=np.tanh(med.gamma*(ls+dl)/1000)/med.z0 if ls>0 else np.zeros(3)
        zin=np.linalg.inv(np.linalg.inv(zin)+ystub[:,None,None]*eye)
        return ((zin-50*eye)@np.linalg.inv(zin+50*eye))/phase
    original=[w,l,1.,0.];err=float(abs(scattering(original)-n.s).max());assert err<1e-12
    def values(x):
        s=scattering(x);gamma=np.column_stack((s@np.ones(2),np.diagonal(s,axis1=1,axis2=2)))
        if np.max(abs(gamma))>=1:return np.full((3,4),1e6)
        return (1+abs(gamma))/(1-abs(gamma))
    bounds=[(.4,1.6),(3.,12.),(.4,2.5),(.2,12.)]
    opt=differential_evolution(lambda x:values(x)[:,:2].max(),bounds,seed=83,tol=1e-8,popsize=16,workers=1)
    wr,lr,ws,ls=opt.x;v=values(opt.x);sv=np.linalg.svd(scattering(opt.x),compute_uv=False).max()
    assert sv<=1.000001,sv
    factors=dict(root_flat_sections=True)
    for pol in 'AB':factors.update({k+'_'+pol:float(v) for k,v in [('root_w',wr/nom['w_mm']),('root_l',lr/nom['l90_mm']),('root_stub_w',ws),('root_stub_l',ls)]})
    summary=dict(largura_raiz_mm=wr,comprimento_raiz_mm=lr,stub_largura_mm=ws,stub_comprimento_fisico_mm=ls,pior_VSWR_ativo=float(v[:,:2].max()),pior_VSWR_casado=float(v[:,2:].max()),VSWR_pontos=v.tolist(),fatores=factors,maior_singular_modelo=float(sv))
    r=dict(estado='ESTIMATIVA_STUB_NAO_VALIDADA',fonte=str(folder),arquivo_s2p=file.name,s2p_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),erro_recomposicao_S=err,alvo_VSWR=1.25,metodo='Z2 interna congelada, acoplamento retido, linha raiz e susceptancia shunt de stub aberto identico em A/B. Correcao analitica da ponta; exige HFSS real com novo retorno.',stub=summary)
    Path(out).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('fonte');a.add_argument('saida');x=a.parse_args();estimate(x.fonte,x.saida)
