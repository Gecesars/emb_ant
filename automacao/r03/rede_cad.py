"""Exportar as duas PCBs com a emenda e os 11 lançamentos do modo par de excitação."""
import json
import os
from pathlib import Path
import FreeCAD as App
import Import
import Part

root=Path(os.environ["P1H_R03"])
V=App.Vector
def disk(x,y,r,z):return Part.Face(Part.Wire([Part.makeCircle(r,V(x,y,z))]))
def cylinder(x,y,r,z,h):return Part.makeCylinder(r,h,V(x,y,z))
def poly(points,z):
    pts=[V(x,y,z) for x,y in points]
    return Part.Face(Part.makePolygon(pts+[pts[0]]))
def rect(x1,x2,y1,y2,z):
    return poly([(x1,y1),(x2,y1),(x2,y2),(x1,y2)],z)

def make(mat,painel=False):
    p=root/mat;out=p/("cad_painel" if painel else "rede_hfss");out.mkdir(exist_ok=True)
    doc=App.newDocument("Rede_longitudinal")
    pieces={};ports=[]
    def add(label,shape,material):
        assert shape.isValid() and not shape.isNull(),label
        obj=doc.addObject("Part::Feature",label);obj.Label=label;obj.Shape=shape
        pieces.setdefault(material,[]).append(obj)
    center=15.4; yseam=31.5
    h=json.loads((p/"Inferior/geometria.json").read_text())["h"]
    w=json.loads((p/"linhas.json").read_text())["larguras"]["50.0"]["largura_mm"]
    polaridades=[1,-1] if painel else [1]
    strap=Part.makeCompound([rect(center-3,center+3,s*yseam-w/2,s*yseam+w/2,h) for s in polaridades])
    ground_strap=Part.makeCompound([rect(center-3,center+3,s*yseam-7,s*yseam+7,0) for s in polaridades])
    add("Emenda_sinal",strap.extrude(V(0,0,.10)),"copper")
    add("Emenda_massa",ground_strap.extrude(V(0,0,-.10)),"copper")
    half=Part.makeBox(600,100,8,V(-300,0,-3))
    for side in ("Inferior","Superior"):
        g=json.loads((p/side/"geometria.json").read_text())
        core=poly(g["outline"],0).extrude(V(0,0,h))
        ground=poly(g["outline_gnd"],0).cut(ground_strap)
        if not painel:core=core.common(half);ground=ground.common(half)
        trace=Part.makeCompound([poly(g["copper"][k],h).cut(strap) for k in (["A","B"] if painel else ["B"])])
        for x,y in g["fixacao"]:
            if not painel and y<=0:continue
            core=core.cut(cylinder(x,y,1.4,-.01,h+.02))
            ground=ground.cut(disk(x,y,1.4+.785,0))
        for name,x,y in g["ports"]:
            if not painel and not name.startswith("B"):continue
            entrada=name.endswith("_IN")
            key=name if painel else ("IN" if entrada else "E%02d"%int(name[1:]))
            ports.append([key,x,y])
            trace=trace.fuse(disk(x,y,.73,h)).cut(disk(x,y,.525,h))
            ground=ground.cut(disk(x,y,1.515 if painel and entrada else 2.13,0))
            core=core.cut(cylinder(x,y,.525,-.01,h+.02))
            add("Pad_"+key,disk(x,y,.73,0).cut(disk(x,y,.525,0)),"folha")
            if painel:
                if not entrada:add("Solda_"+key,cylinder(x,y,2.13,-.18,.18).cut(cylinder(x,y,1.7905,-.18,.18)),"SAC305")
                continue
            start=cylinder(x,y,.45975,-1.5,1.5)
            inner=start.fuse(cylinder(x,y,.525,0,h)).removeSplitter()
            add("Pino_"+key,inner,"copper")
            add("Isol_"+key,cylinder(x,y,1.515,-1.5,1.5).cut(start),"cabo")
            add("Capa_"+key,cylinder(x,y,1.7905,-1.5,1.5).cut(cylinder(x,y,1.515,-1.5,1.5)),"copper")
            add("Solda_"+key,cylinder(x,y,2.13,-.18,.18).cut(cylinder(x,y,1.7905,-.18,.18)),"SAC305")
        add("Laminado_"+side,core,"LAM")
        add("GND_"+side,ground,"folha")
        add("Rede_"+side,trace.removeSplitter(),"folha")
    assert len(ports)==(22 if painel else 11)
    for material,subset in pieces.items():Import.export(subset,str(out/(material+".step")))
    (out/"portas.json").write_text(json.dumps(ports))
    App.closeDocument(doc.Name)
    print("CAD_REDE_OK",mat,len(ports))
if __name__=="__main__":
    for material in os.environ.get("P1H_MATERIAIS","ZYF300CA-C,ZYF255DA,ZYF265D,ZYF300CA-P").split(","):make(material)
