"""Layout KiCad 10. Mesmo cobre, vias, resistores e portas do FEM."""
import json,math,os
from pathlib import Path
import pcbnew as k
root=Path(os.environ.get("P1H_RADIAL_DIR", Path(__file__).resolve().parent))
g=json.loads((root/"geometria.json").read_text())
board=k.BOARD()
def mm(x): return k.FromMM(x)
def size(w,h): return k.VECTOR2I(mm(w),mm(h))
def pos(x,y): return size(g.get("origem_x",80)+x,65-y)
reverse=g.get("sinal_no_verso",False)
signal_cu,ground_cu=(k.B_Cu,k.F_Cu) if reverse else (k.F_Cu,k.B_Cu)
signal_mask,ground_mask=(k.B_Mask,k.F_Mask) if reverse else (k.F_Mask,k.B_Mask)
def layers(*indices):
    ls=k.LSET()
    for index in indices: ls.AddLayer(index)
    return ls
settings=board.GetDesignSettings()
settings.SetBoardThickness(mm(1.61))
nets={}
for net in ["GND"]+["POL_"+pol for pol in g["copper"]]:
    item=k.NETINFO_ITEM(board,net);board.Add(item);nets[net]=item
def poly(layer,points,net=None):
    shape=k.PCB_SHAPE(board)
    shape.SetShape(k.SHAPE_T_POLY)
    ps=k.SHAPE_POLY_SET();ps.NewOutline()
    for x,y in points:ps.Append(pos(x,y))
    shape.SetPolyShape(ps);shape.SetFilled(True);shape.SetWidth(0);shape.SetLayer(layer)
    if net: shape.SetNet(nets[net])
    board.Add(shape)
def fp(ref,value,x,y):
    f=k.FOOTPRINT(board);f.SetReference(ref);f.SetValue(value);f.SetPosition(pos(x,y))
    f.Reference().SetVisible(False);f.Value().SetVisible(False)
    board.Add(f);return f
def pad(f,num,x,y,w,dy,net,through=False,paste=False):
    q=k.PAD(f);q.SetNumber(num);q.SetNet(nets[net]);q.SetSize(size(w,dy));q.SetPosition(pos(x,y))
    if through:
        q.SetShape(k.PAD_SHAPE_CIRCLE);q.SetAttribute(k.PAD_ATTRIB_PTH);q.SetDrillSize(size(.3,.3))
        q.SetLayerSet(layers(k.F_Cu,k.B_Cu,k.F_Mask,k.B_Mask))
    else:
        q.SetAttribute(k.PAD_ATTRIB_SMD);q.SetShape(k.PAD_SHAPE_RECT)
        q.SetLayerSet(layers(k.F_Cu,k.F_Mask,*([k.F_Paste] if paste else [])))
    f.Add(q)
def text(s,x,y,scale=.8,back=False):
    t=k.PCB_TEXT(board);t.SetText(s);t.SetPosition(pos(x,y));t.SetLayer(k.B_SilkS if back else k.F_SilkS);t.SetMirrored(back);t.SetTextSize(size(scale,scale));t.SetTextThickness(mm(.13));board.Add(t)
hx=g["half_x"];hy=g["half_y"]
def corners(x,y):return [(-x,-y),(x,-y),(x,y),(-x,y)]
outline=g.get("outline",corners(hx,hy))
for loop in [outline]+([g["janela"]] if "janela" in g else []):
    for a,b in zip(loop,loop[1:]+loop[:1]):
        e=k.PCB_SHAPE(board);e.SetShape(k.SHAPE_T_SEGMENT);e.SetLayer(k.Edge_Cuts);e.SetWidth(mm(.05));e.SetStart(pos(*a));e.SetEnd(pos(*b));board.Add(e)
for pol,pts in g["copper"].items():
    poly(signal_cu,pts,"POL_"+pol);poly(signal_mask,pts)
z=k.ZONE(board);z.SetNet(nets["GND"]);z.SetLayer(ground_cu);z.SetPadConnection(k.ZONE_CONNECTION_FULL)
z.SetLocalClearance(mm(.785));z.SetMinThickness(mm(.10))
z.Outline().NewOutline()
for x,y in g.get("outline_gnd",corners(hx-.52,hy-.52)):z.Outline().Append(pos(x,y))
board.Add(z)
def maskring(x,y):
    shp=k.PCB_SHAPE(board);shp.SetShape(k.SHAPE_T_POLY);shp.SetLayer(ground_mask)
    ps=k.SHAPE_POLY_SET();ps.NewOutline()
    for n in range(48):
        a=math.tau*n/48;ps.Append(pos(x+2.24*math.cos(a),y+2.24*math.sin(a)))
    hole=ps.NewHole()
    for n in range(48):
        a=-math.tau*n/48;ps.Append(pos(x+1.515*math.cos(a),y+1.515*math.sin(a)),0,hole)
    ps.Fracture();shp.SetPolyShape(ps);shp.SetFilled(True);shp.SetWidth(0);board.Add(shp)
for idx,(name,x,y) in enumerate(g["ports"],1):
    f=fp("J"+str(idx),name+"_UT141C",x,y)
    net=g.get("port_net",{}).get(name,name[0])
    q=k.PAD(f);q.SetNumber("1");q.SetNet(nets["POL_"+net]);q.SetSize(size(1.46,1.46))
    q.SetShape(k.PAD_SHAPE_CIRCLE);q.SetAttribute(k.PAD_ATTRIB_PTH);q.SetDrillSize(size(1.,1.));q.SetPosition(pos(x,y))
    q.SetLayerSet(layers(k.F_Cu,k.B_Cu,k.F_Mask,k.B_Mask));f.Add(q)
    for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        q=k.PAD(f);q.SetNumber("2");q.SetNet(nets["GND"]);q.SetSize(size(.35,.35))
        q.SetShape(k.PAD_SHAPE_CIRCLE);q.SetAttribute(k.PAD_ATTRIB_SMD);q.SetPosition(pos(x+1.87*dx,y+1.87*dy))
        q.SetLayerSet(layers(ground_cu,ground_mask));f.Add(q)
    maskring(x,y)
    cy=-19.25 if name.startswith("A") else 19.25
    if name in g.get("rotulos",{}):
        txt,tx,ty=g["rotulos"][name];text(txt,tx,ty,.85,back=not reverse)
    elif name.endswith("IN"):text(name.replace("_"," "),x,y+3.8,.9,back=True)
    else:
        a=math.atan2(y-cy,x)
        text(name,x+3.82*math.cos(a)+{"A6":1.6,"B5":-1.6}.get(name,0),y+3.82*math.sin(a),.85,back=True)
for j,(x,y) in enumerate(g.get("fixacao",[]),1):
    hole=fp("H"+str(j),"Fixacao_M2.5",x,y)
    q=k.PAD(hole);q.SetAttribute(k.PAD_ATTRIB_NPTH);q.SetShape(k.PAD_SHAPE_CIRCLE)
    q.SetSize(size(2.8,2.8));q.SetDrillSize(size(2.8,2.8));q.SetPosition(pos(x,y))
    q.SetLayerSet(layers(k.F_Cu,k.B_Cu,k.F_Mask,k.B_Mask));hole.Add(q)
for pts in g.get("mascara_emenda_gnd",[]):poly(ground_mask,pts)
text(g.get("legenda","P1H  2 x 1:10"),*g.get("legenda_xy",[0,36.5 if "janela" in g else 0]),1.1,back=reverse)
k.ZONE_FILLER(board).Fill(board.Zones())
path=root/(g.get("arquivo","Divisor_2x10_PTFE")+".kicad_pcb")
k.SaveBoard(str(path),board)
stackup = """(stackup
    (layer "F.SilkS" (type "Top Silk Screen") (color "White"))
    (layer "F.Paste" (type "Top Solder Paste"))
    (layer "F.Mask" (type "Top Solder Mask") (color "Green") (thickness 0.01))
    (layer "F.Cu" (type "copper") (thickness 0.035))
    (layer "dielectric 1" (type "core") (thickness 1.52) (material "ZYF300CA-C") (epsilon_r 2.94) (loss_tangent 0.0016))
    (layer "B.Cu" (type "copper") (thickness 0.035))
    (layer "B.Mask" (type "Bottom Solder Mask") (color "Green") (thickness 0.01))
    (layer "B.Paste" (type "Bottom Solder Paste"))
    (layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
    (copper_finish "ENIG") (dielectric_constraints yes))"""
source=path.read_text(encoding="utf-8")
if "material" in g:
    stackup=stackup.replace('ZYF300CA-C',g["material"]).replace('(epsilon_r 2.94)',f'(epsilon_r {g["dk"]})').replace('(loss_tangent 0.0016)',f'(loss_tangent {g["df"]})')
assert source.count("(setup\n")==1
path.write_text(source.replace("(setup\n","(setup\n"+stackup+"\n",1),encoding="utf-8")
loaded=k.LoadBoard(str(path))
k.SaveBoard(str(path),loaded)
assert g.get("material","ZYF300CA-C") in path.read_text(encoding="utf-8")
assert len(loaded.GetFootprints())==len(g["ports"])+len(g.get("fixacao",[])) and loaded.GetCopperLayerCount()==2
print("PCB",loaded.GetFootprints().__len__(),"footprints")





