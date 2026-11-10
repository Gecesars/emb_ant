"""Duas a quatro secoes proximas a entrada, mantendo divisores locais/radiadores.

Matriz Z2 efetiva congelada apos o primeiro estagio; apenas seleciona CAD
para ensaio. Nenhum valor previsto constitui resultado HFSS da variante.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import skrf as rf
from skrf.media.mline import MLine
from shapely.geometry import LineString
from scipy.optimize import differential_evolution
from quatro_banda_estimar import VSWR_TARGET

def estimate(folder,output,fast=False,max_width=3.,sections=2,local=False,phase_reference=None):
    folder=Path(folder);src=folder/('banda_fast.s2p' if fast else 'triagem3.s2p');n=rf.Network(str(src))
    np.testing.assert_allclose(n.f,np.arange(5090,5251,1 if fast else 80)*1e6,rtol=0,atol=.01)
    g=json.loads((folder/'geometria.json').read_text());p=g['parametros']
    w0=g['lines']['70.71067811865476']['w_mm'];l0=g['lines']['70.71067811865476']['l90_mm'];w50=g['lines']['50']['w_mm']
    assert sections in (2,3,4)
    for key in ['root_w','root_l','root_post_w']+['root_seg%d_%s'%(i,k) for i in (2,3,4) for k in ('w','l')]:
        default=0. if key.startswith('root_seg') and key.endswith('_l') else 1.
        assert p.get(key+'_A',default)==p.get(key+'_B',default),key
    trace=next(t for t in g['traces'] if t['tipo']=='raiz' and t['polarizacao']=='A')
    total=LineString(trace['linha70']+trace['linha50'][1:]).length
    identity=np.broadcast_to(np.eye(2),(len(n.f),2,2)).copy()
    def section(w,l):
        med=MLine(frequency=n.frequency,w=w/1000,h=.00076,t=.000035,ep_r=3.66,tand=.0037,diel='frequencyinvariant',rho=1/5.8e7,rough=.5e-6)
        t=med.gamma*l/1000;z=med.z0;m=np.empty((len(n.f),2,2),complex)
        m[:,0,0]=m[:,1,1]=np.cosh(t);m[:,0,1]=z*np.sinh(t);m[:,1,0]=np.sinh(t)/z
        return m
    def matrix(x,tail=w50,caps=False):
        m=identity.astype(complex)
        pairs=[(float(w),float(l)) for w,l in zip(x[::2],x[1::2]) if l>1e-9]
        ends=np.cumsum([v[1] for v in pairs]);previous=0.
        for i,(w,l) in enumerate(pairs):
            next_w=pairs[i+1][0] if i+1<len(pairs) else tail
            boundary=ends[i]
            if caps and abs(w-next_w)>1e-9:boundary+=(w/2 if w>next_w else -next_w/2)
            assert boundary>previous,(x,boundary,previous)
            m=m@section(w,boundary-previous);previous=boundary
        return m@section(tail,total-previous)
    def apply(m,z):
        a,b,c,d=[m[:,i,j,None,None] for i,j in [(0,0),(0,1),(1,0),(1,1)]]
        return (a*z+b*identity)@np.linalg.inv(c*z+d*identity)
    original=[w0*p.get('root_w_A',1.),l0*p.get('root_l_A',1.),w50*p.get('root_seg2_w_A',1.),l0*p.get('root_seg2_l_A',0.)]
    for i in range(3,sections+1):original.extend([w50*p.get('root_seg%d_w_A'%i,1.),l0*p.get('root_seg%d_l_A'%i,0.)])
    assert all(p.get('root_seg%d_l_A'%i,0.)==0. for i in range(sections+1,5)),'Fonte tem mais secoes'
    phase=np.exp(2j*2*np.pi*n.f/299792458*np.sqrt(2.036363533774732)*.05)[:,None,None]
    spcb=n.s*phase;z=50*(identity+spcb)@np.linalg.inv(identity-spcb)
    source_caps=not p.get('root_flat_sections',False)
    load=apply(np.linalg.inv(matrix(original,w50*p.get('root_post_w_A',1.),caps=source_caps)),2*z)
    def scattering(x,caps=False):
        z=apply(matrix(x,caps=caps),load)/2
        return ((z-50*identity)@np.linalg.inv(z+50*identity))/phase
    def output_voltage(x,caps=False):
        m=matrix(x,caps=caps);spcb=scattering(x,caps=caps)*phase
        vin=(identity+spcb)@np.ones(2,dtype=complex)
        equation=m[:,0,0,None,None]*identity+m[:,0,1,None,None]*np.linalg.inv(load)
        return np.linalg.solve(equation,vin[...,None])[...,0]
    reference_voltage=None;reference_info=None;center=int(np.argmin(abs(n.f-5.17e9)))
    if phase_reference:
        path=Path(phase_reference)/'geometria.json';rg=json.loads(path.read_text());rp=rg['parametros']
        for key in ['local_w_A','local_l_A','local_post_w_A']:
            assert abs(rp.get(key,1.)-p.get(key,1.))<1e-10,'Referencias locais diferentes'
        rx=[w0*rp.get('root_w_A',1.),l0*rp.get('root_l_A',1.)]
        for i in range(2,5):rx.extend([w50*rp.get('root_seg%d_w_A'%i,1.),l0*rp.get('root_seg%d_l_A'%i,0.)])
        reference_voltage=output_voltage(rx,caps=not rp.get('root_flat_sections',False))
        reference_info=dict(arquivo=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),frequencia_GHz=5.17,limite_graus=5.,nota='Fase estimada na saida do primeiro estagio, com carga Z2 congelada. Nao substitui campos HFSS.')
    def phase_delta(x,caps=False):
        if reference_voltage is None:return None
        return np.angle(output_voltage(x,caps=caps)[center]/reference_voltage[center],deg=True)
    assert p.get('root_post_w_A',1.)==1.,'Esta selecao preserva a cauda nominal de50ohms; escolher fonte compativel'
    err=float(np.max(abs(scattering(original,caps=source_caps)-n.s)));assert err<1e-12,err
    def values(x,caps=False):
        s=scattering(x,caps=caps);gam=np.column_stack((s@np.ones(2),np.diagonal(s,axis1=1,axis2=2)))
        if np.max(abs(gam))>=1:return np.full((len(n.f),4),1e6)
        return (1+abs(gam))/(1-abs(gam))
    assert .4<max_width<=5.,'Manter cobre dentro da placa e do retorno na raiz'
    limits=[(.4,max_width),(2.,20.)]*sections
    if local:
        assert p.get('root_flat_sections',False),'Busca local exige fonte com transicoes planas'
        assert all(x>0 for x in original),'Busca local exige todas as secoes presentes'
        limits=[(max(.4,.75*v),min(max_width,1.25*v)) if i%2==0 else (max(2.,v-2.),min(20.,v+2.)) for i,v in enumerate(original)]
    def cost(x):
        if sum(x[1::2])>44.:return 1e3+sum(x[1::2])
        penalty=0. if reference_voltage is None else .05*max(0.,float(np.max(abs(phase_delta(x))))-5.)
        return values(x)[:,:2].max()+penalty
    fit=differential_evolution(cost,limits,seed=79,tol=1e-8,popsize=16,workers=1)
    def summary(x,caps=False):
        v=values(x,caps=caps)
        extra=[item for i in range(3,sections+1) for item in [('root_seg%d_w'%i,x[2*(i-1)]/w50),('root_seg%d_l'%i,x[2*(i-1)+1]/l0)]]
        return dict(largura_raiz_mm=float(x[0]),comprimento_raiz_mm=float(x[1]),largura_segunda_secao_mm=float(x[2]),comprimento_segunda_secao_mm=float(x[3]),
            fase_saida_relativa_centro_graus=None if reference_voltage is None else phase_delta(x,caps=caps).tolist(),
            secoes_raiz_mm=[dict(largura=float(w),comprimento=float(l)) for w,l in zip(x[::2],x[1::2])],
            largura_local_mm=w0*p.get('local_w_A',1.),comprimento_local_mm=l0*p.get('local_l_A',1.),largura_pos_raiz_mm=w50,largura_pos_local_mm=w50*p.get('local_post_w_A',1.),
            fatores=dict(root_flat_sections=not caps,**{key+'_'+pol:float(value) for pol in 'AB' for key,value in [('root_w',x[0]/w0),('root_l',x[1]/l0),('root_seg2_w',x[2]/w50),('root_seg2_l',x[3]/l0),('root_post_w',1.)]+extra}),
            pior_VSWR_ativo=float(v[:,:2].max()),pior_VSWR_casado=float(v[:,2:].max()),pior_VSWR_geral=float(v.max()),VSWR_pontos=v.tolist())
    result=dict(estado='ESTIMATIVA_RAIZ_DUPLA_NAO_VALIDADA',fonte=str(folder),arquivo_s2p=src.name,s2p_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
        metodo='Matriz Z2 efetiva congelada apos primeiro estagio. Secoes proximas a entrada sao alteradas; cauda de50ohms e divisores locais preservados. Acoplamento das entradas retido na matriz; mudancas de radiacao/campos das trilhas exigem HFSS.',
        transicoes='Fonte historica: fronteiras efetivas dos caps quadrados consideradas. Variante: caps planos, passos de largura nas cotas nominais. Descontinuidades EM e radiacao exigem HFSS.',
        faixa_GHz=[5.09,5.25],pontos=len(n.f),secoes=sections,busca_local=local,referencia_fase=reference_info,alvo_VSWR=VSWR_TARGET,criterio_objetivo='VSWR ativo A/B em fase; penalidade de fase de saida somente quando configurada',erro_recomposicao_S=err,limites_mm=limits,referencia=summary(original,caps=source_caps),raiz_dupla=summary(fit.x))
    Path(output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result['raiz_dupla'].items() if k!='VSWR_pontos'},ensure_ascii=False))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('fonte');a.add_argument('saida');a.add_argument('--fast',action='store_true');a.add_argument('--largura-max',type=float,default=3.);a.add_argument('--secoes',type=int,choices=[2,3,4],default=2);a.add_argument('--local',action='store_true');a.add_argument('--fase-referencia');x=a.parse_args();estimate(x.fonte,x.saida,x.fast,x.largura_max,x.secoes,x.local,x.fase_referencia)
