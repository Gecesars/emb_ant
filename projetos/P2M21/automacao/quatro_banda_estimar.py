"""Seleciona larguras para ensaio HFSS; modelo equivalente nao qualifica RF."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
import skrf as rf
from skrf.media.mline import MLine
from scipy.optimize import differential_evolution,minimize_scalar
from shapely.geometry import LineString

ROOT=Path('D:/dev/EMBRAER/P2M21/R13_Casamento_Banda')
BASE=Path('D:/dev/EMBRAER/P2M21/R12_Quatro_8Passes_Fast/antena')
VSWR_TARGET=1.25

def estimate(folder=BASE,triagem=False,output=None,middle_only=False,extended_only=False):
    folder=Path(folder);g=json.loads((folder/'geometria.json').read_text())
    source_file=folder/('triagem3.s2p' if triagem else 'banda_fast.s2p')
    net=rf.Network(str(source_file))
    np.testing.assert_allclose(net.f,np.arange(5090,5251,80 if triagem else 1)*1e6,rtol=0,atol=.01)
    cfg=json.loads((folder/'configuracao.json').read_text());p=g['parametros']
    assert not any(p.get('root_seg%d_l_%s'%(i,pol),0.) for i in (2,3,4) for pol in 'AB'),'Usar estimador de multiplas secoes para esta topologia'
    assert p['simetria'] and cfg['espacamento_vertical_mm']==48
    assert cfg['distancia_face_inferior_laminado_ao_refletor_mm']==14.949
    w0=g['lines']['70.71067811865476']['w_mm'];l0=g['lines']['70.71067811865476']['l90_mm']
    wr=w0*p.get('root_w_A',1);lr=l0*p.get('root_l_A',1)
    assert p.get('root_w_A',1)==p.get('root_w_B',1) and p.get('root_l_A',1)==p.get('root_l_B',1)
    rt=next(t for t in g['traces'] if t['tipo']=='raiz' and t['polarizacao']=='A')
    lt=next(t for t in g['traces'] if t['tipo']=='local' and t['polarizacao']=='A')
    root_total=LineString(rt['linha70']+rt['linha50'][1:]).length
    local_total=LineString(lt['linha70']+lt['linha50'][1:]).length
    wl=lt['largura_transformador_mm'];ll=LineString(lt['linha70']).length
    w50=g['lines']['50']['w_mm']
    root_post=w50*p.get('root_post_w_A',1.)
    local_post=w50*p.get('local_post_w_A',1.)
    for key in ['root_post_w','local_post_w']:
        assert p.get(key+'_A',1.)==p.get(key+'_B',1.)
    def section(width,length):
        m=MLine(frequency=net.frequency,w=width/1000,h=.00076,t=.000035,ep_r=3.66,tand=.0037,diel='frequencyinvariant',rho=1/5.8e7,rough=.5e-6)
        t=m.gamma*length/1000;z=m.z0
        a=np.empty((len(net.f),2,2),complex)
        a[:,0,0]=a[:,1,1]=np.cosh(t);a[:,0,1]=z*np.sinh(t);a[:,1,0]=np.sinh(t)/z
        return a
    def line(width,length,total,post_width):return section(width,length)@section(post_width,total-length)
    def apply(m,z):return (m[:,0,0,None]*z+m[:,0,1,None])/(m[:,1,0,None]*z+m[:,1,1,None])
    gamma=np.column_stack((net.s@np.ones(2),np.diagonal(net.s,axis1=1,axis2=2)))
    cable=np.exp(2j*2*np.pi*net.f/299792458*np.sqrt(2.036363533774732)*.05)[:,None]
    pcb_gamma=gamma*cable;zin=50*(1+pcb_gamma)/(1-pcb_gamma)
    load_root=apply(np.linalg.inv(line(wr,lr,root_total,root_post)),2*zin)
    load_element=apply(np.linalg.inv(line(wl,ll,local_total,local_post)),2*load_root)
    def values(dim):
        rw,lw=dim[:2];rl,local_length=dim[2:4] if len(dim)>=4 else (lr,ll)
        rp,lp=dim[4:6] if len(dim)==6 else (root_post,local_post)
        local_in=apply(line(lw,local_length,local_total,lp),load_element)/2
        newzin=apply(line(rw,rl,root_total,rp),local_in)/2
        ref=abs((newzin-50)/(newzin+50))
        if np.any(ref>=1):return np.full(ref.shape,1e6)
        return (1+ref)/(1-ref)
    actual=(1+abs(gamma))/(1-abs(gamma));reproduced=values([wr,wl])
    np.testing.assert_allclose(actual,reproduced,atol=2e-12,rtol=2e-12)
    def summary(dim):
        v=values(dim)
        rl,local_length=dim[2:4] if len(dim)>=4 else (lr,ll)
        rp,lp=dim[4:6] if len(dim)==6 else (root_post,local_post)
        return dict(largura_raiz_mm=float(dim[0]),largura_local_mm=float(dim[1]),comprimento_raiz_mm=float(rl),comprimento_local_mm=float(local_length),
            largura_pos_raiz_mm=float(rp),largura_pos_local_mm=float(lp),
            fatores=dict(root_w_A=float(dim[0]/w0),root_w_B=float(dim[0]/w0),local_w_A=float(dim[1]/w0),local_w_B=float(dim[1]/w0),root_l_A=float(rl/l0),root_l_B=float(rl/l0),local_l_A=float(local_length/l0),local_l_B=float(local_length/l0),root_post_w_A=float(rp/w50),root_post_w_B=float(rp/w50),local_post_w_A=float(lp/w50),local_post_w_B=float(lp/w50)),
            pior_VSWR_ativo=float(v[:,:2].max()),pior_VSWR_casado=float(v[:,2:].max()),pior_VSWR_geral=float(v.max()),
            extremos=[dict(condicao=n,maximo=float(v[:,i].max()),frequencia_GHz=float(net.f[np.argmax(v[:,i])]/1e9)) for i,n in enumerate(['ativo_A','ativo_B','casado_A','casado_B'])])
    if extended_only:
        limits=[(.4,2.),(.65,1.3),(3.,12.),(8.,18.),(1.1,2.3),(1.1,2.3)]
        fit=differential_evolution(lambda x:values(x).max(),limits,seed=59,tol=1e-8,popsize=14,workers=1)
        result=dict(estado='ESTIMATIVA_PARA_SELECAO_NAO_VALIDADA',fonte=str(folder),arquivo_s2p=source_file.name,s2p_sha256=hashlib.sha256(source_file.read_bytes()).hexdigest(),
            metodo='Modelo equivalente de dois estagios; inclui largura ajustavel dos trechos posteriores aos transformadores. As quatro cargas efetivas por frequencia permanecem congeladas. Nao valida acoplamento nem diagramas; exige HFSS completo.',
            faixa_GHz=[5.09,5.25],alvo_VSWR=VSWR_TARGET,pontos=len(net.f),triagem_tres_frequencias=triagem,erro_recomposicao=float(abs(actual-reproduced).max()),
            referencia=summary([wr,wl]),limites_segmentos_mm=limits,segmentos_completos=summary(fit.x))
        out=Path(output) if output else ROOT/('estimativa_segmentos_'+folder.name+'.json')
        out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2));return result
    if middle_only:
        limits=[(.4,2.),(.65,1.3),(3.,12.),(8.,18.)]
        fit=differential_evolution(lambda x:values(x).max(),limits,seed=47,tol=1e-8,popsize=14,workers=1)
        fit_active=differential_evolution(lambda x:values(x)[:,:2].max(),limits,seed=49,tol=1e-8,popsize=14,workers=1)
        result=dict(estado='ESTIMATIVA_PARA_SELECAO_NAO_VALIDADA',fonte=str(folder),arquivo_s2p=source_file.name,s2p_sha256=hashlib.sha256(source_file.read_bytes()).hexdigest(),
            metodo='MLine com quatro cargas efetivas congeladas por frequencia; inclui a fase nominal dos cabos. Limita largura local a pelo menos0.65mm para evitar o estreitamento extremo do C01. Requer confirmacao HFSS completa e conferencia dos diagramas.',
            faixa_GHz=[5.09,5.25],alvo_VSWR=VSWR_TARGET,pontos=len(net.f),triagem_tres_frequencias=triagem,erro_recomposicao=float(abs(actual-reproduced).max()),
            referencia=summary([wr,wl]),limites_locais_intermediarios_mm=limits,locais_intermediarios=summary(fit.x),locais_intermediarios_ativo=summary(fit_active.x))
        out=Path(output) if output else ROOT/('estimativa_intermediaria_'+folder.name+'.json')
        out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2));return result
    one=minimize_scalar(lambda w:values([w,wl]).max(),bounds=(.4,1.3),method='bounded',options={'xatol':1e-7})
    both=differential_evolution(lambda x:values(x).max(),[(.4,1.3),(.5,1.3)],seed=19,tol=1e-8,popsize=12,workers=1)
    def active_objective(x):
        v=values(x)
        return v[:,:2].max()+1000*max(0,v[:,2:].max()-VSWR_TARGET)
    active=differential_evolution(active_objective,[(.4,1.3),(.5,1.3)],seed=23,tol=1e-8,popsize=12,workers=1)
    root_wl=differential_evolution(lambda x:values([x[0],wl,x[1],ll]).max(),[(.4,1.3),(6.5,11.5)],seed=29,tol=1e-8,popsize=12,workers=1)
    all_wl=differential_evolution(lambda x:values(x).max(),[(.4,1.3),(.4,1.3),(4.,12.),(6.,18.)],seed=31,tol=1e-8,popsize=12,workers=1)
    # Depois de cada ensaio real, limitar o proximo deslocamento geometrico.
    # Mudancas grandes dos trechos locais alteram a radiacao e invalidam a carga congelada.
    bounded_limits=[(max(.4,.8*wr),min(1.3,1.2*wr)),
                    (max(.4,.88*wl),min(1.3,1.12*wl)),
                    (max(4.,lr-1.),min(12.,lr+1.)),
                    (max(6.,ll-.75),min(18.,ll+.75))]
    bounded=differential_evolution(lambda x:values(x).max(),bounded_limits,seed=37,tol=1e-8,popsize=12,workers=1)
    wide_limits=[(.4,1.8),(w0,1.8),(4.,12.),(6.,12.)]
    wide=differential_evolution(lambda x:values(x).max(),wide_limits,seed=41,tol=1e-8,popsize=12,workers=1)
    middle_limits=[(.4,1.8),(.65,1.3),(3.,10.),(8.,14.)]
    middle=differential_evolution(lambda x:values(x).max(),middle_limits,seed=43,tol=1e-8,popsize=12,workers=1)
    result=dict(estado='ESTIMATIVA_PARA_SELECAO_NAO_VALIDADA',fonte=str(folder),arquivo_s2p=source_file.name,s2p_sha256=hashlib.sha256(source_file.read_bytes()).hexdigest(),
       metodo='Cascata MLine de dois estagios; quatro cargas equivalentes efetivas congeladas por frequencia (AB e outra entrada casada). Cabos desembutidos apenas pela fase nominal. Reproduzir a fonte por construcao nao e validacao independente. Acoplamento, radiacao das linhas, curvas e perdas reais dos cabos exigem HFSS completo.',
       faixa_GHz=[5.09,5.25],alvo_VSWR=VSWR_TARGET,pontos=len(net.f),triagem_tres_frequencias=triagem,erro_recomposicao=float(abs(actual-reproduced).max()),
       limites_dois_estagios_mm=dict(largura_raiz=[.4,1.3],largura_local=[.4,1.3],comprimento_raiz=[4,12],comprimento_local=[6,18]),
       referencia=summary([wr,wl]),somente_raiz=summary([one.x,wl]),raiz_e_locais=summary(both.x),prioridade_ativo=summary(active.x),
       raiz_largura_comprimento=summary([root_wl.x[0],wl,root_wl.x[1],ll]),dois_estagios_dimensoes=summary(all_wl.x),
       limites_vizinhanca_mm=bounded_limits,vizinhanca_conservadora=summary(bounded.x),
       limites_locais_largos_mm=wide_limits,locais_largos=summary(wide.x),
       limites_locais_intermediarios_mm=middle_limits,locais_intermediarios=summary(middle.x))
    ROOT.mkdir(exist_ok=True)
    out=Path(output) if output else ROOT/('estimativa_'+folder.name+'.json');out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--fonte',default=str(BASE));a.add_argument('--triagem',action='store_true');a.add_argument('--saida');a.add_argument('--somente-intermediarios',action='store_true');a.add_argument('--segmentos-completos',action='store_true');args=a.parse_args();estimate(Path(args.fonte),args.triagem,args.saida,args.somente_intermediarios,args.segmentos_completos)
