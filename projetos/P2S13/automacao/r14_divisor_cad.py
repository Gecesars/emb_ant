"""FreeCADCmd: C07 fabricavel, PTH e cobre afastado da borda."""
from pathlib import Path
import os,json,hashlib
import FreeCAD as A,Part,Import
ROOT=Path(os.environ['P2S13_DIV3_ROOT']);cfg=json.loads((ROOT/'configuracao.json').read_text(encoding='utf-8'));OUT=ROOT/'cad';OUT.mkdir(exist_ok=True)
d=A.newDocument('Divisor_DFM');V=A.Vector;man={};rec={}
def add(n,s,m):
    s=s.removeSplitter();assert s.isValid() and len(s.Solids)==1 and s.Volume>0,n
    o=d.addObject('Part::Feature',n);o.Shape=s;o.addProperty('App::PropertyString','Material_nominal');o.Material_nominal=m;man[n]=m;return o
def face(points,z):return Part.Face(Part.makePolygon([V(x,y,z) for x,y in points]))
def cyl(r,z0,z1,x,y):return Part.makeCylinder(r,z1-z0,V(x,y,z0))
h=cfg['h'];cu=cfg['cu'];f=cfg['fabricacao'];rh=f['furo_acabado_mm']/2;rb=rh+f['metalizacao_mm'];rp=f['ilha_diametro_mm']/2;inset=f['recuo_terra_mm']
bx,by=cfg['board'];ox,oy=cfg['board_origin']
sub=Part.makeBox(bx,by,h,V(ox,oy,0));gnd=Part.makeBox(bx-2*inset,by-2*inset,cu,V(ox+inset,oy+inset,-cu));foils={}
for pol,data in cfg['signals'].items():
    sh=face(data['exterior'],h)
    for hole in data['holes']:sh=sh.cut(face(hole,h))
    foils['Sinal_'+pol]=sh.extrude(V(0,0,cu))
for p in cfg['portas']:
    n,x,y,ri,ro=[p[k] for k in ['name','x','y','ri','ro']]
    pol=n[-1];key='Sinal_'+pol
    # Finished hole and copper barrel are separate solids, without volume overlap.
    sub=sub.cut(cyl(rb,-.01,h+.01,x,y));gnd=gnd.cut(cyl(ro,-cu-.01,.01,x,y))
    foils[key]=foils[key].fuse(cyl(rp,h,h+cu,x,y)).cut(cyl(rh,h-.01,h+cu+.01,x,y)).removeSplitter()
    add('Pino_'+n,cyl(ri,-.18,h+cu,x,y),'copper')
    add('Barril_'+n,cyl(rb,0,h,x,y).cut(cyl(rh,0,h,x,y)),'copper')
    add('Solda_'+n,cyl(rh,-cu,h+cu,x,y).cut(cyl(ri,-cu,h+cu,x,y)),'SAC305')
    add('Ilha_inferior_'+n,cyl(rp,-cu,0,x,y).cut(cyl(rh,-cu,0,x,y)),'folha_cu')
    rec['Ilha_inferior_'+n]=dict(base_z_mm=0,skip_hole_cylinders=[dict(x=x,y=y,r=rh)])
    ptfe=cyl(ro,-.18,0,x,y).cut(cyl(ri,-.18,0,x,y)).cut(cyl(rp,-cu,0,x,y))
    add('PTFE_'+n,ptfe,'PTFE_terminal')
    add('Massa_'+n,cyl(ro+.5,-.18,-cu,x,y).cut(cyl(ro,-.18,-cu,x,y)),'copper')
add('Substrato',sub,'ZYF300');add('Terra',gnd,'folha_cu');rec['Terra']=dict(base_z_mm=0)
for n,sh in foils.items():
    add(n,sh,'folha_cu');rec[n]=dict(base_z_mm=h,skip_hole_cylinders=[dict(x=p['x'],y=p['y'],r=rh) for p in cfg['portas'] if p['name'].endswith(n[-1])])
d.recompute();objects=[d.getObject(n) for n in man];bad=[];pairs=0
for i,a in enumerate(objects):
    for b in objects[i+1:]:
        if any(min(getattr(a.Shape.BoundBox,k+'Max'),getattr(b.Shape.BoundBox,k+'Max'))-max(getattr(a.Shape.BoundBox,k+'Min'),getattr(b.Shape.BoundBox,k+'Min'))<=1e-6 for k in 'XYZ'):continue
        pairs+=1;vol=a.Shape.common(b.Shape).Volume
        if vol>1e-7:bad.append(dict(a=a.Name,b=b.Name,volume=vol))
assert not bad,bad
native=ROOT/'Divisor_Duplo3.FCStd';d.saveAs(str(native))
for mat in sorted(set(man.values())):Import.export([d.getObject(n) for n,m in man.items() if m==mat],str(OUT/(mat+'.step')))
for n,x in [('manifesto',man),('folhas_solidas',rec),('portas',cfg['portas']),('intersecoes',dict(aprovado=True,objetos=len(man),pares=pairs,intersecoes=bad))]:
    (OUT/(n+'.json')).write_text(json.dumps(x,indent=2)+'\n')
A.closeDocument(d.Name);d=A.openDocument(str(native));assert all(d.getObject(n).Shape.isValid() for n in man)
(OUT/'reabertura.json').write_text(json.dumps(dict(validos=True,objetos=len(man),sha256=hashlib.sha256(native.read_bytes()).hexdigest()),indent=2))
A.closeDocument(d.Name);print('DFM_CAD_OK',len(man))
