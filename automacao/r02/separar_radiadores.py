"""Controle R02-S: dez PCBs individuais no mesmo chassi, com o mesmo chicote e divisores."""
import json
import os
import shutil
import sys
from pathlib import Path

import FreeCAD as App
import Import
import Part

repo=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(repo/"freecad/mecanica_R01/fonte"))
import construir as m
src=Path(os.environ["P1H_R02_CAD"])
target=Path(os.environ["P1H_R01"])/"cad"
target.mkdir(parents=True,exist_ok=True)
assert src.resolve()!=target.resolve()
manifest=json.loads((src/"manifesto.json").read_text())
for file in src.glob("*.step"):
    if file.stem not in ("RO4350B_R01","POM_nom"):shutil.copyfile(file,target/file.name)


def output(doc,name,shape):
    assert shape.isValid() and len(shape.Solids)==1,name
    o=doc.addObject("Part::Feature",name);o.Label=name;o.Shape=shape
    return o


source=App.newDocument("BaseContinua")
Import.insert(str(src/"RO4350B_R01.step"),source.Name)
continuous=next(o.Shape.copy() for o in source.Objects if o.Label=="Rogers")
doc=App.newDocument("Individuais")
size=28.3125
centers=[(i-4.5)*m.PASSO for i in range(10)]
isolated=[]
for i,x in enumerate(centers,1):
    shape=continuous.common(m.bx(x-size/2,-size/2,m.PLACA_Z-.1,size,size,m.CORE+.2))
    obj=output(doc,"Rogers_E%02d"%i,shape)
    manifest[obj.Label]="RO4350B_R01"
    isolated.append(obj)
del manifest["Rogers"]
delta=continuous.Volume-sum(o.Shape.Volume for o in isolated)
assert abs(delta-9*(m.PASSO-size)*size*m.CORE)<.001
Import.export(isolated,str(target/"RO4350B_R01.step"))

old=App.newDocument("Suportes")
Import.insert(str(src/"POM_nom.step"),old.Name)
rad=m.PLACA_Z


def rail(side):
    def block(x1,x2,y1,y2,z1,z2):
        lo=y1 if side>0 else -y2
        return m.bx(x1,lo,z1,x2-x1,y2-y1,z2-z1)
    solids=[block(-252.6,252.6,15.2,18.1,14.7,18.5)]
    for x in centers:
        a=x-size/2;b=x+size/2
        solids.extend([block(a-.2,b+.2,13.35,15.25,15,rad),block(a-.2,b+.2,13.6,15.25,rad+m.CORE+.25,18.5),
                       block(a-.2,b+.2,14.32,15.25,rad,rad+m.CORE+.25)])
        for t in [a-.2-1.1,b+.2]:solids.append(block(t,t+1.1,13.35,15.25,15,18.5))
    for x in m.SUP_X:
        solids.append(m.cz(x,side*16.65,12.7,.8,2.05))
    return m.union(solids)


rails=[rail(side) for side in (-1,1)]
new=[]
for side,sh in zip(("E","D"),rails):
    obj=output(doc,"Guia_PCB_"+side,sh);manifest[obj.Label]="POM_nom";new.append(obj)
    assert all(sh.common(o.Shape).Volume<1e-6 for o in isolated)
for o in old.Objects:
    if manifest.get(o.Label)!="POM_nom":continue
    sh=o.Shape.copy()
    if o.Label.startswith(("Berco_","Batente_")):
        for i,rail_shape in enumerate(rails):
            # Abrir a sela pelo topo para que as guias, com os pinos integrados, possam assentar.
            y=15.2 if i==1 else -18.1
            sh=sh.cut(m.bx(-252.6,y,14.7,505.2,2.9,5.5)).cut(rail_shape)
            assert sh.common(rail_shape).Volume<1e-6
    new.append(output(doc,o.Label,sh))
assert len(new)==15
Import.export(new,str(target/"POM_nom.step"))
(target/"manifesto.json").write_text(json.dumps(manifest,indent=2),encoding="utf8")
print("R02_S_OK",len(isolated),"radiadores",len(new),"componentes POM",round(delta,6),"mm3 de laminado retirados")
