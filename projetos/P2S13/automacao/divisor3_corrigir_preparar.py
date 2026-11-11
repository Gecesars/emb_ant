"""Divisao direta de tres vias: geometria e sintese carregada, sem isolamento resistivo."""
from pathlib import Path
import sys,os,json,math,shutil
import numpy as np
from scipy.optimize import differential_evolution,brentq
from shapely.geometry import LineString,Point,box
from shapely.ops import unary_union
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0,str(Path(__file__).parent))
from divisor_duplo3_planejar import medium,F,SA,fields,angles,dual,load
from skrf.circuit import Circuit
REPO=Path(__file__).resolve().parents[3]
ROOT=Path(os.environ['P2S13_DIV3_ROOT']);ROOT.mkdir(parents=True,exist_ok=True)
assert not (ROOT/'Divisor_Duplo3.aedt').exists()
params=json.loads(os.environ.get('P2S13_DIV3_PARAM','{}'))
C=2.50916841304;Y=2.5 if params.get('route')=='aberta' else 4.;M50=medium(50.);lambda50=float(2*np.pi/M50.beta[0]*1000)
def chamfer(pts,r=1.5):
    out=[pts[0]]
    for a,b,c in zip(pts,pts[1:],pts[2:]):
        a,b,c=map(lambda p:np.array(p,float),(a,b,c));assert min(np.linalg.norm(a-b),np.linalg.norm(c-b))>2*r
        out.extend([(b+r*(a-b)/np.linalg.norm(a-b)).tolist(),(b+r*(c-b)/np.linalg.norm(c-b)).tolist()])
    return out+[pts[-1]]
def geometry(zq,lq,middle_delta=0):
    # Radial three-way launch. Quarter-wave trace centerlines never fold onto each other.
    dx,dy=(math.sqrt(lq*lq-(6-Y)**2),6-Y) if params.get('route')=='aberta' else (lq*.819152044289,lq*.573576436351)
    qs=[[[C,Y],[C-dx,Y+dy]],[[C,Y],[C,Y+lq]],[[C,Y],[C+dx,Y+dy]]]
    osides=[]
    for k,sgn in [(0,-1),(2,1)]:
        end=qs[k][-1];out=[C+sgn*96,18.]
        delta=params.get('outer_delta_mm',[0.,0.])[0 if k==0 else 1]
        radius=1.5-float(delta)/(2-math.sqrt(2));assert .4<radius<3.5
        osides.append(chamfer([end,[out[0],end[1]],out],r=radius))
    side_lengths=[float(LineString(p).length) for p in osides]
    lo=float(np.mean(side_lengths))
    end=qs[1][-1];lm=lo-2*lambda50+middle_delta
    um=brentq(lambda u:LineString(chamfer([end,[C+u,end[1]],[C+u,18.],[C,18.]])).length-lm,3.1,20.)
    om=chamfer([end,[C+um,end[1]],[C+um,18.],[C,18.]])
    return qs,[osides[0],om,osides[1]],[side_lengths[0],lm,side_lengths[1]]
def net(z,l,md=0):
    _,_,ls=geometry(z,l,md);nodes=[[] for _ in range(7)]
    for i in range(3):
        zi=float(params.get('middle_Z',z)) if i==1 else float(z)
        q=medium(zi).line(l/1000,unit='m',name='Q%d'%i);o=M50.line(ls[i]/1000,unit='m',name='O%d'%i)
        nodes[0].append((q,0));nodes[1+i]=[(q,1),(o,0)];nodes[4+i]=[(o,1),(Circuit.Port(F,'R%d'%i),0)]
    nodes[0].insert(0,(Circuit.Port(F,'IN'),0));return Circuit(nodes).network
def objective(x):
    s,a=load(dual(net(*x)));r=max(abs(s@np.ones(2)).max(),abs(np.diag(s)).max())
    amp=np.ptp(20*np.log10(abs(a)));phase=np.ptp(np.angle(a/a[2],deg=True))
    return r+0.025*amp+0.002*phase
if params and not params.get('optimize'):
    z=float(params['Zq']);l=float(params['Lq']);md=float(params.get('middle_delta',0))
else:
    bounds=[(65,110),(6.5,11.),(-1.5,1.5)] if params.get('route')=='aberta' else [(72,105),(9.5,9.8),(-1.,1.)]
    opt=differential_evolution(objective,bounds,seed=5170,popsize=7,maxiter=60,tol=1e-5)
    z,l,md=map(float,opt.x)
n=net(z,l,md);s,a=load(dual(n));g0=10*np.log10(np.sum(abs(fields['H'][np.argmin(abs(angles))]@a)**2))
qs,outs,ls=geometry(z,l,md);curves=[];signals={};polys=[];ports=[]
for pol,sgn in [('A',1),('B',-1)]:
    parts=[]
    for i in range(3):
        for prefix,path,zz in [('Q',qs[i],float(params.get('middle_Z',z)) if i==1 else z),('O',outs[i],50.)]:
            pts=[[x,sgn*y] for x,y in path];w=float(medium(zz).w*1000)
            sh=LineString(pts).buffer(w/2,cap_style=2,join_style=2,mitre_limit=2)
            parts.append((prefix+str(i+1),sh,pts))
            curves.append(dict(name=pol+'_'+prefix+str(i+1),points=pts,Z_ohm=zz,width_mm=w,length_mm=float(LineString(pts).length)))
    for ia,(na,pa,aa) in enumerate(parts):
        for nb,pb,bb in parts[ia+1:]:
            hit=pa.intersection(pb)
            if hit.area<1e-8:continue
            shared=[p for p in [aa[0],aa[-1]] if any(np.linalg.norm(np.array(p)-q)<1e-6 for q in [bb[0],bb[-1]])]
            assert shared,(na,nb,'short',hit.area)
            assert hit.difference(unary_union([Point(p).buffer(3) for p in shared])).area<1e-8,(na,nb,'longoverlap')
    for name,pt in [('IN_'+pol,[C,Y])]+[('R%d_%s'%(i+1,pol),[C+(i-1)*96,18]) for i in range(3)]:
        x,y=pt[0],sgn*pt[1];ports.append(dict(name=name,x=x,y=y,z=-.18,ri=.45975,ro=1.515));pad_r=float(params.get('input_pad_r',.65)) if name.startswith('IN_') else .65
        parts.append((name,Point(x,y).buffer(pad_r,quad_segs=12 if pad_r==.65 else 24),[]))
    shape=unary_union([p for _,p,_ in parts]);assert shape.geom_type=='Polygon' and shape.is_valid
    assert box(-110,-32,110,32).contains(shape)
    signals[pol]=dict(exterior=list(shape.exterior.coords),holes=[list(r.coords) for r in shape.interiors]);polys.append(shape)
assert polys[0].distance(polys[1])>.2
cfg=dict(native='Divisor_Duplo3.aedt',design='Duplo1x3_Planar',frequency_GHz=5.17,nucleos=14,max_passes=6,min_passes=2,delta_s=.05,
    material='ZYF300',er=2.94,tand=.0016,h=1.52,cu=.035,board=[220,64],sources=['IN_A','IN_B'],portas=ports,resistores=[],signals=signals,traces=curves,
    topology='Trifurcacao nao isolada; tres transformadores de impedancia, rotas50ohm em fase no centro; ramal central encurtado por duas ondas guiadas. A/B espelhados.',
    parametros=dict(Zq=z,Lq=l,middle_delta=md,middle_Z=float(params.get('middle_Z',z)),route=params.get('route','compacta'),input_pad_r=float(params.get('input_pad_r',.65)),outer_delta_mm=params.get('outer_delta_mm',[0.,0.])),percent_refinement=params.get('percent_refinement',30),basis_order=params.get('basis_order',1),out_lengths=ls,lambda50_mm=lambda50,
    nominal_VSWR_ativo=((1+abs(s@np.ones(2)))/(1-abs(s@np.ones(2)))).tolist(),nominal_VSWR_casado=((1+abs(np.diag(s)))/(1-abs(np.diag(s)))).tolist(),
    nominal_ganho_frontal_dBi=float(g0),nominal_potencias_W=(abs(a)**2).tolist(),nominal_fases_graus=np.angle(a/a[2],deg=True).tolist(),
    nominal_saida_modulo=abs(n.s[0,1:,0]).tolist(),nominal_saida_fase=np.angle(n.s[0,1:,0],deg=True).tolist())
if params.get('mask_windows'):
    cfg['mask_windows']=dict(over_laminate_mm=.02032,over_copper_mm=.0127,er=3.8,tand=.025,
        x_relative_to_center_mm=[[ -90,-20],[20,90]],nota='Espessuras/Dk de referencia JLC; Df0.025 nominal assumido em5.17GHz com referencia generica Rogers1GHz. ENIG somente nas areas abertas; mascaras nao removem perdas dieletricas.')
if params.get('shield_gap_mm'):
    cfg['shield']=dict(gap_above_copper_mm=float(params['shield_gap_mm']),wall_mm=1.,material='AL5052',conductivity_S_m=2e7,
        note='Tampa e paredes metalicas aterradas por contato continuo com borda da massa. Contato perfeito nominal; precisa detalhamento mecanico antes de fabricar.')
(ROOT/'configuracao.json').write_text(json.dumps(cfg,indent=2)+'\n')
shutil.copy2(REPO/'projetos/P2S13/continuacao_tres_placas2/HFSS_14nucleos.acf',ROOT/'HFSS_14nucleos.acf')
fig,ax=plt.subplots(figsize=(12,4.5));ax.add_patch(plt.Rectangle((-110,-32),220,64,color='#e3e8dd'))
for sh in polys:
    ax.fill(*sh.exterior.xy,color='#bb7b28')
    for hole in sh.interiors:ax.fill(*hole.xy,color='#e3e8dd')
if cfg.get('mask_windows'):
    for left,right in cfg['mask_windows']['x_relative_to_center_mm']:
        ax.add_patch(plt.Rectangle((C+left,-32),right-left,64,color='#237a4a',alpha=.32))
for p in ports:ax.plot(p['x'],p['y'],'o',ms=3,color='navy');ax.annotate(p['name'],(p['x'],p['y']),xytext=(0,7),textcoords='offset points',ha='center',fontsize=8)
ax.set(xlim=(-114,114),ylim=(-35,35),xlabel='X (mm)',ylabel='Y (mm)',title='Divisor duplo 1:3 direto — ZYF300CA-C 1,52 mm — 220 × 64 mm\nA/B espelhados; sem resistores de isolamento; somente 5,17 GHz');ax.set_aspect('equal');fig.tight_layout();fig.savefig(ROOT/'layout.png',dpi=180);plt.close(fig)
print(json.dumps({k:v for k,v in cfg.items() if k.startswith('nominal') or k=='parametros'},indent=2))
