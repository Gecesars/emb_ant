"""Pre-dimensiona a raiz comum A/B com cargas equivalentes congeladas.
Nao modela irradiacao das trilhas ou alteracoes do acoplamento. Exige novo HFSS.
"""
from pathlib import Path
import argparse,json
import numpy as np
import skrf as rf
from skrf.media.mline import MLine
from scipy.optimize import differential_evolution
from shapely.geometry import LineString

ROOT=Path('D:/dev/EMBRAER/P2M21/R11_Divisor_Ajustes')

def main(name,new_pitch=None):
    folder=ROOT/name;g=json.loads((folder/'geometria.json').read_text())
    p=g['parametros'];w0=g['lines']['70.71067811865476']['w_mm'];l0=g['lines']['70.71067811865476']['l90_mm']
    w=w0*p.get('root_w_A',1);length=l0*p.get('root_l_A',1)
    assert p.get('root_w_B',1)==p.get('root_w_A',1) and p.get('root_l_B',1)==p.get('root_l_A',1)
    rt=next(t for t in g['traces'] if t['tipo']=='raiz' and t['polarizacao']=='A')
    total=LineString(rt['linha70']+rt['linha50'][1:]).length
    freq=rf.Frequency(5.17,5.17,1,'GHz')
    def section(width,mm):
        m=MLine(frequency=freq,w=width/1000,h=.00076,t=.000035,ep_r=3.66,tand=.0037,diel='frequencyinvariant',rho=1/5.8e7,rough=.5e-6)
        t=m.gamma[0]*mm/1000;z=m.z0[0]
        return np.array([[np.cosh(t),z*np.sinh(t)],[np.sinh(t)/z,np.cosh(t)]])
    def root(width,mm,route=total):return section(width,mm)@section(g['lines']['50']['w_mm'],route-mm)
    def apply(m,z):return (m[0,0]*z+m[0,1])/(m[1,0]*z+m[1,1])
    s=rf.Network(str(folder/'centro.s2p')).s[0]
    gamma=np.array([s[0].sum(),s[1].sum(),s[0,0],s[1,1]])
    beta=2*np.pi*5.17e9/299792458*np.sqrt(2.036363533774732)
    cable_phase=np.exp(2j*beta*.05)
    pcb_gamma=gamma*cable_phase
    zin=50*(1+pcb_gamma)/(1-pcb_gamma)
    loads=apply(np.linalg.inv(root(w,length)),2*zin)
    new_total=total
    new_loads=loads.copy()
    if new_pitch is not None:
        assert not p.get('root_extra',0) and not p.get('upper',0) and not p.get('lower',0)
        lt=next(t for t in g['traces'] if t['tipo']=='local' and t['polarizacao']=='A')
        local_total=LineString(lt['linha70']+lt['linha50'][1:]).length
        local_w=lt['largura_transformador_mm'];local_l=LineString(lt['linha70']).length
        local_old=section(local_w,local_l)@section(g['lines']['50']['w_mm'],local_total-local_l)
        element_loads=apply(np.linalg.inv(local_old),2*loads)
        change=float(new_pitch)-g['passo_vertical_mm']
        local_new=section(local_w,local_l)@section(g['lines']['50']['w_mm'],local_total+change/2-local_l)
        new_loads=apply(local_new,element_loads)/2
        new_total=total+change
    def values(dim,route,load):
        newzin=apply(root(*dim,route=route),load)/2
        ref=abs((newzin-50)/(newzin+50))
        if np.any(ref>=1):return np.full(4,1e6)
        return (1+ref)/(1-ref)
    def vswr(dim):return values(dim,new_total,new_loads)
    reference=values([w,length],total,loads);actual=(1+abs(gamma))/(1-abs(gamma))
    np.testing.assert_allclose(reference,actual,atol=1e-12,rtol=1e-12)
    opt=differential_evolution(lambda x:max(vswr(x)),[(.4,1.3),(5.,14.)],seed=17,tol=1e-8)
    result=dict(fonte=str(folder/'centro.s2p'),metodo='Modelo nominal MLine raiz+linha50; cabos ideais de fase para desembutimento; quatro cargas efetivas congeladas (AB e outra entrada casada). Requer HFSS completo.',
       estado='ESTIMATIVA_NAO_VALIDADA',largura_mm=float(opt.x[0]),comprimento_mm=float(opt.x[1]),
       passo_fonte_mm=g['passo_vertical_mm'],passo_novo_mm=new_pitch,
       root_w_factor=float(opt.x[0]/w0),root_l_factor=float(opt.x[1]/l0),
       VSWR_estimado_ativo=vswr(opt.x)[:2].tolist(),VSWR_estimado_casado=vswr(opt.x)[2:].tolist(),
       erro_recomposicao_modelo_original=float(max(abs(reference-actual))))
    if new_pitch is not None:
        result['metodo']+=' Novo passo: modelo em cascata dos dois estagios e cargas terminais congeladas; acoplamento, curvas e nova borda de placa nao previstos.'
    filename='estimativa_transformador_comum.json' if new_pitch is None else 'estimativa_passo_%g.json'%new_pitch
    (folder/filename).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('variant');a.add_argument('--pitch',type=float);args=a.parse_args();main(args.variant,args.pitch)
