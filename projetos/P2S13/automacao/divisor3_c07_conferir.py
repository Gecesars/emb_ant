"""Auditoria independente KiCad/CAM vs CAD HFSS C07; nao executa RF.
Parser Gerber restrito: regioes positivas lineares e flashes circulares;
qualquer comando geometrico inesperado e rejeitado.
"""
from pathlib import Path
from collections import Counter
import json,hashlib,re,math,csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MP
from matplotlib.patches import PathPatch
from shapely.geometry import Point,Polygon,LineString
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely import make_valid,affinity

R=Path(__file__).resolve().parents[3];S=R/'projetos/P2S13/divisor_duplo_1x3_correcao/c07_centro'
O=R/'projetos/P2S13/kicad/divisor_duplo_1x3_C07';CAM=O/'gerbers';NAME='divisor_duplo_1x3_C07'
read=lambda p:json.loads(p.read_text(encoding='utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cfg=read(S/'configuracao.json');native=read(O/'leitura_kicad.json');cad=read(O/'conferencia_cad_hfss.json')
assert cad['aprovado'] and cad['fonte_config_sha256']==native['source_sha256']==sha(S/'configuracao.json')
assert native['native_sha256']==sha(O/(NAME+'.kicad_pcb'))
assert native['tracks']==0
disk=lambda xy,r:Point(xy).buffer(r,quad_segs=2048)
board=Polygon([[-110,-32],[110,-32],[110,32],[-110,32]])
drill_expected=unary_union([disk((p['x'],p['y']),p['ri']) for p in cfg['portas']])
expected={('F.Cu','SIG_'+n):Polygon(g['exterior'],g['holes']).difference(drill_expected) for n,g in cfg['signals'].items()}
expected[('B.Cu','GND')]=board.difference(unary_union([disk((p['x'],p['y']),p['ro']) for p in cfg['portas']]))
actual={key:[] for key in expected}
for d in native['drawings']:
    actual[d['layer'],d['net']].extend(Polygon(c).buffer(0) for c in d['contours'])
native_drills=[]
for p in native['pads']:
    if p['npth']:
        assert p['drill']==p['diameter']==.9195
        native_drills.append(disk(p['center'],p['drill']/2));continue
    assert p['drill']==0
    for layer in p['layers']:actual[layer,p['net']].append(disk(p['center'],p['diameter']/2))
assert len(native_drills)==8
nd=unary_union(native_drills)
actual={key:unary_union(parts).difference(nd) for key,parts in actual.items()}
comparisons=[]
for key,e in expected.items():
    a=actual[key];area=a.symmetric_difference(e).area;dist=a.hausdorff_distance(e)
    # Area de diferenca cresce com o perimetro; o limite fisico e o desvio de borda.
    assert area<2*e.length*.000004 and dist<.000004,(key,area,dist)
    assert a.geom_type=='Polygon' and a.is_valid,(key,a.geom_type)
    comparisons.append(dict(camada=key[0],rede=key[1],area_HFSS_mm2=e.area,area_KiCad_mm2=a.area,
        diferenca_area_mm2=area,Hausdorff_mm=dist,componentes_conectados=1))
assert actual['F.Cu','SIG_A'].distance(actual['F.Cu','SIG_B'])>.2
assert unary_union([LineString(s) for s in native['outline']]).equals(board.boundary)
for m in native['mask']:assert unary_union([Polygon(c) for c in m['contours']]).equals(board)

def gerber(p,function):
    raw=p.read_text();assert '%FSLAX46Y46*%' in raw and '%MOMM*%' in raw
    assert '%TF.FileFunction,'+function+'*%' in raw and '%LPC' not in raw and '%AM' not in raw
    apertures={int(n):float(v) for n,v in re.findall(r'%ADD(\d+)C,([.\d]+)\*%',raw)}
    parts=[];segments=[];region=None;ap=None;last=None
    for line in raw.splitlines():
        if line=='G36*':assert region is None;region=[]
        elif line=='G37*':
            assert len(region)>3 and region[0]==region[-1];parts.append(make_valid(Polygon(region)));region=None
        elif m:=re.fullmatch(r'D(\d+)\*',line):ap=int(m[1]);assert ap in apertures
        elif m:=re.fullmatch(r'X(-?\d+)Y(-?\d+)D0([123])\*',line):
            pt=(int(m[1])/1e6,int(m[2])/1e6);op=m[3]
            if op=='3':assert region is None;parts.append(disk(pt,apertures[ap]/2))
            elif region is not None:assert (op=='2')==(len(region)==0);region.append(pt)
            elif op=='1':assert last is not None;segments.append((last,pt))
            last=pt
        else:assert not line or line.startswith(('G04 ','%TF.','%TA.','%TO.','%TD','%ADD')) or line in ('%FSLAX46Y46*%','%MOMM*%','%LPD*%','G01*','M02*'),line
    assert region is None
    return unary_union(parts),segments

drill=(CAM/(NAME+'-NPTH.drl')).read_text()
assert 'FORMAT={3:6/' in drill and 'METRIC' in drill and 'TF.FileFunction,NonPlated,1,2,NPTH' in drill
tools={int(n):float(d) for n,d in re.findall(r'^T(\d+)C([.\d]+)$',drill,re.M)};holes=[];current=None
for line in drill.splitlines():
    if m:=re.fullmatch(r'T(\d+)',line):current=tools[int(m[1])]
    elif m:=re.fullmatch(r'X(-?\d+)Y(-?\d+)',line):holes.append((int(m[1])/1e6,int(m[2])/1e6,current))
    else:assert line.startswith((';','T')) or line in ('M48','FMAT,2','METRIC','%','G90','G05','M30'),line
assert len(holes)==8 and {p[2] for p in holes}=={.9195}
pth=(CAM/(NAME+'-PTH.drl')).read_text();assert 'TF.FileFunction,Plated' in pth and not re.search(r'^X',pth,re.M)
errors=[]
for p in cfg['portas']:
    want=(120+p['x'],p['y']-42)
    nearest=min(holes,key=lambda q:math.dist(q[:2],want));err=math.dist(nearest[:2],want)
    assert err<.000001,(want,nearest,err)
    errors.append(err)
cam_drills=unary_union([disk(p[:2],p[2]/2) for p in holes])
to_cam=lambda s:affinity.translate(s,xoff=120,yoff=-42)
cam_board=to_cam(board);cam_shapes={};cam_results=[]
for face,suffix,func in [('F','gtl','Copper,L1,Top'),('B','gbl','Copper,L2,Bot')]:
    a,segs=gerber(CAM/(NAME+'-'+face+'_Cu.'+suffix),func);assert not segs
    a=a.difference(cam_drills);e=to_cam(unary_union([v for key,v in expected.items() if key[0]==face+'.Cu']))
    diff=a.symmetric_difference(e).area;dist=a.hausdorff_distance(e)
    assert diff<2*e.length*.000005 and dist<.000005,(face,diff,dist)
    cam_shapes[face]=a;cam_results.append(dict(camada=face+'.Cu',diferenca_area_mm2=diff,Hausdorff_mm=dist))
for face,suffix in [('F','gts'),('B','gbs')]:
    p=CAM/(NAME+'-'+face+'_Mask.'+suffix)
    a,segs=gerber(p,'Soldermask,'+('Top' if face=='F' else 'Bot'));assert a.equals(cam_board) and not segs
    assert '%TF.FilePolarity,Negative*%' in p.read_text()
_,segs=gerber(CAM/(NAME+'-Edge_Cuts.gm1'),'Profile,NP')
assert len(segs)==4 and unary_union([LineString(s) for s in segs]).equals(cam_board.boundary)
drc=read(O/'drc.json');counts=Counter((v['severity'],v['type']) for v in drc['violations'])
assert not drc['unconnected_items']
assert counts==Counter({('error','hole_clearance'):8,('error','copper_edge_clearance'):1,('warning','solder_mask_bridge'):25}),counts
result=dict(conversao_geometrica_aprovada=True,liberado_fabricacao_padrao_JLC=False,novo_solve=False,
    comparacao_KiCad=comparisons,comparacao_Gerber=cam_results,contorno_mm=[220,64],
    furos_NPTH=8,furos_PTH=0,diametro_NPTH_mm=.9195,antipad_BCu_mm=3.03,
    erro_max_XY_furacao_mm=max(errors),mascara_aberta_ambas_faces=True,serigrafia=False,
    DRC_erros=9,DRC_avisos=25,DRC_desconectados=0,DRC_itens=[dict(severidade=k[0],tipo=k[1],quantidade=v) for k,v in counts.items()],
    folga_cobre_borda_B_mm=0,folga_cobre_NPTH_F_mm=0,
    anel_top_min_nominal_mm=.65*math.cos(math.pi/48)-.45975,
    nota='Nove violacoes sao preservadas, sem exclusoes DRC: C07 possui cobre ate borda e ate furos NPTH. Exigem analise especial JLC; nao aprovar reducao de cobre ou metalizacao automatica.',
    resolucao_digital='KiCad e CAM XY 1 nm; antipads de 2048 vertices (sagita 1,783 nm), limites 4/5 nm incluindo quantizacao XY; nao tolerancia fabril.',
    hashes_CAM={p.name:sha(p) for p in sorted(CAM.iterdir()) if p.is_file()})
(O/'verificacao.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
with (O/'conexoes.csv').open('w',encoding='utf8',newline='') as f:
    w=csv.writer(f);w.writerow(['Referencia','Porta','HFSS_X_mm','HFSS_Y_mm','KiCad_X_mm','KiCad_Y_mm','Furo_NPTH_mm','Antipad_BCu_mm'])
    for i,p in enumerate(cfg['portas'],1):w.writerow(['J'+str(i),p['name'],p['x'],p['y'],120+p['x'],42-p['y'],2*p['ri'],2*p['ro']])
def draw(ax,s,color,alpha=1):
    if s.is_empty:return
    if s.geom_type!='Polygon':
        for sub in s.geoms:
            if sub.geom_type in ('Polygon','MultiPolygon'):draw(ax,sub,color,alpha)
        return
    s=orient(s,1);verts=[];codes=[]
    for ring in [s.exterior,*s.interiors]:
        xy=list(ring.coords);verts.extend(xy);codes.extend([MP.MOVETO]+[MP.LINETO]*(len(xy)-2)+[MP.CLOSEPOLY])
    ax.add_patch(PathPatch(MP(verts,codes),facecolor=color,edgecolor='none',alpha=alpha))
(O/'preview').mkdir(exist_ok=True)
fig,axs=plt.subplots(3,1,figsize=(13,11))
for i,ax in enumerate(axs):
    draw(ax,cam_board,'#eceddf')
    if i!=0:draw(ax,cam_shapes['B'],'#357fb4',.5 if i==2 else 1)
    if i!=1:draw(ax,cam_shapes['F'],'#b87824')
    draw(ax,cam_drills,'white')
    ax.plot(*cam_board.exterior.xy,color='#444444',lw=.6)
    ax.set_aspect('equal');ax.set_xlim(5,235);ax.set_ylim(-78,-6);ax.set_title(['F.Cu + NPTH','B.Cu + antipads','Sobreposicao das faces e furos'][i])
    ax.set_xlabel('X CAM (mm)');ax.set_ylabel('Y CAM (mm)')
    for p in cfg['portas']:ax.annotate(p['name'],(120+p['x'],p['y']-42),xytext=(0,8 if p['y']>0 else -13),textcoords='offset points',ha='center',fontsize=8)
fig.suptitle('C07 — Gerbers e Excellon conferidos contra HFSS\n220 x 64 mm | ZYF300CA-C 1,52 mm | Cu 35 um | oito NPTH de 0,9195 mm',fontsize=13)
fig.tight_layout(rect=(0,.045,1,.94));fig.text(.5,.018,'PRELIMINAR: cobre ate furos NPTH e borda requer DFM especial. Sem mascara e sem serigrafia.',ha='center',fontsize=10)
fig.savefig(O/'preview/gerbers_conferidos.png',dpi=160);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(10,5))
for ax,p in zip(axs,[cfg['portas'][0],cfg['portas'][1]]):
    cx,cy=120+p['x'],p['y']-42
    draw(ax,cam_shapes['B'],'#357fb4',.5);draw(ax,cam_shapes['F'],'#b87824');draw(ax,cam_drills,'white')
    ax.set_xlim(cx-3.5,cx+3.5);ax.set_ylim(cy-3.5,cy+3.5);ax.set_aspect('equal');ax.grid(alpha=.3)
    ax.set_title(p['name']+' — vista comum pelo topo');ax.set_xlabel('X CAM (mm)');ax.set_ylabel('Y CAM (mm)')
fig.suptitle('Interfaces coaxiais preservadas — furo 0,9195 mm / antipad 3,03 mm')
fig.tight_layout();fig.savefig(O/'preview/detalhe_coaxiais.png',dpi=180);plt.close(fig)
print(json.dumps({k:result[k] for k in ['conversao_geometrica_aprovada','comparacao_KiCad','comparacao_Gerber','DRC_erros','DRC_avisos','DRC_desconectados','erro_max_XY_furacao_mm']},indent=2))
