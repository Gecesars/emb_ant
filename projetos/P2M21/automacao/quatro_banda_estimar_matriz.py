"""Selecao de casamento por matriz Z2 efetiva congelada; nao valida HFSS."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import skrf as rf
from skrf.media.mline import MLine
from shapely.geometry import LineString
from scipy.optimize import differential_evolution
from quatro_banda_estimar import ROOT,VSWR_TARGET

def estimate(folder,output,extended=False,root_only=False,active_only=False,fast=False):
    folder=Path(folder);src=folder/('banda_fast.s2p' if fast else 'triagem3.s2p');net=rf.Network(str(src))
    expected=np.arange(5090,5251,1 if fast else 80)*1e6
    np.testing.assert_allclose(net.f,expected,rtol=0,atol=.01)
    g=json.loads((folder/'geometria.json').read_text());p=g['parametros']
    assert not any(p.get('root_seg%d_l_%s'%(i,pol),0.) for i in (2,3,4) for pol in 'AB'),'Usar estimador de multiplas secoes para esta topologia'
    w50=g['lines']['50']['w_mm'];w0=g['lines']['70.71067811865476']['w_mm'];l0=g['lines']['70.71067811865476']['l90_mm']
    dims=[w0*p.get('root_w_A',1.),w0*p.get('local_w_A',1.),l0*p.get('root_l_A',1.),l0*p.get('local_l_A',1.),w50*p.get('root_post_w_A',1.),w50*p.get('local_post_w_A',1.)]
    for key in ['root_w','local_w','root_l','local_l','root_post_w','local_post_w']:
        assert p.get(key+'_A',1.)==p.get(key+'_B',1.),key
    rt=next(t for t in g['traces'] if t['tipo']=='raiz' and t['polarizacao']=='A')
    lt=next(t for t in g['traces'] if t['tipo']=='local' and t['polarizacao']=='A')
    totals=[LineString(t['linha70']+t['linha50'][1:]).length for t in [rt,lt]]
    identity=np.broadcast_to(np.eye(2),(len(net.f),2,2)).copy()
    def section(w,l):
        med=MLine(frequency=net.frequency,w=w/1000,h=.00076,t=.000035,ep_r=3.66,tand=.0037,diel='frequencyinvariant',rho=1/5.8e7,rough=.5e-6)
        t=med.gamma*l/1000;z=med.z0;m=np.empty((len(net.f),2,2),complex)
        m[:,0,0]=m[:,1,1]=np.cosh(t);m[:,0,1]=z*np.sinh(t);m[:,1,0]=np.sinh(t)/z
        return m
    def line(w,l,wp,total):return section(w,l)@section(wp,total-l)
    def apply(m,z):
        # A,B,C,D escalares comuns as polarizacoes. A matriz Z retida inclui Z12/Z21.
        a,b,c,d=[m[:,i,j,None,None] for i,j in [(0,0),(0,1),(1,0),(1,1)]]
        return (a*z+b*identity)@np.linalg.inv(c*z+d*identity)
    phase=np.exp(2j*2*np.pi*net.f/299792458*np.sqrt(2.036363533774732)*.05)[:,None,None]
    s_pcb=net.s*phase
    z_input=50*(identity+s_pcb)@np.linalg.inv(identity-s_pcb)
    z_local=apply(np.linalg.inv(line(dims[0],dims[2],dims[4],totals[0])),2*z_input)
    z_effective=apply(np.linalg.inv(line(dims[1],dims[3],dims[5],totals[1])),2*z_local)
    def scattering(x):
        x=list(x)+dims[4:] if len(x)==4 else x
        z=apply(line(x[1],x[3],x[5],totals[1]),z_effective)/2
        z=apply(line(x[0],x[2],x[4],totals[0]),z)/2
        return ((z-50*identity)@np.linalg.inv(z+50*identity))/phase
    def values(x):
        s=scattering(x);gam=np.column_stack((s@np.ones(2),np.diagonal(s,axis1=1,axis2=2)))
        if np.max(abs(gam))>=1:return np.full((len(net.f),4),1e6)
        return (1+abs(gam))/(1-abs(gam))
    err=float(np.max(abs(scattering(dims)-net.s)));assert err<1e-12,err
    def summary(x):
        x=list(x)+dims[4:] if len(x)==4 else x;v=values(x)
        return dict(largura_raiz_mm=float(x[0]),largura_local_mm=float(x[1]),comprimento_raiz_mm=float(x[2]),comprimento_local_mm=float(x[3]),largura_pos_raiz_mm=float(x[4]),largura_pos_local_mm=float(x[5]),
            fatores={key+'_'+pol:float(val) for pol in 'AB' for key,val in zip(['root_w','local_w','root_l','local_l','root_post_w','local_post_w'],[x[0]/w0,x[1]/w0,x[2]/l0,x[3]/l0,x[4]/w50,x[5]/w50])},
            pior_VSWR_ativo=float(v[:,:2].max()),pior_VSWR_casado=float(v[:,2:].max()),pior_VSWR_geral=float(v.max()),VSWR_pontos=v.tolist())
    limits=[(.4,2.),(.65,1.3),(3.,12.),(8.,18.)]+([(1.1,2.3),(1.1,2.3)] if extended else [])
    def objective(x):
        v=values(x)
        return v[:,:2].max() if active_only else v.max()
    fit=None if root_only else differential_evolution(objective,limits,seed=67,tol=1e-8,popsize=14,workers=1)
    root_limits=[(.4,2.5),(3.,12.),(1.1,3.)]
    def root_dimensions(x):return [x[0],dims[1],x[1],dims[3],x[2],dims[5]]
    root_fit=differential_evolution(lambda x:objective(root_dimensions(x)),root_limits,seed=71,tol=1e-8,popsize=12,workers=1)
    result=dict(estado='ESTIMATIVA_MATRICIAL_NAO_VALIDADA',fonte=str(folder),arquivo_s2p=src.name,s2p_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
        metodo='Matriz Z2 efetiva congelada, com Z12/Z21; cascata equivalente dos dois estagios identicos A/B. Atualiza a interacao entre entradas terminadas nas redes novas. Nao representa variacao da radiacao, curvas ou distribuicao interna dos quatro radiadores. A recomposicao por construcao nao valida a predicao.',
        faixa_GHz=[5.09,5.25],pontos=len(net.f),tipo_dados='HFSS Fast' if fast else 'HFSS Discrete3',alvo_VSWR=VSWR_TARGET,criterio_objetivo='VSWR ativo A/B em fase' if active_only else 'VSWR ativo e outra entrada casada',erro_recomposicao_S=err,limites_mm=limits,modo='somente_raiz' if root_only else 'todos',referencia=summary(dims),matriz_otimizada=summary(root_dimensions(root_fit.x) if root_only else fit.x),limites_somente_raiz_mm=root_limits,somente_raiz=summary(root_dimensions(root_fit.x)))
    Path(output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('fonte');a.add_argument('saida');a.add_argument('--segmentos-completos',action='store_true');a.add_argument('--somente-raiz',action='store_true');a.add_argument('--ativos',action='store_true');a.add_argument('--fast',action='store_true');x=a.parse_args();estimate(x.fonte,x.saida,x.segmentos_completos,x.somente_raiz,x.ativos,x.fast)
