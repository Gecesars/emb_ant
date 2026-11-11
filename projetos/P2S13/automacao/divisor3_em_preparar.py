"""Sintese e roteamento planar do divisor 1:3 em cascata, duplicado A/B."""
from pathlib import Path
import json,sys,math,shutil,os
import numpy as np
from scipy.optimize import brentq,differential_evolution
from shapely.geometry import LineString,Point,Polygon,box
from shapely.ops import unary_union
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(Path(__file__).parent))
from divisor_duplo3_planejar import medium,F,SA
from skrf.circuit import Circuit
import skrf as rf
ROOT=Path(os.environ.get('P2S13_DIV3_ROOT','D:/dev/EMBRAER/P2S13/R08_Divisor_HFSS'));ROOT.mkdir(exist_ok=True)
CORRIGIR=os.environ.get('P2S13_DIV3_JUNCAO')=='1'
delay_len=17. if CORRIGIR else 7.5
assert not (ROOT/'Divisor_Duplo3.aedt').exists(),'Nao alterar modelo existente.'
C=2.50916841304;W50=float(medium(50.).w*1000)
def q(z):return float(np.pi/(2*medium(float(z)).beta[0])*1000)
K=np.sqrt(2);ZH=50*np.sqrt(K*(1+K*K));ZL=50*np.sqrt((1+K*K)/K**3)
ZMH=np.sqrt(50*50*K);ZML=np.sqrt(50*50/K);ZE=50*np.sqrt(2)
def line(z,l,name):return medium(float(z)).line(l/1000,unit='m',name=name)
def network(z=44.49,li=12.01,lo=None):
    lo=lo or lengths
    p=[('in',0,1,line(z,li,'in')),('qh',1,2,line(ZH,q(ZH),'qh')),('ql',1,3,line(ZL,q(ZL),'ql')),
       ('mh',2,4,line(ZMH,q(ZMH),'mh')),('ml',3,5,line(ZML,q(ZML),'ml')),
       ('bh',4,6,line(50.,bypass_len,'bh')),('dl',5,7,line(50.,delay_len,'dl')),
       ('e1',7,8,line(ZE,q(ZE),'e1')),('e2',7,9,line(ZE,q(ZE),'e2')),
       ('r1',2,3,Circuit.SeriesImpedance(F,float(50*(K+1/K)),'r1')),
       ('r2',8,9,Circuit.SeriesImpedance(F,100.,'r2')),
       ('o1',6,10,line(50.,lo[0],'o1')),('o2',8,11,line(50.,lo[1],'o2')),('o3',9,12,line(50.,lo[2],'o3'))]
    nodes=[[] for _ in range(13)]
    for _,i,j,n in p:nodes[i].append((n,0));nodes[j].append((n,1))
    for name,i in zip(['IN','R1','R2','R3'],[0,10,11,12]):nodes[i].append((Circuit.Port(F,name),0))
    return Circuit(nodes).network

traces=[]
def add(name,points,z,length=None):
    points=[list(map(float,p)) for p in points];l=float(LineString(points).length)
    if length is not None:assert abs(l-length)<1e-7,(name,l,length)
    w=float(medium(float(z)).w*1000)
    traces.append(dict(name=name,points=points,Z_ohm=float(z),width_mm=w,length_mm=l))
    return points[-1]
def arm(name,start,dx,dy,z):
    l=q(z)
    sign=np.sign(dy)
    h=brentq(lambda h:math.hypot(dx/2,h)+math.hypot(dx/2,h-abs(dy))-l,abs(dy),20)
    return add(name,[start,[start[0]+dx/2,start[1]+sign*h],[start[0]+dx,start[1]+dy]],z,l)

I=[-43.,18.];H=arm('QH',I,6,4,ZH);L=arm('QL',I,6,-4,ZL)
MH=add('MH',[H,[H[0]+q(ZMH),H[1]]],ZMH)
ML=add('ML',[L,[L[0]+q(ZML),L[1]]],ZML)
delay_points=([ML,[ML[0]+8,ML[1]],[ML[0]+8,ML[1]-5],[ML[0]+12,ML[1]-5]] if CORRIGIR else [ML,[ML[0]+4,ML[1]],[ML[0]+4,ML[1]-3.5]])
DL=add('DELAY',delay_points,50.,delay_len)
E1=arm('E1',DL,6,3,ZE);E2=arm('E2',DL,6,-3,ZE)
# Cantos chanfrados de 45 graus; comprimento da linha central contabilizado.
def chamfer(points,r=2.):
    out=[points[0]]
    for a,b,c in zip(points,points[1:],points[2:]):
        a,b,c=map(lambda p:np.array(p,float),(a,b,c));u=(a-b)/np.linalg.norm(a-b);v=(c-b)/np.linalg.norm(c-b)
        assert min(np.linalg.norm(a-b),np.linalg.norm(c-b))>r*1.01
        out.extend([(b+r*u).tolist(),(b+r*v).tolist()])
    out.append(points[-1]);return out
R1=[C-96,18.];R2=[C,18.];R3=[C+96,18.]
out3=chamfer([E2,[R3[0],E2[1]],R3]);l3=LineString(out3).length
lambda50=4*q(50.)
# Ajustar o bypass junto com sua saida: total50ohm equivale ao ramo do
# segundo Wilkinson menos uma onda guiada, preservando fase no centro.
top=28.3
def path1(bl):
    bh=[MH[0]+bl,MH[1]]
    return chamfer([bh,[bh[0],top],[R1[0],top],R1])
bypass_len=brentq(lambda bl:bl+LineString(path1(bl)).length-(q(50.)+delay_len+l3-lambda50),3.,30.)
BH=add('BYPASS',[MH,[MH[0]+bypass_len,MH[1]]],50.)
out1=chamfer([BH,[BH[0],top],[R1[0],top],R1])
l1=LineString(out1).length
top2=26.
xmid=brentq(lambda x:LineString(chamfer([E1,[x,E1[1]],[x,top2],[R2[0],top2],R2])).length-l3,25.,65.)
out2=chamfer([E1,[xmid,E1[1]],[xmid,top2],[R2[0],top2],R2])
add('OUT1',out1,50.,l1);add('OUT2',out2,50.,l3);add('OUT3',out3,50.,l3)
lengths=[float(l1),float(l3),float(l3)]
def calc(z,li):
    n=network(z,li);s=np.zeros((8,8),complex)
    for ids in [[0,2,4,6],[1,3,5,7]]:s[np.ix_(ids,ids)]=n.s[0]
    t=np.linalg.solve(np.eye(6)-s[2:,2:]@SA,s[2:,:2]);ss=s[:2,:2]+s[:2,2:]@SA@t
    return ss,n
opt=differential_evolution(lambda x:max(abs(calc(*x)[0]@np.ones(2)).max(),abs(np.diag(calc(*x)[0])).max()),[(35,80),(1,20)],seed=5170,maxiter=55,popsize=7,tol=1e-6)
zin,lin=map(float,opt.x)
inputpt=[I[0]-lin,I[1]];add('INPUT',[inputpt,I],zin,lin)
n=network(zin,lin);s=calc(zin,lin)[0]
assert np.max(np.linalg.svd(n.s[0],compute_uv=False))<=1.00001
curves=[];signals={};resistors=[];ports=[];polys=[]
for pol,sign in [('A',1),('B',-1)]:
    parts=[]
    for tr in traces:
        pts=[[x,sign*y] for x,y in tr['points']]
        shape=LineString(pts).buffer(tr['width_mm']/2,cap_style=2,join_style=2,mitre_limit=2)
        parts.append((tr['name'],shape,pts));curves.append({**tr,'name':pol+'_'+tr['name'],'points':pts})
    # Verificar que trilhas nao adjacentes nao se curto-circuitam.
    for ia,(na,pa,a) in enumerate(parts):
        for nb,pb,b in parts[ia+1:]:
            hit=pa.intersection(pb)
            if hit.area<1e-8:continue
            shared=[x for x in [a[0],a[-1]] if any(np.linalg.norm(np.array(x)-y)<1e-6 for y in [b[0],b[-1]])]
            assert shared,(pol,na,nb,'curto',hit.area)
            allowed=unary_union([Point(p).buffer(6) for p in shared])
            assert hit.difference(allowed).area<1e-8,(na,nb,'sobreposicao fora da juncao')
    if CORRIGIR:
        byname={n:(p,pts) for n,p,pts in parts}
        for branch in ['E1','E2']:
            assert LineString(byname[branch][1]).intersection(byname['DELAY'][0]).length<1e-6,branch
    for name,start,end,R in [('R106',H,L,float(50*(K+1/K))),('R100',E1,E2,100.)]:
        x=start[0];ymid=(start[1]+end[1])/2
        assert abs(x-end[0])<1e-6
        # Pads flip-chip0402: largura.65, extensao1.4, vao.4.
        for a,b in [(start[1],ymid+.2),(end[1],ymid-.2)]:
            parts.append((name+'_lead',LineString([[x,sign*a],[x,sign*b]]).buffer(.325,cap_style=2,join_style=2),[]))
        resistors.append(dict(name=pol+'_'+name,x=x,y=sign*ymid,R=R,width=.65,gap=.4,body_l=1.,body_w=.6,body_h=.5))
    for name,pt in [('IN_'+pol,inputpt)]+[('R%d_%s'%(i,pol),pt) for i,pt in enumerate([R1,R2,R3],1)]:
        x,y=pt[0],sign*pt[1];parts.append((name,Point(x,y).buffer(.65,quad_segs=12),[]));ports.append(dict(name=name,x=x,y=y,z=-.18,ri=.45975,ro=1.515))
    shape=unary_union([p for _,p,_ in parts]);assert shape.geom_type=='Polygon' and shape.is_valid,(pol,shape.geom_type)
    signals[pol]=dict(exterior=list(shape.exterior.coords),holes=[list(r.coords) for r in shape.interiors]);polys.append(shape)
assert polys[0].distance(polys[1])>.2
for sh in polys:assert box(-110,-32,110,32).contains(sh),sh.bounds
cfg=dict(native='Divisor_Duplo3.aedt',design='Duplo1x3_Planar',frequency_GHz=5.17,nucleos=14,max_passes=6,min_passes=2,delta_s=.05,
    material='ZYF300',er=2.94,tand=.0016,h=1.52,cu=.035,board=[220,64],sources=['IN_A','IN_B'],portas=ports,
    topology='Cada 1:3: Wilkinson1:2 desigual1/3+2/3, transformadores de50ohm, Wilkinson1:2 igual no ramo2/3; compensacao de fase no ramo1/3.',
    resistores=resistors,signals=signals,traces=curves,input=dict(Z=zin,L=lin,W=float(medium(zin).w*1000)),
    out_lengths=lengths,lambda50_mm=lambda50,juncao_corrigida=CORRIGIR,nota_fase='Bypass+OUT1 tem fase equivalente a DELAY+quarto de onda50ohm+OUT3 menos uma onda guiada. Saidas nominais em fase apenas no centro; sem sweep.',
    resistor_model='CH0402F nominal: RLC resistivo entre pads e corpo alumina9.8/tand0.0001 assumidos; parasitas internos e tolerancias nao caracterizados.',
    nominal_VSWR_ativo=((1+abs(s@np.ones(2)))/(1-abs(s@np.ones(2)))).tolist(),nominal_VSWR_casado=((1+abs(np.diag(s)))/(1-abs(np.diag(s)))).tolist(),
    nominal_saida_modulo=abs(n.s[0,1:,0]).tolist(),nominal_saida_fase=np.angle(n.s[0,1:,0],deg=True).tolist())
(ROOT/'configuracao.json').write_text(json.dumps(cfg,indent=2)+'\n')
shutil.copy2(REPO/'projetos/P2S13/continuacao_tres_placas2/HFSS_14nucleos.acf',ROOT/'HFSS_14nucleos.acf')
fig,ax=plt.subplots(figsize=(13,5));ax.add_patch(plt.Rectangle((-110,-32),220,64,color='#e3e8dd'))
for sh in polys:
    x,y=sh.exterior.xy;ax.fill(x,y,color='#bb7b28')
    for ring in sh.interiors:x,y=ring.xy;ax.fill(x,y,color='#e3e8dd')
for p in ports:ax.plot(p['x'],p['y'],'o',color='navy',ms=3);ax.annotate(p['name'],(p['x'],p['y']),xytext=(0,8),textcoords='offset points',ha='center',fontsize=8)
for r in resistors:ax.add_patch(plt.Rectangle((r['x']-.3,r['y']-.5),.6,1,color='#222'))
ax.set(xlim=(-114,114),ylim=(-35,35),xlabel='X (mm)',ylabel='Y (mm)',title='Divisor duplo 1:3 planar em cascata — 220 × 64 mm\nZYF300CA-C 1,52 mm | duas redes espelhadas | condutores físicos de35 µm')
ax.set_aspect('equal');fig.tight_layout();fig.savefig(ROOT/'layout.png',dpi=180);plt.close(fig)
print('LAYOUT_OK',cfg['input'],lengths,cfg['nominal_VSWR_ativo'],cfg['nominal_saida_fase'])
