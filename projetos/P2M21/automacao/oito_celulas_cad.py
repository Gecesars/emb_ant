"""Copia os solidos C12 sem remodelar o cobre; refletor comum e 16 coaxiais."""
from pathlib import Path
import json,hashlib
import FreeCAD as A,Part,Import
ROOT=Path('D:/dev/EMBRAER/P2M21/R14_Oito_Celulas')
cfg=json.loads((ROOT/'configuracao.json').read_text())
SRC=Path(cfg['fonte']);out=ROOT/'cad';out.mkdir(exist_ok=True)
assert hashlib.sha256((SRC/'4_elementos.FCStd').read_bytes()).hexdigest()==cfg['fontes_sha256']['4_elementos.FCStd']
source=A.openDocument(str(SRC/'4_elementos.FCStd'))
materials=json.loads((SRC/'cad/manifesto.json').read_text())
records=json.loads((SRC/'cad/folhas_solidas.json').read_text())
d=A.newDocument('P2M21_Oito_Celulas');man={};rec={};identity=[]
def add(name,sh,material):
    assert sh.isValid() and sh.Volume>0,name
    o=d.addObject('Part::Feature',name);o.Shape=sh
    o.addProperty('App::PropertyString','Material_nominal');o.Material_nominal=material
    man[name]=material;return o
for c in cfg['celulas']:
    group=d.addObject('App::DocumentObjectGroup',c['nome'])
    for n,mat in materials.items():
        if n=='Refletor_Al2mm':continue
        orig=source.getObject(n).Shape;sh=orig.copy();sh.translate(A.Vector(c['x'],c['y'],0))
        name=c['nome']+'_'+n;o=add(name,sh,mat);group.addObject(o)
        restored=sh.copy();restored.translate(A.Vector(-c['x'],-c['y'],0))
        dv=abs(sh.Volume-orig.Volume)
        assert dv<1e-7,(name,dv)
        # Translation-only copies preserve BREP topology, lengths and areas.
        assert len(sh.Faces)==len(orig.Faces) and abs(sh.Area-orig.Area)<1e-7
        identity.append(dict(nome=name,origem=n,delta_volume_mm3=dv,faces=len(sh.Faces)))
        if n in records:rec[name]={k:v for k,v in records[n].items() if not k.startswith('faces_')}
ref=Part.makeBox(776,162,2,A.Vector(-388,-81,-2))
for p in cfg['portas']:
    ref=ref.cut(Part.makeCylinder(2.1,2,A.Vector(p['x'],p['y'],-2)))
add('Refletor_Al2mm',ref,'AL5052')
d.recompute();native=ROOT/'P2M21_8celulas.FCStd';d.saveAs(str(native))
objs=[d.getObject(n) for n in man];bad=[];tested=0
for i,a in enumerate(objs):
    ba=a.Shape.BoundBox
    for b in objs[i+1:]:
        bb=b.Shape.BoundBox
        if any(min(getattr(ba,k+'Max'),getattr(bb,k+'Max'))-max(getattr(ba,k+'Min'),getattr(bb,k+'Min'))<=1e-6 for k in 'XYZ'):continue
        tested+=1;vol=a.Shape.common(b.Shape).Volume
        if vol>1e-7:bad.append(dict(a=a.Name,b=b.Name,volume_mm3=vol))
        if tested%100==0:print('PARES',tested,flush=True)
assert len(man)==329 and len(rec)==len(records)*8 and len(cfg['portas'])==16
report=dict(aprovado=not bad,objetos=len(man),pares=tested,intersecoes=bad,
    celulas=8,solidos_copiados=identity,folga_placas_lateral_mm=2,folga_placas_vertical_mm=8)
for n,v in [('manifesto',man),('folhas_solidas',rec),('portas',cfg['portas']),('intersecoes',report)]:
    (out/(n+'.json')).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
assert not bad,bad
for mat in sorted(set(man.values())):
    Import.export([d.getObject(n) for n,m in man.items() if m==mat],str(out/(mat+'.step')))
print('CAD',len(man),'SOLIDOS; PARES',tested,'SEM INTERSECOES',flush=True)
A.closeDocument(source.Name);A.closeDocument(d.Name)
re=A.openDocument(str(native));assert all(re.getObject(n).Shape.isValid() for n in man)
(out/'reabertura.json').write_text(json.dumps(dict(objetos=len(man),todos_validos=True,sha256=hashlib.sha256(native.read_bytes()).hexdigest()),indent=2)+'\n')
A.closeDocument(re.Name)
