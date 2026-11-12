"""Executar no FreeCAD GUI; altera apenas a apresentacao da montagem R17."""
from pathlib import Path
import json
import FreeCAD as A,FreeCADGui as G
V=A.Vector;ROOT=Path('D:/dev/EMBRAER/P2S13/R17_Flanges_Refletor/mecanica');OUT=ROOT/'imagens';OUT.mkdir(exist_ok=True)
d=next((x for x in A.listDocuments().values() if x.FileName.replace('\\','/')==str(ROOT/'Antena_DN100_R17_PRELIMINAR.FCStd')),None)
if d is None:d=A.openDocument(str(ROOT/'Antena_DN100_R17_PRELIMINAR.FCStd'))
A.setActiveDocument(d.Name);G.updateGui()
objs=[o for o in d.Objects if o.isDerivedFrom('Part::Feature')]
cols=json.loads((ROOT/'cores.json').read_text())
for o in objs:
    o.ViewObject.ShapeColor=tuple(cols[o.Name]);o.ViewObject.LineColor=(.2,.23,.25);o.ViewObject.DisplayMode='Flat Lines';o.ViewObject.Visibility=True
    if 'PVC' in o.Name:o.ViewObject.Transparency=88
v=G.getDocument(d.Name).activeView()
def frame(view,objects,rot,w,h):
    view.setCameraType('Orthographic');G.updateGui()
    projected=[]
    for o in objects:
        if not o.ViewObject.Visibility:continue
        b=o.Shape.optimalBoundingBox(False,False)
        for x in [b.XMin,b.XMax]:
            for y in [b.YMin,b.YMax]:
                for z in [b.ZMin,b.ZMax]:projected.append(rot.inverted().multVec(V(x,y,z)))
    lo=[min(getattr(q,k) for q in projected) for k in ['x','y','z']];hi=[max(getattr(q,k) for q in projected) for k in ['x','y','z']]
    center=rot.multVec(V(*[(a+b)/2 for a,b in zip(lo,hi)]));pos=center+rot.multVec(V(0,0,1000))
    node=view.getCameraNode();node.orientation.setValue(*rot.Q);node.position.setValue(pos.x,pos.y,pos.z);node.height.setValue(max(hi[1]-lo[1],(hi[0]-lo[0])*h/w)*1.10)
    node.focalDistance.setValue(1000);node.nearDistance.setValue(1);node.farDistance.setValue(5000)
    G.updateGui()
def save(name,rot,w=2000,h=1000):
    frame(v,objs,rot,w,h);v.saveImage(str(OUT/(name+'.png')),w,h,'White')
save('montagem_transparente',A.Rotation(V(0,-1,0),V(1,0,0),V(.25,0,1),'ZXY'),1200,1800)
for o in objs:
    if 'PVC' in o.Name:o.ViewObject.Visibility=False
save('interno_frente',A.Rotation())
save('interno_verso',A.Rotation(V(1,0,0),180))
save('montagem_corte',A.Rotation(V(1,0,0),160))
for o in objs:o.ViewObject.Visibility=o.Name.startswith(('Flange_Inferior','Junta_Inferior','N_','M3_Inferior'))
save('flange_inferior',A.Rotation(V(0,-1,0),V(0,0,1),V(-1,0,0),'ZXY'),1600,1200)
# Vista local em novo documento somente de apresentacao, sem alterar o BREP fonte.
import Part
detail=A.newDocument('R17_Detalhe_Lingueta')
clip=Part.makeBox(35,36,29,V(150,-18,-24))
for o in objs:
    if not o.Name.startswith(('Refletor_Al2mm','Flange_Superior','M3_Superior')):continue
    sh=o.Shape.common(clip)
    if sh.isNull() or sh.Volume<1e-8:continue
    z=detail.addObject('Part::Feature',o.Name);z.Shape=sh;z.ViewObject.ShapeColor=tuple(cols[o.Name]);z.ViewObject.DisplayMode='Flat Lines'
detail.recompute();A.setActiveDocument(detail.Name);G.updateGui();dv=G.getDocument(detail.Name).activeView();frame(dv,detail.Objects,A.Rotation(V(1,-1,0),V(0,0,1),V(-1,-1,.65),'ZXY'),1600,1100);dv.saveImage(str(OUT/'detalhe_lingueta.png'),1600,1100,'White')
A.closeDocument(detail.Name);A.setActiveDocument(d.Name)
for o in objs:o.ViewObject.Visibility=True
v=G.getDocument(d.Name).activeView();frame(v,objs,A.Rotation(V(0,-1,0),V(1,0,0),V(.25,0,1),'ZXY'),1600,1000);d.save()
print('R17_IMAGENS',OUT)
