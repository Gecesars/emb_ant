"""Envelope paramétrico no FreeCAD. As dimensões nominais coincidem com HFSS e KiCad."""
from pathlib import Path
import json
import FreeCAD as App
import Part

here=Path(__file__).resolve().parent
geometry=json.loads((here.parent/"automacao/P1H/KiCad_Antenas/elemento_hfss.json").read_text())
Vec=App.Vector

def profile(rect,holes):
    x1,y1,x2,y2=rect
    pts=[Vec(x1,y1,0),Vec(x2,y1,0),Vec(x2,y2,0),Vec(x1,y2,0)]
    face=Part.Face(Part.makePolygon(pts+[pts[0]]))
    for x,y,r in holes:
        circ=Part.Face(Part.Wire([Part.makeCircle(r,Vec(x,y,0))]))
        face=face.cut(circ)
    return face

def holder(doc,name,shape):
    obj=doc.addObject("Part::Feature",name);obj.Shape=shape
    return obj

def archive(doc,name,expected):
    doc.recompute()
    final=[o for o in doc.Objects if o.Name.startswith(("Nucleo","Refletor","CobreRF","PlacaDivisor"))]
    assert len(final)==expected and all(not obj.Shape.isNull() and obj.Shape.isValid() for obj in final)
    doc.saveAs(str(here/(name+".FCStd")));App.closeDocument(doc.Name)
    reopened=App.openDocument(str(here/(name+".FCStd")))
    assert len([o for o in reopened.Objects if o.Name.startswith(("Nucleo","Refletor","CobreRF","PlacaDivisor"))])==expected
    App.closeDocument(reopened.Name)

ports=list(geometry["ports"].values())
holes=[(x,y,.425) for x,y in ports]+[(x,y,.2) for x,y in geometry["vias"]]
outline=geometry["outline"][0];half=outline/2;pitch=geometry["pitch"];h=geometry["core"]
reflector=profile((-24.15625,-18,24.15625,18),[(x,y,1.3067316) for x,y in ports])
boards=profile((-half,-half,half,half),holes).extrude(Vec(0,0,h))
def poly(points):
    q=[Vec(x,y,0) for x,y in points]
    return Part.Face(Part.makePolygon(q+[q[0]]))
def circle(x,y,r):
    return Part.Face(Part.Wire([Part.makeCircle(r,Vec(x,y,0))]))
layers={"F":[],"B":[]}
for pad in geometry["lands"]:
    face=poly(pad["outer"])
    for cut in pad["holes"]:face=face.cut(poly(cut))
    layers[pad["layer"]].append(face)
for layer,pieces in layers.items():
    for x,y in ports:pieces.append(circle(x,y,.60))
    for x,y in geometry["vias"]:pieces.append(circle(x,y,.363))
    copper=pieces[0].multiFuse(pieces[1:]).removeSplitter()
    for x,y,r in holes:copper=copper.cut(circle(x,y,r))
    copper.translate(Vec(0,0,h if layer=="F" else 0))
    layers[layer]=copper
artwork=Part.makeCompound([layers["F"],layers["B"]])
for one in (False,True):
    name="P1H_10_"+("Continua" if one else "Separadas")
    d=App.newDocument(name)
    spec=d.addObject("App::FeaturePython","Dimensoes")
    for n,val in [("Passo",pitch),("Altura",16.61)]:
        spec.addProperty("App::PropertyLength",n,"Dimensoes");setattr(spec,n,val)
    if one:
        perforations=[(x+(i-4.5)*pitch,y,r) for i in range(10) for x,y,r in holes]
        total=9*pitch+outline
        board=holder(d,"Nucleo_continuo",profile((-total/2,-half,total/2,half),perforations).extrude(Vec(0,0,h)))
        board.setExpression("Placement.Base.z","Dimensoes.Altura")
        spec.setEditorMode("Passo",1)
    for i in range(10):
        shapes=[("Refletor",reflector,False),("CobreRF",artwork,True)]
        if not one:shapes.append(("Nucleo",boards,True))
        for label,shape,raised in shapes:
            item=holder(d,label+"_%02d"%(i+1),shape)
            item.setExpression("Placement.Base.x","(%s) * Dimensoes.Passo"%(i-4.5))
            if raised:item.setExpression("Placement.Base.z","Dimensoes.Altura")
    d.recompute();d.getObject("Dimensoes").Altura=18;d.recompute()
    assert abs(d.getObject("CobreRF_01").Placement.Base.z-18)<1.e-6
    d.getObject("Dimensoes").Altura=16.61
    archive(d,name,21 if one else 30)

g=json.loads((here.parent/"automacao/P1H/Divisor_10X_PTFE/geometria.json").read_text())
d=App.newDocument("Divisor_2x10_PTFE")
ref=holder(d,"PlacaDivisor",profile((-g["half_x"],-g["half_y"],g["half_x"],g["half_y"]),[(x,y,.5) for _,x,y in g["ports"]]).extrude(Vec(0,0,g["h"])))
assert len(ref.Shape.Solids)==1 and abs(ref.Shape.BoundBox.ZLength-1.52)<1.e-6
archive(d,"Divisor_2x10_PTFE",1)
print("FreeCAD: tres documentos reabertos e conferidos.")
