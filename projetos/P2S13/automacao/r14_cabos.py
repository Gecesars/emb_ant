"""Seis coaxiais de mesmo comprimento, curvaturas tangentes e saídas soldadas."""
from pathlib import Path
import sys,json,math
import numpy as np
from scipy.optimize import brentq
from scipy.spatial import cKDTree
HERE=Path(__file__).parent;REPO=HERE.parents[2]
sys.path.insert(0,str(REPO/'freecad/mecanica_R01/fonte'))
import formar_cabos as fc
fc.R=6.;R=6.
ROOT=Path('D:/dev/EMBRAER/P2S13/R14_Compacto_Simetrico_SemRadome/c00')
cfg=json.loads((ROOT/'configuracao.json').read_text());dc=json.loads((ROOT/'divisor/configuracao.json').read_text())
old={p['name']:p for p in cfg['portas_coaxiais']};zstart=cfg['divisor_translacao_z_mm']+.18;zplane=-18.
endpoints={}
for p in dc['portas']:
    if not p['name'].endswith('_A') or p['name'].startswith('IN_'):continue
    q=old[p['name']];endpoints[p['name']]=(np.array([p['x'],-p['y'],zstart]),np.array([q['x'],q['y'],14.949]))
def bend(points):return fc.fillet(points,r=R)
def total(edges):return float(sum(fc.lengths(edges)))
def route(key,offset=0,frac=.5):
    s,e=endpoints[key];direct=e[:2]-s[:2];norm=np.array([-direct[1],direct[0]])/np.linalg.norm(direct)
    if key=='R2_A':
        left=float(offset);plan=[s[:2],[left,s[1]],[left,e[1]],e[:2]]
    else:
        mid=s[:2]+frac*direct+offset*norm;plan=[s[:2],e[:2]] if abs(offset)<1e-10 else [s[:2],mid,e[:2]]
    return bend([s]+[[*p,zplane] for p in plan]+[e])
minimum=max(total(route(k)) for k in ['R1_A','R3_A']);chosen=None
for length in np.arange(math.ceil(minimum),161,1):
    candidates={}
    for key in endpoints:
        options=[]
        if key=='R2_A':
            try:
                x=brentq(lambda x:total(route(key,x))-length,-100,-25);options=[route(key,x)]
            except ValueError:pass
        else:
            for frac in [.25,.4,.5,.6,.75]:
                for sign in [-1,1]:
                    previous=None
                    for off in np.linspace(0,60,121):
                        try:value=total(route(key,sign*off,frac))-length
                        except ValueError:continue
                        if previous and value*previous[1]<=0:
                            try:
                                t=brentq(lambda t:total(route(key,sign*t,frac))-length,previous[0],off);options.append(route(key,sign*t,frac))
                            except ValueError:pass
                            break
                        previous=(off,value)
        accepted=[]
        for edges in options:
            pts=fc.sample(edges,.4)
            if max(pts[:,1])>-.001 or min(pts[:,1])<-44:continue
            if not(-147<min(pts[:,0]) and max(pts[:,0])<147):continue
            # Last bend entirely behind reflector; final segment aligned with existing hole.
            if edges[-1][1][2]>-8:continue
            assert abs(total(edges)-length)<1e-6
            accepted.append((float(np.max(abs(pts[:,1]))),edges,pts,cKDTree(pts)))
        candidates[key]=sorted(accepted,key=lambda x:x[0])
    if not all(candidates.values()):continue
    for a in candidates['R1_A']:
      for b in candidates['R2_A']:
       for c in candidates['R3_A']:
        opts=[a,b,c]
        if any(min(opts[j][3].query(opts[i][2])[0])<4.3 for i in range(3) for j in range(i)):continue
        chosen=dict(zip(['R1_A','R2_A','R3_A'],[o[1] for o in opts]));break
       if chosen:break
      if chosen:break
    if chosen:break
assert chosen,'Nao encontrou seis cabos iguais com folga'
allroutes=dict(chosen)
for name,edges in chosen.items():allroutes[name[:-1]+'B']=[[e[0]]+[[x,-y,z] for x,y,z in e[1:]] for e in edges]
clouds={k:fc.sample(v,.2) for k,v in allroutes.items()};keys=list(clouds);clearance=min(min(cKDTree(clouds[keys[j]]).query(clouds[keys[i]])[0]) for i in range(6) for j in range(i))
assert clearance>4.1
cfg['cabos']=dict(comprimento_mm=float(length),raio_dobra_mm=R,raio_interno_mm=.45975,raio_dieletrico_mm=1.515,raio_externo_mm=1.7905,
    quantidade=6,perdas=True,distancia_minima_eixos_mm=float(clearance),folga_minima_estimativa_mm=float(clearance-2*1.7905),
    criterio='Mesmo material, diametros e comprimento do eixo; soldas iguais; sem atenuacao/fase artificial. Folgas definitivas no CAD.',
    comprimento_minimo_familia_direta_mm=minimum)
(ROOT/'cabos.json').write_text(json.dumps(allroutes,indent=2)+'\n');(ROOT/'configuracao.json').write_text(json.dumps(cfg,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
(ROOT/'igualdade_cabos.json').write_text(json.dumps(dict(comprimentos_mm={k:total(v) for k,v in allroutes.items()},**cfg['cabos']),indent=2)+'\n')
print(json.dumps(cfg['cabos'],indent=2))
