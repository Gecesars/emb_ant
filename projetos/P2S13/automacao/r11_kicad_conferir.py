"""Conferencia geometrica independente KiCad/Gerber/Excellon C08 versus config CAD."""
from pathlib import Path
import json,os,math,re,ast,csv,hashlib,collections
from shapely.geometry import Point,Polygon,LineString
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely import make_valid,affinity
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MP
from matplotlib.patches import PathPatch
S=Path(os.environ['P2S13_DIV3_ROOT']);O=S/'kicad';CAM=O/'gerbers';NAME='divisor_duplo_1x3_C08'
read=lambda p:json.loads(p.read_text(encoding='utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cfg=read(S/'configuracao.json');native=read(O/'leitura_kicad.json');f=cfg['fabricacao']
assert native['source_sha256']==sha(S/'configuracao.json') and native['native_sha256']==sha(O/(NAME+'.kicad_pcb'))
disk=lambda xy,r:Point(xy).buffer(r,quad_segs=2048)
# Reuse only the audited restricted Gerber parser and polygon renderer, not legacy approval logic.
source=Path(__file__).with_name('divisor3_c07_conferir.py');tree=ast.parse(source.read_text(encoding='utf-8-sig'))
for node in tree.body:
    if isinstance(node,ast.FunctionDef) and node.name in ['gerber','draw']:exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'))
board=Polygon([[-110,-32],[110,-32],[110,32],[-110,32]])
drills=unary_union([disk((p['x'],p['y']),f['furo_acabado_mm']/2) for p in cfg['portas']])
expected={}
for pol,data in cfg['signals'].items():
    pads=unary_union([disk((p['x'],p['y']),f['ilha_diametro_mm']/2) for p in cfg['portas'] if p['name'].endswith(pol)])
    expected['F.Cu','SIG_'+pol]=Polygon(data['exterior'],data['holes']).union(pads).difference(drills)
    expected['B.Cu','SIG_'+pol]=pads.difference(drills)
expected['B.Cu','GND']=board.buffer(-f['recuo_terra_mm'],join_style=2).difference(unary_union([disk((p['x'],p['y']),p['ro']) for p in cfg['portas']]))
actual={key:[] for key in expected}
for row in native['drawings']:actual[row['layer'],row['net']].extend(Polygon(c).buffer(0) for c in row['contours'])
nd=[]
for p in native['pads']:
    if p['drill']:
        assert not p['npth'] and p['drill']==1.1 and p['diameter']==1.8 and set(p['layers'])=={'F.Cu','B.Cu'}
        nd.append(disk(p['center'],p['drill']/2))
    for layer in p['layers']:actual[layer,p['net']].append(disk(p['center'],p['diameter']/2))
assert len(nd)==8;nd=unary_union(nd);actual={key:unary_union(v).difference(nd) for key,v in actual.items()}
checks=[]
for key,e in expected.items():
    a=actual[key];diff=a.symmetric_difference(e).area
    assert diff<2*e.length*.000005 and a.buffer(.000005).covers(e) and e.buffer(.000005).covers(a),(key,diff)
    checks.append(dict(camada=key[0],rede=key[1],diferenca_area_mm2=diff,limite_desvio_borda_mm=.000005,area_mm2=a.area))
faces=read(O/'faces_cad.json');assert faces['fonte_config_sha256']==sha(S/'configuracao.json') and faces['fonte_fcstd_sha256']==sha(S/'Divisor_Duplo3.FCStd')
cad_checks=[]
for key,a in actual.items():
    group=[f for f in faces['faces'] if (f['camada'],f['rede'])==key]
    e=unary_union([Polygon(f['exterior'],f['furos']) for f in group]);diff=a.symmetric_difference(e).area
    assert a.buffer(.000005).covers(e) and e.buffer(.000005).covers(a),(key,'CAD faces',diff)
    cad_checks.append(dict(camada=key[0],rede=key[1],diferenca_area_mm2=diff,area_CAD_exata_mm2=sum(f['area_CAD_mm2'] for f in group),limite_desvio_borda_mm=.000005))
(O/'conferencia_cad_hfss.json').write_text(json.dumps(dict(aprovado=True,comparacoes=cad_checks,fonte_fcstd_sha256=faces['fonte_fcstd_sha256'],fonte_config_sha256=faces['fonte_config_sha256']),indent=2))
assert unary_union([LineString(s) for s in native['outline']]).equals(board.boundary)
raw=(CAM/(NAME+'-PTH.drl')).read_text();assert 'FORMAT={3:6/' in raw and 'TF.FileFunction,Plated' in raw
tools={int(n):float(d) for n,d in re.findall(r'^T(\d+)C([.\d]+)$',raw,re.M)};holes=[];tool=None
for line in raw.splitlines():
    if m:=re.fullmatch(r'T(\d+)',line):tool=tools[int(m[1])]
    elif m:=re.fullmatch(r'X(-?\d+)Y(-?\d+)',line):holes.append((int(m[1])/1e6,int(m[2])/1e6,tool))
assert len(holes)==8 and {p[2] for p in holes}=={1.1}
assert not re.search(r'^X', (CAM/(NAME+'-NPTH.drl')).read_text(),re.M)
xyerrors=[min(math.dist(q[:2],(120+p['x'],p['y']-42)) for q in holes) for p in cfg['portas']];assert max(xyerrors)<1e-6
to_cam=lambda x:affinity.translate(x,xoff=120,yoff=-42)
cam_drills=unary_union([disk(p[:2],p[2]/2) for p in holes]);cam_shapes={};cam_checks=[]
for side,suffix,fn in [('F','gtl','Copper,L1,Top'),('B','gbl','Copper,L2,Bot')]:
    a,segs=gerber(CAM/(NAME+'-'+side+'_Cu.'+suffix),fn);assert not segs
    a=a.difference(cam_drills);e=to_cam(unary_union([v for k,v in expected.items() if k[0]==side+'.Cu']))
    diff=a.symmetric_difference(e).area;assert diff<2*e.length*.000005 and a.buffer(.000005).covers(e) and e.buffer(.000005).covers(a),(side,diff)
    cam_shapes[side]=a;cam_checks.append(dict(camada=side+'.Cu',diferenca_area_mm2=diff,limite_desvio_borda_mm=.000005))
for side,suffix in [('F','gts'),('B','gbs')]:
    p=CAM/(NAME+'-'+side+'_Mask.'+suffix);a,segs=gerber(p,'Soldermask,'+('Top' if side=='F' else 'Bot'))
    assert a.equals(to_cam(board)) and not segs and '%TF.FilePolarity,Negative*%' in p.read_text()
_,segs=gerber(CAM/(NAME+'-Edge_Cuts.gm1'),'Profile,NP');assert unary_union([LineString(s) for s in segs]).equals(to_cam(board).boundary)
drc=read(O/'drc.json');assert not drc['unconnected_items'] and not [v for v in drc['violations'] if v['severity']=='error']
counts=collections.Counter((v['severity'],v['type']) for v in drc['violations']);assert all(k==('warning','solder_mask_bridge') for k in counts)
r=dict(geometria_KiCad_CAM_aprovada=True,DRC_erros=0,DRC_desconectados=0,DRC_avisos=sum(counts.values()),
       avisos='Mascara totalmente aberta por projeto; sem exclusoes DRC',PTH=8,NPTH=0,furo_mm=1.1,ilha_mm=1.8,anel_mm=.35,
       recuo_terra_mm=.3,comparacoes_KiCad=checks,comparacoes_CAD=cad_checks,comparacoes_CAM=cam_checks,max_erro_XY_furacao_mm=max(xyerrors),
       hashes_CAM={p.name:sha(p) for p in CAM.iterdir() if p.is_file()},validacao_RF_separada=True,
       fonte_config_sha256=sha(S/'configuracao.json'),fonte_parser_sha256=sha(source))
(O/'verificacao.json').write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
(O/'preview').mkdir(exist_ok=True);fig,axs=plt.subplots(3,1,figsize=(13,11));cam_board=to_cam(board)
for i,ax in enumerate(axs):
    draw(ax,cam_board,'#eeeede')
    if i!=0:draw(ax,cam_shapes['B'],'#357fb4',.5 if i==2 else 1)
    if i!=1:draw(ax,cam_shapes['F'],'#b87824')
    draw(ax,cam_drills,'white');ax.plot(*cam_board.exterior.xy,color='#444',lw=.6);ax.set_aspect('equal');ax.set_xlim(5,235);ax.set_ylim(-78,-6)
    ax.set_title(['F.Cu + PTH','B.Cu: terra recuado e ilhas isoladas','Sobreposicao das faces'][i]);ax.set_xlabel('X CAM (mm)');ax.set_ylabel('Y CAM (mm)')
    for p in cfg['portas']:ax.annotate(p['name'],(120+p['x'],p['y']-42),xytext=(0,8 if p['y']>0 else -13),textcoords='offset points',ha='center',fontsize=8)
fig.suptitle('C08 DFM — cobre e furacao conferidos\n220 × 64 mm | ZYF300CA-C 1,52 mm | Cu 35 µm | ENIG | oito PTH Ø1,10 mm')
fig.tight_layout(rect=(0,.04,1,.94));fig.text(.5,.018,'DRC: zero erros e zero desconectados. Faces sem mascara; desempenho RF depende da analise R11.',ha='center');fig.savefig(O/'preview/gerbers_conferidos.png',dpi=160);plt.close(fig)
print(json.dumps(r,indent=2))
