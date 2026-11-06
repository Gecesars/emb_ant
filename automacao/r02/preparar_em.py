"""Exportar o conjunto R02 para o HFSS. Reutilizar somente peças comuns do CAD EM da R01."""
import json
import os
import sys
from pathlib import Path

import FreeCAD as App
import Import
import Part

repo=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(repo/"freecad/mecanica_R01/fonte"))
import construir as m

V=App.Vector
root=Path(os.environ["P1H_R02"])
cad=Path(os.environ["P1H_R01"])/"cad"
source=Path(os.environ["P1H_CAD_BASE"])
cad.mkdir(exist_ok=True,parents=True)
mechanical=App.openDocument(str(root/"compacta/P1H_R02_compacta.FCStd"))
out=App.newDocument("R02_EM")
parts={}
coils={}
zb=-11.52
zf=zb+1.52


def add(name,shape,material):
    assert shape.isValid() and not shape.isNull(),name
    obj=out.addObject("Part::Feature",name)
    obj.Label=name
    obj.Shape=shape
    parts.setdefault(material,[]).append(obj)


def cylinder(x,y,r,z,h):
    return Part.makeCylinder(r,h,V(x,y,z))


def disk(x,y,r,z):
    return Part.Face(Part.Wire([Part.makeCircle(r,V(x,y,z))]))


def face(points,dx,z):
    pts=[V(dx+x,y,z) for x,y in points]
    return Part.Face(Part.makePolygon(pts+[pts[0]]))


for material,labels in [("copper",("Via",)),("folha_cu",("Ant",)),("latao_nom",("N_",)),
                        ("PTFE_cabo",("N_isol_",)),("RO4350B_R01",("Rogers",))]:
    old=App.newDocument("Origem")
    Import.insert(str(source/(material+".step")),old.Name)
    for o in old.Objects:
        if o.Label.startswith(labels):
            add(o.Label,o.Shape.copy(),material)
        if o.Label in ("Lancamento_A","Lancamento_B"):
            pol=o.Label[-1]
            x=m.PIN;y=(-1 if pol=="A" else 1)*m.N_Y
            clip=o.Shape.common(m.bx(x-5,y-5,m.DIV_B-5,10,10,6.52))
            clip.translate(V(0,0,zb-m.DIV_B))
            assert len(clip.Solids)==1
            coils[pol]=clip
    App.closeDocument(old.Name)
assert len(parts["folha_cu"])==100 and len(parts["copper"])==20
assert len(parts["latao_nom"])==4 and len(parts["PTFE_cabo"])==2 and len(coils)==2
for o in mechanical.Objects:
    name=o.Name
    if name=="Refletor_R02":mat="AL5052"
    elif name.startswith("Trilho_"):mat="aco_nom" if "_par_" in name else "POM_nom"
    elif name.startswith(("Berco_","Batente_")):mat="POM_nom"
    elif name.startswith(("Passa_","Junta_N_")):mat="Silicone_nom"
    elif name.startswith("Termorretratil_N_"):mat="PE_nom"
    elif name.startswith(("Par_","Arruela_")) and not name.startswith("Arruela_N_"):mat="aco_nom"
    else:continue
    add(name,o.Shape.copy(),mat)


for side,offset in [("Inferior",m.PIN-2.5*m.PASSO),("Superior",m.PIN+2.5*m.PASSO)]:
    g=json.loads((root/"placas"/side/"geometria.json").read_text())
    core=face(g["outline"],offset,zb).extrude(V(0,0,1.52))
    core=core.cut(face(g["janela"],offset,zb).extrude(V(0,0,1.52)))
    gnd=face(g["outline_gnd"],offset,zb).cut(face(g["janela_sem_cobre"],offset,zb))
    traces={net:face(points,offset,zf) for net,points in g["copper"].items()}
    for name,px,y in g["ports"]:
        x=offset+px
        net=g["port_net"][name]
        traces[net]=traces[net].fuse(disk(x,y,.73,zf)).cut(disk(x,y,.525,zf))
        core=core.cut(cylinder(x,y,.525,zb-.01,1.54))
        root_input=name in ("RA_IN","RB_IN")
        gnd=gnd.cut(disk(x,y,1.515 if root_input else 2.13,zb))
        add("Pad_"+side+"_"+name,disk(x,y,.73,zb).cut(disk(x,y,.525,zb)),"folha_cu")
        if not root_input:
            solder=cylinder(x,y,2.13,zb-.18,.18).cut(cylinder(x,y,m.R_CABO,zb-.18,.18))
            add("Solda_"+side+"_"+name,solder,"SAC305")
    add("PCB_"+side,core,"ZYF300")
    add("Massa_"+side,gnd,"folha_cu")
    for net,sh in traces.items():add("Estrela_"+side+"_"+net,sh.removeSplitter(),"folha_cu")


routes=json.loads((root/"compacta/caminhos.json").read_text())
routes.update(json.loads((root/"compacta/enlaces.json").read_text()))
for name,edges in routes.items():
    inp=name.startswith("IN_")
    trunk=name.startswith("TR_")
    x,y,z=edges[-1][-1]
    sx,sy,sz=edges[0][1]
    # Na janela de entrada conservam-se cinco mm das superfícies originais
    # de conexão e da bobina. As retas finais são normais às PCBs.
    if inp or not trunk:edges[-1][-1][2]-=5 if inp else 1
    wire=m.wire_from_data(edges)
    outer=m.tube(wire,m.R_CABO);die=m.tube(wire,1.515);inner=m.tube(wire,.45975)
    outer=outer.cut(die);die=die.cut(inner)
    if inp:
        metal=m.union([coils[name[-1]],inner,outer])
        die=m.union([die,cylinder(x,y,1.515,zb-5,1).cut(cylinder(x,y,.45975,zb-5,1))])
        assert len(metal.Solids)==1,name
        add("Lancamento_"+name[-1],metal,"copper")
    else:
        barrel=cylinder(sx,sy,.525,zb,1.52)
        if trunk:
            inner=m.union([inner,barrel,cylinder(x,y,.525,zb,1.52)])
        else:
            base=m.PLACA_Z
            lower=cylinder(x,y,m.R_CABO,base-1,.25).cut(cylinder(x,y,.834856,base-1,.25))
            upper=cylinder(x,y,1.2704335,base-.75,.75).cut(cylinder(x,y,.834856,base-.75,.75))
            outer=m.union([outer,lower,upper])
            inner=m.union([inner,barrel,cylinder(x,y,.362981,base-1,1),cylinder(x,y,.45,base,m.CORE)])
        assert len(inner.Solids)==1 and len(outer.Solids)==1,name
        add("Sinal_"+name,inner,"copper");add("Capa_"+name,outer,"copper")
    add("Isol_"+name,die,"PTFE_cabo")
assert len(parts["SAC305"])==28 and len(parts["ZYF300"])==2 and len(parts["PTFE_cabo"])==28
assert len(parts["POM_nom"])==13 and len(parts["Silicone_nom"])==12
out.recompute()
manifest={}
for material,objects in parts.items():
    manifest.update({o.Label:material for o in objects})
    Import.export(objects,str(cad/(material+".step")))
(cad/"manifesto.json").write_text(json.dumps(manifest,indent=2),encoding="utf8")
print("CAD_R02_OK",len(manifest),{k:len(v) for k,v in parts.items()})
