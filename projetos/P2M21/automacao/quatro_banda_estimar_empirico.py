"""Selecao local por secantes de respostas HFSS, sem declarar validacao."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
import skrf as rf
from scipy.optimize import differential_evolution
from divisor_variantes_comparar import read_pattern,beam
from quatro_ajustar_analisar import sidelobe

def run(folders,out,extent=1.,max_width=5.):
    assert .4<max_width<=5.5
    folders=[Path(x) for x in folders];data=[];parameters=[];audit=[]
    keys=['root_w','root_l','root_seg2_w','root_seg2_l','root_seg3_w','root_seg3_l']
    for folder in folders:
        src=folder/'triagem3.s2p';n=rf.Network(str(src));np.testing.assert_allclose(n.f,[5.09e9,5.17e9,5.25e9]);np.testing.assert_allclose(n.z0,50)
        r=json.loads((folder/'resultado.json').read_text());assert r['convergiu'] and r['fisica_ok']
        g=json.loads((folder/'geometria.json').read_text());p=g['parametros'];assert p['root_flat_sections']
        assert not any(p.get('root_seg4_l_'+pol,0.) for pol in 'AB'),'Este seletor representa tres secoes'
        assert all(p[k+'_A']==p[k+'_B'] for k in keys)
        w0=g['lines']['70.71067811865476']['w_mm'];l0=g['lines']['70.71067811865476']['l90_mm'];w50=g['lines']['50']['w_mm']
        parameters.append(np.array([p[k+'_A']*scale for k,scale in zip(keys,[w0,l0,w50,l0,w50,l0])]))
        if data:
            for key in ['local_w_A','local_w_B','local_l_A','local_l_B','local_post_w_A','local_post_w_B','root_post_w_A','root_post_w_B','pitch','pcb_z','ground','dipolo_escala_externa']:
                np.testing.assert_allclose(p.get(key,1),prior.get(key,1),atol=1e-12,rtol=0)
            for key in ['extra_A','extra_B','lower','upper']:
                np.testing.assert_allclose(p.get(key,0),prior.get(key,0),atol=1e-12,rtol=0)
        prior=p;data.append(n.s)
        audit.append(dict(fonte=str(folder),s2p_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),geometria_sha256=hashlib.sha256((folder/'geometria.json').read_bytes()).hexdigest(),campos_sha256={axis:hashlib.sha256((folder/('AB_'+axis+'.csv')).read_bytes()).hexdigest() for axis in 'HV'},passes=r['passes'],delta_s=r['delta_s']))
    assert 3<=len(data)<=5
    parameters=np.array(parameters)
    stable=np.ptp(parameters,axis=0)<1e-5
    # Colunas nominalmente fixas nao devem criar restricoes artificiais pela
    # diferenca numerica de poucos nanometros entre saidas do otimizador.
    parameters[:,stable]=np.round(np.mean(parameters[:,stable],axis=0),4)
    # A ultima fonte e a referencia; os coeficientes descrevem passos
    # geometricos efetivamente observados, incluindo acoplamento e descontinuidades.
    p0=parameters[-1];dp=parameters[:-1]-p0
    s0=data[-1];ds=np.array(data[:-1])-s0
    directions=len(data)-1
    assert np.linalg.matrix_rank(dp,tol=1e-6)==directions,'Escolher fontes geometricamente independentes'
    def predict(a):
        x=p0+a@dp;s=s0+np.einsum('k,kfij->fij',a,ds)
        gamma=np.column_stack((s@np.ones(2),np.diagonal(s,axis1=1,axis2=2)))
        v=(1+abs(gamma))/(1-abs(gamma))
        return x,s,v
    def cost(a):
        x,s,v=predict(a)
        if np.any(x[::2]<.4) or np.any(x[::2]>max_width+1e-6) or np.any(x[1::2]<2) or np.any(x[1::2]>20) or sum(x[1::2])>44:return 1e3
        if np.linalg.svd(s,compute_uv=False).max()>=1 or np.any(v<1):return 1e3
        return float(v[:,:2].max())
    fit=differential_evolution(cost,[(-extent,extent)]*directions,seed=17,tol=1e-11,popsize=16)
    x,s,v=predict(fit.x);assert cost(fit.x)<1e3
    factors={key+'_'+pol:float(value/scale) for key,value,scale in zip(keys,x,[w0,l0,w50,l0,w50,l0]) for pol in 'AB'};factors['root_flat_sections']=True
    proposal=dict(fatores=factors,secoes_raiz_mm=[dict(largura=float(w),comprimento=float(l)) for w,l in zip(x[::2],x[1::2])],coeficientes=fit.x.tolist(),pior_VSWR_ativo=float(v[:,:2].max()),pior_VSWR_casado=float(v[:,2:].max()),VSWR_pontos=v.tolist())
    estimated_fields={}
    for axis in 'HV':
        curves=[read_pattern(f/('AB_'+axis+'.csv')) for f in folders]
        theta=curves[-1][0]
        for t,e in curves:np.testing.assert_allclose(theta,t)
        es=np.array([e for t,e in curves]);field=es[-1]+np.einsum('k,kij->ij',fit.x,es[:-1]-es[-1])
        gain=10*np.log10(np.sum(abs(field)**2,axis=1));front=np.flatnonzero(abs(theta)<=90);peak=front[np.argmax(gain[front])]
        estimated_fields[axis]=dict(ganho_frontal_dBi=float(gain[np.argmin(abs(theta))]),maximo_graus=float(theta[peak]),abertura_graus=float(beam(theta,gain)[0]))
        if axis=='V':estimated_fields[axis]['SLL']=sidelobe(theta,gain)
    proposal['campos_estimados_nao_validados']=estimated_fields
    result=dict(estado='ESTIMATIVA_EMPIRICA_NAO_VALIDADA',fonte=str(folders[-1]),arquivo_s2p='triagem3.s2p',s2p_sha256=audit[-1]['s2p_sha256'],fontes=audit,direcoes_independentes=directions,colunas_numericamente_fixas=[keys[i] for i in np.flatnonzero(stable)],tolerancia_fixas_mm=1e-5,metodo='Modelo afim local de S complexo e geometria a partir de %d ensaios reais. Inclui apenas %d direcoes amostradas. Extrapolacao nao confirma VSWR, convergencia ou diagrama; requer novo HFSS.'%(len(data),directions),faixa_GHz=[5.09,5.25],pontos=3,limite_coeficiente=extent,largura_max_mm=max_width,alvo_VSWR=1.25,empirico=proposal)
    Path(out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(proposal,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('fontes',nargs='+');p.add_argument('saida');p.add_argument('--extensao',type=float,default=1.);p.add_argument('--largura-max',type=float,default=5.);a=p.parse_args();assert 0<a.extensao<=2;run(a.fontes,a.saida,a.extensao,a.largura_max)
