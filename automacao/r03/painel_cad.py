"""Gerar o CAD EM do painel completo no sistema de coordenadas comum às três revisões."""
import json
import os
import sys
from pathlib import Path
import FreeCAD as App
import Import
import Part
from rede_cad import make

repo=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(repo/"freecad/mecanica_R01/fonte"))
import construir as m

V=App.Vector
estudo=Path(os.environ["P1H_R03"])
rad=Path(os.environ["P1H_CAD_BASE"])
dest=Path(os.environ["P1H_R01"])/"cad";dest.mkdir(parents=True,exist_ok=True)
material=os.environ.get("P1H_MATERIAL","ZYF300CA-C")
make(material,True)
lam=estudo/material;board=lam/"cad_painel"
g=json.loads((lam/"Inferior/geometria.json").read_text())
doc=App.newDocument("Painel_R03");pieces={};coils={}
ground=-10.

def add(name,shape,mat):
    assert shape.isValid() and not shape.isNull(),name
    o=doc.addObject("Part::Feature",name);o.Label=name;o.Shape=shape
    pieces.setdefault(mat,[]).append(o)

def read(path):
    d=App.newDocument("Importacao")
    Import.insert(str(path),d.Name)
    try:
        for o in d.Objects:
            if o.TypeId=="Part::Feature" and not o.Shape.isNull():yield o.Label,o.Shape.copy()
    finally:App.closeDocument(d.Name)

for mat,labels in [("copper",("Via",)),("folha_cu",("Ant",)),("latao_nom",("N_",)),
                   ("PTFE_cabo",("N_isol_",)),("RO4350B_R01",("Rogers",))]:
    for name,shape in read(rad/(mat+".step")):
        if name.startswith(labels):add(name,shape,mat)
        if name in ("Lancamento_A","Lancamento_B"):
            pol=name[-1];y=(-1 if pol=="A" else 1)*m.N_Y
            axis=V(m.PIN,y,m.DIV_B)
            head=shape.common(m.bx(m.PIN-5,y-5,m.DIV_B-5,10,10,6.52))
            head.rotate(axis,V(0,1,0),180)
            head.translate(V(m.PIN-230,(-1 if pol=="A" else 1)*31,ground)-axis)
            assert len(head.Solids)==1
            coils[pol]=head
assert len(coils)==2 and len(pieces["folha_cu"])==100 and len(pieces["copper"])==20
for key,mat in [("LAM","ZYF300"),("copper","copper"),("SAC305","SAC305"),("folha","folha_cu")]:
    for name,shape in read(board/(key+".step")):
        shape=shape.mirror(V(),V(0,0,1))
        shape.translate(V(m.PIN,0,ground))
        add(name,shape,mat)
mech=App.openDocument(str(estudo/"mecanica/P1H_R03_alongada.FCStd"))
for o in mech.Objects:
    n=o.Name
    if n=="Refletor_R03":mat="AL5052"
    elif n.startswith(("Berco_","Batente_","Espacador_")):mat="POM_nom"
    elif n.startswith(("Passa_","Junta_N_")):mat="Silicone_nom"
    elif n.startswith("Termorretratil_N_"):mat="PE_nom"
    elif n.startswith("Nylon_pcb_"):mat="PA_nom"
    elif n.startswith(("Par_","Arruela_")) and not n.startswith("Arruela_N_"):mat="aco_nom"
    else:continue
    add(n,o.Shape.copy(),mat)
App.closeDocument(mech.Name)

def cyl(x,y,r,z,h):return Part.makeCylinder(r,h,V(x,y,z))
for name,edges in json.loads((estudo/"mecanica/caminhos.json").read_text()).items():
    x,y,z=edges[-1][-1];inp=name.startswith("IN")
    edges[-1][-1][2]+=5 if inp else -1
    wire=m.wire_from_data(edges)
    outer=m.tube(wire,m.R_CABO);die=m.tube(wire,1.515);inner=m.tube(wire,.45975)
    outer=outer.cut(die);die=die.cut(inner)
    if inp:
        joined=m.union([coils[name[-1]],inner,outer])
        assert len(joined.Solids)==1,name
        add("Lancamento_"+name[-1],joined,"copper")
        die=m.union([die,cyl(x,y,1.515,ground+4,1).cut(cyl(x,y,.45975,ground+4,1))])
    else:
        inner=m.union([inner,cyl(x,y,.525,ground-1.52,1.52),cyl(x,y,.362981,z-1,1),cyl(x,y,.45,z,m.CORE)])
        bottom=cyl(x,y,m.R_CABO,z-1,.25).cut(cyl(x,y,.834856,z-1,.25))
        top=cyl(x,y,1.2704335,z-.75,.75).cut(cyl(x,y,.834856,z-.75,.75))
        outer=m.union([outer,bottom,top])
        assert len(inner.Solids)==len(outer.Solids)==1,name
        add("Sinal_"+name,inner,"copper");add("Capa_"+name,outer,"copper")
    add("Isol_"+name,die,"PTFE_cabo")
assert len(pieces["SAC305"])==20 and len(pieces["PTFE_cabo"])==24
assert len(pieces["PA_nom"])==14 and len(pieces["Silicone_nom"])==12
manifest={}
for mat,items in pieces.items():
    Import.export(items,str(dest/(mat+".step")))
    manifest.update({o.Label:mat for o in items})
(dest/"manifesto.json").write_text(json.dumps(manifest,indent=2))
(dest/"laminados.json").write_text(json.dumps({"ZYF300":[g["dk"],g["df"]],"PA_nom":[3.3,.02]}))
print("CAD_PAINEL_OK",material,{k:len(v) for k,v in pieces.items()})
