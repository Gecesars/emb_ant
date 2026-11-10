"""Duas celulas C12 preservadas e refletor com dobras laterais curvas reais."""
from pathlib import Path
import json,math,hashlib,os
import FreeCAD as A,Part,Import
ROOT=Path(os.environ['P2S13_ROOT']);cfg=json.loads((ROOT/'configuracao.json').read_text())
out=ROOT/'cad';out.mkdir(exist_ok=True)
SRC=Path(cfg['fonte']);source=A.openDocument(str(SRC/'4_elementos.FCStd'))
assert hashlib.sha256((SRC/'4_elementos.FCStd').read_bytes()).hexdigest()==cfg['fontes_sha256']['4_elementos.FCStd']
materials=json.loads((SRC/'cad/manifesto.json').read_text());records=json.loads((SRC/'cad/folhas_solidas.json').read_text())
d=A.newDocument('P2S13_'+cfg['revisao']);man={};rec={};ident=[]
def add(n,sh,mat):
    assert sh.isValid() and sh.Volume>0,n
    o=d.addObject('Part::Feature',n);o.Shape=sh;o.addProperty('App::PropertyString','Material_nominal');o.Material_nominal=mat;man[n]=mat;return o
for c in cfg['celulas']:
    group=d.addObject('App::DocumentObjectGroup',c['nome'])
    for n,mat in materials.items():
        if n=='Refletor_Al2mm':continue
        orig=source.getObject(n).Shape;sh=orig.copy();sh.translate(A.Vector(c['x'],0,0))
        name=c['nome']+'_'+n;group.addObject(add(name,sh,mat))
        assert abs(sh.Volume-orig.Volume)<1e-7 and abs(sh.Area-orig.Area)<1e-7 and len(sh.Faces)==len(orig.Faces)
        ident.append(dict(nome=name,origem=n,delta_volume_mm3=abs(sh.Volume-orig.Volume)))
        if n in records:rec[name]={k:v for k,v in records[n].items() if not k.startswith('faces_')}
b=cfg['inicio_dobra_y_mm'];alpha=math.radians(cfg['angulo_dobra_graus']);t=cfg['espessura_mm'];ri=cfg['raio_interno_mm'];ro=ri+t;L=cfg['refletor_comprimento_mm'];W=cfg['refletor_desenvolvido_largura_mm']
tail=W/2-b-alpha*(ri+cfg['K_dobra']*t)
assert tail>=0
V=lambda y,z:A.Vector(-L/2,y,z)
if alpha==0:ref=Part.makeBox(L,W,t,V(-W/2,-t))
else:
    O=lambda a:V(b+ro*math.sin(a),-ro+ro*math.cos(a))
    I=lambda a:V(b+ri*math.sin(a),-ro+ri*math.cos(a))
    p0,p1=O(0),O(alpha);q0,q1=I(0),I(alpha)
    ext=A.Vector(0,tail*math.cos(alpha),-tail*math.sin(alpha));p2=p1+ext;q2=q1+ext
    edges=[Part.makeLine(V(0,0),p0),Part.Arc(p0,O(alpha/2),p1).toShape(),Part.makeLine(p1,p2),Part.makeLine(p2,q2),Part.makeLine(q2,q1),Part.Arc(q1,I(alpha/2),q0).toShape(),Part.makeLine(q0,V(0,-t)),Part.makeLine(V(0,-t),V(0,0))]
    right=Part.Face(Part.Wire(edges)).extrude(A.Vector(L,0,0));left=right.copy();left.rotate(A.Vector(0,0,-t/2),A.Vector(0,0,1),180)
    # Rotacao acima inverte X tambem; comprimento e centrado e permanece identico.
    ref=right.fuse(left).removeSplitter()
for p in cfg['portas']:
    ref=ref.cut(Part.makeCylinder(2.1,120,A.Vector(p['x'],p['y'],-100)))
o=add('Refletor_Al2mm',ref,'AL5052')
for name,value in [('Inicio_dobra_Y',b),('Raio_interno',ri),('Comprimento',L),('Largura_desenvolvida',W)]:o.addProperty('App::PropertyLength',name);setattr(o,name,value)
o.addProperty('App::PropertyAngle','Angulo_para_tras');o.Angulo_para_tras=cfg['angulo_dobra_graus']
o.addProperty('App::PropertyString','Recalcular');o.Recalcular='Parametros documentais; reconstruir pelo script criar_cad.py e configuracao.json para alterar o BREP.'
d.recompute();native=ROOT/cfg['cad_native'];d.saveAs(str(native))
objs=[d.getObject(n) for n in man];bad=[];tested=0
for i,a in enumerate(objs):
    ba=a.Shape.BoundBox
    for bbobj in objs[i+1:]:
        bb=bbobj.Shape.BoundBox
        if any(min(getattr(ba,k+'Max'),getattr(bb,k+'Max'))-max(getattr(ba,k+'Min'),getattr(bb,k+'Min'))<=1e-6 for k in 'XYZ'):continue
        tested+=1;v=a.Shape.common(bbobj.Shape).Volume
        if v>1e-7:bad.append(dict(a=a.Name,b=bbobj.Name,volume_mm3=v))
assert len(man)==41*2+1 and len(rec)==len(records)*2
report=dict(aprovado=not bad,objetos=len(man),pares=tested,intersecoes=bad,celulas=2,solidos_copiados=ident,extensao_refletor_Y_mm=ref.BoundBox.YLength,extensao_refletor_Z_mm=ref.BoundBox.ZLength,asa_reta_mm=tail,dobra_alpha_graus=cfg['angulo_dobra_graus'],inicio_dobra_Y_mm=b)
for n,v in [('manifesto',man),('folhas_solidas',rec),('portas',cfg['portas']),('intersecoes',report)]: (out/(n+'.json')).write_text(json.dumps(v,indent=2)+'\n')
assert not bad,bad
for mat in sorted(set(man.values())):Import.export([d.getObject(n) for n,m in man.items() if m==mat],str(out/(mat+'.step')))
A.closeDocument(source.Name);A.closeDocument(d.Name)
re=A.openDocument(str(native));assert all(re.getObject(n).Shape.isValid() for n in man)
(out/'reabertura.json').write_text(json.dumps(dict(objetos=len(man),todos_validos=True,sha256=hashlib.sha256(native.read_bytes()).hexdigest()),indent=2)+'\n')
A.closeDocument(re.Name);print('CAD_OK',cfg['revisao'],len(man),tested)
