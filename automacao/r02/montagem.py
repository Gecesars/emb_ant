"""Conferência OCCT dos dois divisores compactos, chicote e interfaces da R02."""
from itertools import combinations
import json
import os
import sys
from pathlib import Path
import FreeCAD as App
import Part

repo=Path(__file__).resolve().parents[2]
mech=repo/"freecad/mecanica_R01"
sys.path.insert(0,str(mech/"fonte"))
import construir as m
from dimensoes import PIN, PASSO, PLACA_Z, R_CABO, N_Y
V=App.Vector
root=Path(os.environ["P1H_R02"])
folder=root/"compacta"
g5=json.loads((root/"revisao/1x5/geometria.json").read_text())
g2=json.loads((root/"revisao/1x2/geometria.json").read_text())
routes=json.loads((folder/"caminhos.json").read_text())
routes.update(json.loads((folder/"enlaces.json").read_text()))
zf,zb=-10.0,-11.52
cx=dict(INF=PIN-PASSO*2.5,SUP=PIN+PASSO*2.5,RAIZ=PIN)
old=App.openDocument(str(mech/"03_Antena_montada.FCStd"))
d=App.newDocument("P1H_R02_compacta")


def put(name,shape):
    assert shape.isValid() and not shape.isNull(),name
    o=d.addObject("Part::Feature",name);o.Shape=shape
    return o


def flat(points, x, z):
    pts=[V(x+px,py,z) for px,py in points]
    return Part.Face(Part.makePolygon(pts+[pts[0]]))


def core_geom(half):
    x=cx[half]
    g=g2 if half=="RAIZ" else g5
    sh=m.bx(x-19.5,-39,zb,39,78,1.52)
    if "janela" in g:
        sh=sh.cut(flat(g["janela"],x,zb).extrude(V(0,0,1.52)))
    for name,px,y in g["ports"]:
        sh=sh.cut(m.cz(x+px,y,zb-.1,.5,1.72))
    for pol,v in g["copper"].items():
        trace=flat(v,x,zf)
        for name,px,y in g["ports"]:
            if name[0]==pol:trace=trace.cut(m.cz(x+px,y,zf-.1,.5,.2))
        put("RF_"+half+"_"+pol,trace)
    return sh


def rail(half,side):
    x=cx[half]+side*21.5
    sh=m.bx(x-4,-41,-14,8,82,12)
    edge=cx[half]+side*19.75
    sh=sh.cut(m.bx(edge if side<0 else edge-4,-39.3,-11.75,4,78.6,1.75))
    for y in [-50,17.5]:
        sh=sh.cut(m.bx(x-4.1,y,-8.5,8.2,32.5,6.6))
    # Os dois trilhos internos da placa inferior liberam a passagem da ponte de laminado.
    if (half=="INF" and side==1) or (half=="RAIZ" and side==-1):
        sh=sh.cut(m.bx(x-4.1,29.7,-11.75,8.2,9.6,1.75))
    if half=="RAIZ":
        sh=sh.cut(m.oval(PIN+side*PASSO/2,4.9,-3.45,1.6))
        for y in [-PIN,PIN]:sh=sh.cut(m.cz(PIN+side*PASSO/2,y,-14.1,2.6,12.2))
    if half=="INF" and side==1:
        for y in [-11,11]:sh=sh.cut(m.cz(m.SUP_X[1],y,-4.8,3.0,3.0))
    for y in ([-11,11] if half=="RAIZ" else [-6.5,6.5]):
        sh=sh.cut(m.cz(x,y,-10.5,1.025,8.6))
    return sh


obstacles={}
for group in [old.Apoios_POM,old.Radiadores,old.Passagens,old.Entradas_N,old.Fixadores]:
    for o in group.Group:
        if o.Name.startswith("Par_trilho"):continue
        sh=o.Shape
        if o.Name=="Berco_2":
            for y in [-6.5,6.5]:sh=sh.cut(m.cz(cx["INF"]+21.5,y,-.1,3.0,2.9))
        put(o.Name,sh)
        if group != old.Radiadores or o.Name.startswith("Nucleo"):obstacles[o.Name]=sh
chassis=old.Chapa_Aluminio_2mm.Shape
for half in ["INF","SUP"]:
    for side in [-1,1]:
        for y in [-6.5,6.5]:
            chassis=chassis.cut(m.cz(cx[half]+side*21.5,y,-2.1,1.4,2.2))
put("Refletor_R02",chassis);obstacles["Refletor"]=chassis
lower=core_geom("INF");upper=core_geom("SUP");central=core_geom("RAIZ")
bridge=m.bx(cx["INF"]+19.5,30,zb,cx["RAIZ"]-cx["INF"]-39,9,1.52)
lower=m.union([lower,central,bridge])
assert len(lower.Solids)==1 and len(upper.Solids)==1
for name,shape in [("PCB_inferior_com_raiz",lower),("PCB_superior",upper)]:
    put(name,shape);obstacles[name]=shape
for half in cx:
    for side in [-1,1]:
        name="Trilho_"+half+("_E" if side<0 else "_D")
        sh=rail(half,side);put(name,sh);obstacles[name]=sh
        assert max(sh.common(other).Volume for other in [lower,upper,chassis])<1e-5,name
        for idx,y in enumerate(([-11,11] if half=="RAIZ" else [-6.5,6.5])):
            bolt=m.screw(cx[half]+side*21.5,y,0,-1,8)
            key=name+"_par_"+str(idx);put(key,bolt);obstacles[key]=bolt
for pol in "AB":
    sh=old.getObject("Bobina_"+pol).Shape.copy()
    sh.translate(V(0,0,zb-m.DIV_B));put("Bobina_"+pol,sh)
cables={}
wires={}
lengths={}
for name,edges in routes.items():
    wire=m.wire_from_data(edges)
    wires[name]=wire
    lengths[name]=wire.Length
    sh=m.tube(wire,R_CABO)
    put(name,sh);cables[name]=sh
errors=[]
for key,sh in obstacles.items():
    if not (key.startswith("Trilho_") or key=="Berco_2"):continue
    for other,s in obstacles.items():
        if key==other or not sh.BoundBox.intersect(s.BoundBox):continue
        v=sh.common(s).Volume
        if v>1e-4:errors.append([key,other,round(v,5)])
for key,sh in cables.items():
    for other,s in list(obstacles.items())+[(n,q) for n,q in cables.items() if n<key]:
        if not sh.BoundBox.intersect(s.BoundBox):continue
        v=sh.common(s).Volume
        if v>1e-4:errors.append([key,other,round(v,5)])
for name in [k for k in cables if k.startswith(("INF_","SUP_"))]:
    assert abs(lengths[name]-130)<1e-5
for name in [k for k in cables if k.startswith("TR_")]:
    assert abs(lengths[name]-132)<1e-5
assert abs(lengths["IN_A"]-lengths["IN_B"])<1e-6
dist,a,b=min((w1.distToShape(w2)[0]-2*R_CABO,a,b)
             for (a,w1),(b,w2) in combinations(wires.items(),2))
assert dist>.39,(a,b,dist)
out=dict(comprimentos_mm={k:round(v,6) for k,v in lengths.items()},interferencias_mm3=errors,
         placas_fisicas=2,raio_eixo_mm=4.4,folga_minima_entre_capas_mm=round(dist,6),par_critico=[a,b])
(folder/"verificacao_cad.json").write_text(json.dumps(out,indent=2),encoding="utf8")
print("INTERFERENCIAS",errors)
assert not errors,errors
d.recompute()
d.saveAs(str(folder/"P1H_R02_compacta.FCStd"))
