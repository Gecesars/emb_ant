"""Divisor compacto: duas redes 1:3, tres ramais fisica/eletricamente identicos."""
from pathlib import Path
import json,sys,math,shutil
import numpy as np
from shapely.geometry import LineString,Point,Polygon,box
from shapely.ops import unary_union
import skrf as rf
from skrf.circuit import Circuit
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).parent;sys.path.insert(0,str(HERE))
from divisor_duplo3_planejar import medium,F
ROOT=Path('D:/dev/EMBRAER/P2S13/R14_Compacto_Simetrico_SemRadome/c00')
REF=Path('D:/dev/EMBRAER/P2S13/R12_Curvilinear_Simplificado');OLD=Path('D:/dev/EMBRAER/P2S13/R11_Fabricavel_Radome/d00')
assert not (ROOT/'P2S13_Compacto_SemRadome.aedt').exists() and not (ROOT/'P2S13_Compacto_SemRadome.FCStd').exists(),'Preservar CAD e resultados'
ROOT.mkdir(parents=True,exist_ok=True);DIV=ROOT/'divisor';DIV.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
z1=(150**3*50)**.25;z2=(150*50**3)**.25
m1,m2=medium(z1),medium(z2);l1=float(np.pi/(2*m1.beta[0])*1000);l2=float(np.pi/(2*m2.beta[0])*1000)
w1,w2=float(m1.w*1000),float(m2.w*1000);R=l1+l2;C=2.50916841304;Y=19.1
board=[36.,78.];origin=[C+R/4-board[0]/2,-board[1]/2]
traces=[];signals={};ports=[];poly=[]
for pol,sgn in [('A',1),('B',-1)]:
    # Pad real circular de raio .9mm sera unido pelo CAD; esboco interno evita
    # coincidencias degeneradas entre poligono aproximado e circulo analitico.
    center=np.array([C,sgn*Y]);parts=[Point(*center).buffer(.65,quad_segs=24)]
    ports.append(dict(name='IN_'+pol,x=C,y=sgn*Y,z=-.18,ri=.45975,ro=1.515))
    for cell,deg in [('R1',120),('R2',240),('R3',0)]:
        u=np.array([np.cos(np.deg2rad(deg)),sgn*np.sin(np.deg2rad(deg))]);p1=center+l1*u;p2=center+R*u
        normal=np.array([-u[1],u[0]])
        contour=[(0,-w1/2),(l1,-w1/2),(l1,-w2/2),(R,-w2/2),(R,w2/2),(l1,w2/2),(l1,w1/2),(0,w1/2)]
        parts.append(Polygon([center+x*u+y*normal for x,y in contour]))
        for sec,a,b,z,w,l in [('T1',center,p1,z1,w1,l1),('T2',p1,p2,z2,w2,l2)]:
            traces.append(dict(name=pol+'_'+cell+'_'+sec,points=[a.tolist(),b.tolist()],Z_ohm=z,width_mm=w,length_mm=l,phase_nominal_graus=90.))
        parts.append(Point(*p2).buffer(.65,quad_segs=24))
        ports.append(dict(name=cell+'_'+pol,x=float(p2[0]),y=float(p2[1]),z=-.18,ri=.45975,ro=1.515))
    raw=unary_union(parts);assert raw.is_valid and raw.geom_type=='Polygon'
    sh=Polygon([(round(x,8),round(y,8)) for x,y in raw.exterior.coords],
      [[(round(x,8),round(y,8)) for x,y in hole.coords] for hole in raw.interiors]).simplify(1e-7,preserve_topology=True)
    assert sh.is_valid and sh.geom_type=='Polygon' and raw.hausdorff_distance(sh)<2e-7
    assert box(*origin,origin[0]+board[0],origin[1]+board[1]).contains(sh)
    poly.append(sh);signals[pol]=dict(exterior=list(sh.exterior.coords),holes=[list(h.coords) for h in sh.interiors])
assert poly[0].distance(poly[1])>.2
# Conferencia do circuito distribuido nominal, sem afirmar resultado EM.
nodes=[[(Circuit.Port(F,'IN'),0)]];qs=[]
for i in range(3):
    a=m1.line(l1/1000,unit='m',name='Q1_%d'%i);b=m2.line(l2/1000,unit='m',name='Q2_%d'%i);qs.append((a,b))
    nodes[0].append((a,0));nodes.extend([[(a,1),(b,0)],[(b,1),(Circuit.Port(F,'O%d'%i),0)]])
net=Circuit(nodes).network;s=net.s[0];np.testing.assert_allclose(s[1:,0],s[1,0],atol=1e-12)
dc=read(OLD/'configuracao.json')
dc={k:v for k,v in dc.items() if not k.startswith(('nominal_','fonte_')) and k not in ['out_lengths','lambda50_mm','parametros']}
dc.update(revisao='C09_Compacto_2Secoes_c00',board=board,board_origin=origin,signals=signals,portas=ports,traces=traces,
  topology='Duas trifurcacoes sem resistores; tres ramais radiais identicos de duas secoes lambda/4; ligacao soldada por seis cabos iguais.',
  precisao_poligonos_mm=1e-8,limite_simplificacao_numerica_mm=2e-7,
  parametros=dict(Z1_ohm=z1,Z2_ohm=z2,L1_mm=l1,L2_mm=l2,W1_mm=w1,W2_mm=w2,comprimento_por_ramal_mm=R,distancia_centros_AB_mm=2*Y),
  max_passes=6,min_passes=2,delta_s=.05,nucleos=14,basis_order=1,percent_refinement=60)
write(DIV/'configuracao.json',dc)
write(DIV/'igualdade_ramais.json',dict(aprovado_geometria_nominal=True,ramais=6,comprimento_fisico_mm=[R]*6,secoes_mm=[l1,l2],larguras_mm=[w1,w2],
  fase_eletrica_nominal_graus=[180.]*6,observacao='Mesma sequencia de materiais, larguras e comprimentos. Fase real carregada sera medida no HFSS; nao e compensacao por multiplos de onda.',
  modelo_distribuido_VSWR_entrada=float((1+abs(s[0,0]))/(1-abs(s[0,0]))),))
fig,ax=plt.subplots(figsize=(6,9));ax.add_patch(plt.Rectangle(origin,*board,facecolor='#e4eadc',edgecolor='black'))
for sh in poly:ax.fill(*sh.exterior.xy,color='#b57a2d')
for p in ports:
    ax.plot(p['x'],p['y'],'o',color='navy',ms=3);ax.annotate(p['name'],(p['x'],p['y']),xytext=(3,4),textcoords='offset points',fontsize=8)
ax.set(xlabel='X (mm)',ylabel='Y (mm)',title='C09 — divisor duplo 1:3 compacto\n36 × 78 mm | duas seções iguais por ramal');ax.set_aspect('equal');ax.margins(.1);fig.tight_layout();fig.savefig(DIV/'layout.png',dpi=160);plt.close(fig)
c=read(REF/'configuracao.json');c.update(revisao='R14_c00',native='P2S13_Compacto_SemRadome.aedt',cad_native='P2S13_Compacto_SemRadome.FCStd',design='Compacto_SemRadome',
 fonte_CAD_preservado=str(REF),fonte_divisor=str(DIV),max_passes=6,min_passes=2,max_delta_s=.05,percent_refinement=60,nucleos=14,sweep=False,gui=False,
 radome_presente=False,escopo='Tres PCBs de dois elementos, refletor e divisor compacto de duas secoes. Seis cabos fisicos iguais soldados. Sem radome.',
 estudo='Ramais da PCB de igual comprimento fisico e eletrico nominal, sem compensacao por ondas inteiras. Cabos iguais; medir ganhos/VSWR/H/V.',
 alteracoes_autorizadas='12nov: substituir divisor por compacto simetrico de duas secoes; cabos soldados; retirar radome. H(0) ate0.5dB abaixo do pico.',
 portas=[dict(p,x=p['x'],y=-p['y'],z=c['divisor_translacao_z_mm']+.18) for p in ports if p['name'].startswith('IN_')],
 solver_type='Direct Solver',curvilinear=True,campos_volumetricos_locais=True)
c['metas']['depressao_frontal_H_max_dB']=.5
write(ROOT/'configuracao.json',c);shutil.copy2(REF/'HFSS_14nucleos.acf',ROOT/'HFSS_14nucleos.acf')
write(ROOT/'estado.json',dict(estado='PREPARAR_CABOS_E_CAD',nenhum_solver_iniciado=True))
print(json.dumps(dict(root=str(ROOT),board=board,dimensoes=dc['parametros']),indent=2))
