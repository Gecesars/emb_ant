"""CAD solido do divisor; executado em FreeCADCmd separado da GUI."""
from pathlib import Path
import json,hashlib,os
import FreeCAD as A,Part,Import
ROOT=Path(os.environ.get('P2S13_DIV3_ROOT','D:/dev/EMBRAER/P2S13/R08_Divisor_HFSS'));cfg=json.loads((ROOT/'configuracao.json').read_text());OUT=ROOT/'cad';OUT.mkdir(exist_ok=True)
d=A.newDocument('P2S13_Divisor_Duplo3');V=A.Vector;man={};rec={}
def add(name,sh,mat):
    assert sh.isValid() and len(sh.Solids)==1 and sh.Volume>0,name
    o=d.addObject('Part::Feature',name);o.Shape=sh;o.addProperty('App::PropertyString','Material_nominal');o.Material_nominal=mat;man[name]=mat;return o
def face(points,z):return Part.Face(Part.makePolygon([V(x,y,z) for x,y in points]))
h=cfg['h'];cu=cfg['cu'];sub=Part.makeBox(220,64,h,V(-110,-32,0));gnd=Part.makeBox(220,64,cu,V(-110,-32,-cu))
foils={}
for pol,data in cfg['signals'].items():
    f=face(data['exterior'],h)
    for hole in data['holes']:f=f.cut(face(hole,h))
    foils['Sinal_'+pol]=f.extrude(V(0,0,cu)).removeSplitter()
for p in cfg['portas']:
    name,x,y,ri,ro=[p[k] for k in ['name','x','y','ri','ro']]
    drill=Part.makeCylinder(ri,h+cu+.1,V(x,y,-.02))
    sub=sub.cut(drill);gnd=gnd.cut(Part.makeCylinder(ro,cu+.1,V(x,y,-cu-.02)))
    for n,sh in foils.items():foils[n]=sh.cut(drill).removeSplitter()
    add('Pino_'+name,Part.makeCylinder(ri,h+cu+.18,V(x,y,-.18)),'copper')
    add('Solda_'+name,Part.makeCylinder(.65,.07,V(x,y,h+cu)),'SAC305')
    add('PTFE_'+name,Part.makeCylinder(ro,.18,V(x,y,-.18)).cut(Part.makeCylinder(ri,.18,V(x,y,-.18))),'PTFE_terminal')
    add('Massa_'+name,Part.makeCylinder(ro+.5,.18-cu,V(x,y,-.18)).cut(Part.makeCylinder(ro,.18-cu,V(x,y,-.18))),'copper')
add('Substrato',sub.removeSplitter(),'ZYF300');add('Terra',gnd.removeSplitter(),'folha_cu');rec['Terra']={'base_z_mm':0.}
for n,sh in foils.items():add(n,sh,'folha_cu');rec[n]={'base_z_mm':h}
for r in cfg['resistores']:
    add('Corpo_'+r['name'],Part.makeBox(r['body_w'],r['body_l'],r['body_h'],V(r['x']-r['body_w']/2,r['y']-r['body_l']/2,h+cu)),'Alumina_nominal')
d.recompute();native=ROOT/'Divisor_Duplo3.FCStd';d.saveAs(str(native))
objects=[d.getObject(n) for n in man];bad=[];pairs=0
for i,a in enumerate(objects):
    for b in objects[i+1:]:
        if any(min(getattr(a.Shape.BoundBox,k+'Max'),getattr(b.Shape.BoundBox,k+'Max'))-max(getattr(a.Shape.BoundBox,k+'Min'),getattr(b.Shape.BoundBox,k+'Min'))<=1e-6 for k in 'XYZ'):continue
        pairs+=1;vol=a.Shape.common(b.Shape).Volume
        if vol>1e-7:bad.append(dict(a=a.Name,b=b.Name,volume=vol))
assert not bad,bad
for mat in sorted(set(man.values())):Import.export([d.getObject(n) for n,m in man.items() if m==mat],str(OUT/(mat+'.step')))
for name,data in [('manifesto',man),('folhas_solidas',rec),('portas',cfg['portas']),('intersecoes',dict(aprovado=True,objetos=len(man),pares=pairs,intersecoes=bad))]:
    (OUT/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
A.closeDocument(d.Name);d=A.openDocument(str(native));assert len([o for o in d.Objects if hasattr(o,'Shape')])==len(man)
assert all(d.getObject(n).Shape.isValid() for n in man)
(OUT/'reabertura.json').write_text(json.dumps(dict(objetos=len(man),validos=True,sha256=hashlib.sha256(native.read_bytes()).hexdigest()),indent=2))
A.closeDocument(d.Name);print('CAD_OK',len(man),pairs)
