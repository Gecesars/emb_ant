"""Build separate and continuous Rogers laminates using the same P1H copper artwork."""
from pathlib import Path
import json
import pcbnew as k

root=Path(__file__).resolve().parent
g=json.loads((root/"elemento_hfss.json").read_text())
mm=k.FromMM
def xy(x,y):
    return k.VECTOR2I(mm(x),mm(y))
def at(x,y):
    return xy(x+22,40-y)

def create_board(name,count):
    board=k.BOARD()
    board.GetDesignSettings().SetBoardThickness(mm(.85))
    w,h=g["outline"]; pitch=g["pitch"]
    def polygon(layer,outer,holes=(),net=None,dx=0):
        s=k.PCB_SHAPE(board);s.SetShape(k.SHAPE_T_POLY)
        p=k.SHAPE_POLY_SET();p.NewOutline()
        for x,y in outer:p.Append(at(dx+x,y))
        for hole in holes:
            idx=p.NewHole()
            for x,y in hole:p.Append(at(dx+x,y),0,idx)
        if holes:p.Fracture()
        s.SetPolyShape(p);s.SetLayer(layer);s.SetWidth(0);s.SetFilled(True)
        if net:s.SetNet(net)
        board.Add(s)
    outline=[(-w/2,-h/2),((count-1)*pitch+w/2,-h/2),((count-1)*pitch+w/2,h/2),(-w/2,h/2)]
    for p,q in zip(outline,outline[1:]+outline[:1]):
        edge=k.PCB_SHAPE(board);edge.SetShape(k.SHAPE_T_SEGMENT);edge.SetLayer(k.Edge_Cuts)
        edge.SetStart(at(*p));edge.SetEnd(at(*q));edge.SetWidth(mm(.05));board.Add(edge)
    for i in range(count):
        dx=pitch*i
        def point(x,y):return at(dx+x,y)
        nets={}
        for label in sorted({d["net"] for d in g["lands"]}):
            net=k.NETINFO_ITEM(board,f"E{i+1:02}_{label}");board.Add(net);nets[label]=net
        for d in g["lands"]:
            polygon(k.F_Cu if d["layer"]=="F" else k.B_Cu,d["outer"],d["holes"],nets[d["net"]],dx)
        # Keep the antenna laminate exposed above the full RF area, including gaps in its copper.
        a=w/2-.25;b=h/2-.25
        for layer in (k.F_Mask,k.B_Mask):
            polygon(layer,[(-a,-b),(a,-b),(a,b),(-a,b)],dx=dx)
        for pol,(x,y) in g["ports"].items():
            f=k.FOOTPRINT(board);f.SetReference(f"J{2*i+1+(pol=='B')}")
            f.SetValue(f"P1H_{pol}_SONDA");f.SetPosition(point(x,y))
            f.Reference().SetVisible(False);f.Value().SetVisible(False);board.Add(f)
            pin=k.PAD(f);pin.SetNumber("1");pin.SetShape(k.PAD_SHAPE_CIRCLE)
            pin.SetAttribute(k.PAD_ATTRIB_PTH);pin.SetPosition(point(x,y));pin.SetNet(nets["SIG_"+pol])
            pin.SetDrillSize(xy(.85,.85));pin.SetSize(xy(1.20,1.20));pin.SetLayerSet(k.LSET.AllCuMask());f.Add(pin)
            # Anchor for the coax shield on its own RF quadrant, physically inside the annulus.
            ret=k.PAD(f);ret.SetNumber("2");ret.SetShape(k.PAD_SHAPE_CIRCLE);ret.SetAttribute(k.PAD_ATTRIB_SMD)
            ret.SetPosition(point(x+1.05,y));ret.SetSize(xy(.25,.25));layers=k.LSET();layers.AddLayer(k.B_Cu)
            ret.SetLayerSet(layers);ret.SetNet(nets["RET_"+pol]);f.Add(ret)
        for x,y in g["vias"]:
            via=k.PCB_VIA(board);via.SetPosition(point(x,y));via.SetWidth(mm(.726));via.SetDrill(mm(.40))
            via.SetNet(nets["SIG_B"]);board.Add(via)
        def label(s,x,y):
            text=k.PCB_TEXT(board);text.SetText(s);text.SetLayer(k.F_Fab);text.SetPosition(point(x,y))
            text.SetTextSize(xy(.7,.7));text.SetTextThickness(mm(.1));board.Add(text)
        for pol,(x,y) in g["ports"].items():label(pol,x+1.5,y)
        label(f"P1H {i+1:02}",-8,11.5)
    dest=root/name;dest.mkdir(exist_ok=True)
    filename=dest/(name+".kicad_pcb");k.SaveBoard(str(filename),board)
    text=filename.read_text(encoding="utf8")
    stackup='''(stackup
      (layer "F.SilkS" (type "Top Silk Screen") (color "White"))
      (layer "F.Paste" (type "Top Solder Paste"))
      (layer "F.Mask" (type "Top Solder Mask") (color "Green") (thickness 0.01))
      (layer "F.Cu" (type "copper") (thickness 0.035))
      (layer "dielectric 1" (type "core") (thickness 0.76) (material "Rogers RO4350B") (epsilon_r 3.66) (loss_tangent 0.0037))
      (layer "B.Cu" (type "copper") (thickness 0.035))
      (layer "B.Mask" (type "Bottom Solder Mask") (color "Green") (thickness 0.01))
      (layer "B.Paste" (type "Bottom Solder Paste"))
      (layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
      (copper_finish "ENIG") (dielectric_constraints yes))'''
    filename.write_text(text.replace("(setup\n","(setup\n"+stackup+"\n",1),encoding="utf8")
    loaded=k.LoadBoard(str(filename));k.SaveBoard(str(filename),loaded)
    corners=[d.GetStart() for d in loaded.GetDrawings() if d.GetLayer()==k.Edge_Cuts]
    width=k.ToMM(max(v.x for v in corners)-min(v.x for v in corners))
    height=k.ToMM(max(v.y for v in corners)-min(v.y for v in corners))
    assert abs(width-((count-1)*pitch+w))<.001 and abs(height-h)<.001
    assert len(loaded.GetFootprints())==2*count and len(loaded.GetTracks())==2*count
    assert "Rogers RO4350B" in filename.read_text()
    project=filename.with_suffix(".kicad_pro")
    config=json.loads(project.read_text(encoding="utf8"))
    for netclass in config["net_settings"]["classes"]:
        if netclass["name"]=="Default":netclass["clearance"]=.15
    settings=config["board"]["design_settings"]
    settings["rules"]["min_clearance"]=.15
    settings["rule_severities"]["solder_mask_bridge"]="warning"
    project.write_text(json.dumps(config,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(name,width,height)

for name,count in [("P1H_Individual",1),("P1H_Coluna_10",10)]:
    create_board(name,count)
