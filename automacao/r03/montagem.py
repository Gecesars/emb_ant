"""Modelo OCCT das duas placas alongadas, postes coaxiais e entradas curtas da R03."""
import csv
import json
import os
import sys
from itertools import combinations
from pathlib import Path
import FreeCAD as App
import Part

repo=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(repo/"freecad/mecanica_R01/fonte"))
import construir as m

w=Path(os.environ["P1H_R03"]);out=w/"mecanica";out.mkdir(exist_ok=True)
model=os.environ.get("P1H_MATERIAL","ZYF300CA-C")
pieces={s:json.loads((w/model/s/"geometria.json").read_text()) for s in ["Inferior","Superior"]}
V=App.Vector;GROUND=-10.;SIGNAL=-11.52
fix=[(x+m.PIN,y) for g in pieces.values() for x,y in g["fixacao"]]
bolts=[(x,y) for x in m.SUP_X+m.BAT_X for y in [-11.,11.]]+fix
m.SAIDA=out;m.ref_bolts=lambda:bolts
flat=m.flat();chassis=m.folded()
(out/"verificacao.json").write_text(json.dumps(dict(volume_dobrado_mm3=chassis.Volume,volume_planificado_mm3=flat,
     furos_fixacao_mm=bolts,diametro_mm=2.8),indent=2))
base=App.openDocument(str(repo/"freecad/mecanica_R01/03_Antena_montada.FCStd"))
doc=App.newDocument("Montagem_R03");obstacles={}
def add(name,sh,obstacle=True):
    assert sh.isValid() and not sh.isNull(),name
    obj=doc.addObject("Part::Feature",name);obj.Shape=sh
    if obstacle:obstacles[name]=sh
    return obj
def face(pts,z):
    vertices=[V(m.PIN+x,y,z) for x,y in pts]
    return Part.Face(Part.makePolygon(vertices+[vertices[0]]))
for group in [base.Radiadores,base.Apoios_POM,base.Passagens,base.Fixadores,base.Entradas_N]:
    for obj in group.Group:
        if not obj.Name.startswith("Par_trilho"):
            add(obj.Name,obj.Shape.copy(),not obj.Name.startswith("CobreRF"))
add("Refletor_R03",chassis)
for side,g in pieces.items():
    core=face(g["outline"],SIGNAL).extrude(V(0,0,1.52))
    holes=[m.cz(x+m.PIN,y,SIGNAL-.1,.5,1.72) for _,x,y in g["ports"]]
    holes.extend([m.cz(x+m.PIN,y,SIGNAL-.1,1.4,1.72) for x,y in g["fixacao"]])
    core=core.cut(Part.makeCompound(holes))
    add("PCB_"+side,core)
    for pol,pts in g["copper"].items():
        trace=face(pts,SIGNAL).extrude(V(0,0,-.035)).cut(Part.makeCompound(holes))
        add("RF_"+side+"_"+pol,trace,False)
    gholes=[m.cz(x+m.PIN,y,GROUND-.01,1.515,.06) for _,x,y in g["ports"]]
    gholes.extend([m.cz(x+m.PIN,y,GROUND-.01,2.185,.06) for x,y in g["fixacao"]])
    add("Massa_"+side,face(g["outline_gnd"],GROUND).extrude(V(0,0,.035)).cut(Part.makeCompound(gholes)),False)
for i,(x,y) in enumerate(fix):
    body=m.cz(x,y,GROUND,3,8).cut(m.cz(x,y,GROUND-.1,1.025,8.2))
    add("Espacador_%02d"%i,body)
    add("Par_fronte_%02d"%i,m.screw(x,y,0,-1,5.2))
    add("Nylon_pcb_%02d"%i,m.screw(x,y,SIGNAL,1,5.6))
for side,sgn in [("A",-1),("B",1)]:
    seam=m.PIN+15.4;y=sgn*31.5
    width=json.loads((w/model/"linhas.json").read_text())["larguras"]["50.0"]["largura_mm"]
    add("Fita_RF_"+side,m.bx(seam-3,y-width/2,SIGNAL-.10,6,width,.10))
    add("Fita_GND_"+side,m.bx(seam-3,y-7,GROUND,6,14,.10))
paths={};wires={}
for i in range(10):
    for pol,sgn in [("A",-1),("B",1)]:
        name="E%02d_"%(i+1)+pol;x=(i-4.5)*m.PASSO+m.PIN;y=sgn*m.PIN
        edges=[["L",[x,y,GROUND],[x,y,m.PLACA_Z]]]
        paths[name]=edges;wires[name]=m.wire_from_data(edges)
        add(name,m.cz(x,y,GROUND,m.R_CABO,m.PLACA_Z-GROUND))
def clashes(sh,collection):
    result=[]
    for label,other in collection.items():
        if sh.BoundBox.intersect(other.BoundBox) and sh.common(other).Volume>1e-5:result.append(label)
    return result
for length,edges in json.loads((w/"candidatos.json").read_text()):
    pair={}
    for pol,sgn in [("A",-1),("B",1)]:
        coords=[[tag,*[[x,y*sgn,z] for x,y,z in pts]] for tag,*pts in edges]
        wire=m.wire_from_data(coords);tube=m.tube(wire,m.R_CABO)
        if clashes(tube,obstacles):break
        pair[pol]=(coords,wire,tube)
    if len(pair)==2:break
else:raise RuntimeError("Sem par de entradas entre as rotas candidatas.")
for pol,(coords,wire,tube) in pair.items():
    key="IN_"+pol;paths[key]=coords;wires[key]=wire
    # A janela de 4 mm deixa a bobina e os dois terminais visíveis na montagem.
    body=json.loads(json.dumps(coords));body[-1][-1][2]+=4
    add(key,m.tube(m.wire_from_data(body),m.R_CABO))
    orig=base.getObject("Bobina_"+pol).Shape.copy()
    trans=base.getObject("Terminal_IN_"+pol).Shape.copy()
    pos=V(m.PIN,(-1 if pol=="A" else 1)*m.N_Y,m.DIV_B)
    end=V(*coords[-1][-1])
    for name,shape in [("Bobina_"+pol,orig),("Terminal_"+key,trans)]:
        shape.rotate(pos,V(0,1,0),180);shape.translate(end-pos);add(name,shape,False)
errors=[]
for key,sh in obstacles.items():
    if not key.startswith(("PCB_","Espacador_","Nylon_","Par_fronte_","E0","E10","Fita_")):continue
    for nm in clashes(sh,{n:other for n,other in obstacles.items() if n!=key}):errors.append([key,nm])
mindist=min(w1.distToShape(w2)[0]-2*m.R_CABO for (k,w1),(j,w2) in combinations(wires.items(),2))
result=dict(material=model,interferencias=errors,folga_minima_entre_capas_mm=mindist,
            comprimentos_mm={k:wire.Length for k,wire in wires.items()},postes=20,cabos_entrada=2,
            comprimento_total_mm=sum(wire.Length for wire in wires.values()),furos_fixacao_pcb=len(fix))
(out/"verificacao_chicote.json").write_text(json.dumps(result,indent=2),encoding="utf8")
assert not errors,errors
assert mindist>1.4 and abs(wires["IN_A"].Length-wires["IN_B"].Length)<1e-6
(out/"caminhos.json").write_text(json.dumps(paths,indent=1))
doc.recompute();doc.saveAs(str(out/"P1H_R03_alongada.FCStd"))
print("R03_CAD_OK",round(length,6),round(mindist,6),len(paths))
