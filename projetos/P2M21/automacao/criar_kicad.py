"""Tres PCBs nativas, mesma arte e parametros do CAD EM P2M21."""
import json,math
from pathlib import Path
import pcbnew as k
repo=Path(__file__).resolve().parents[3]
root=Path('D:/dev/EMBRAER/P2M21/R00_Concepcao');out=root/'kicad';out.mkdir(exist_ok=True)
art=json.loads((repo/'automacao/P1H/KiCad_Antenas/elemento_hfss.json').read_text())
mm=k.FromMM
def xy(x,y):return k.VECTOR2I(mm(x),mm(y))
def at(x,y):return xy(x+110,70-y)
def net(b,name):
    n=k.NETINFO_ITEM(b,name);b.Add(n);return n
def poly(b,layer,coords,holes=(),n=None,dx=0,dy=0):
    s=k.PCB_SHAPE(b);s.SetShape(k.SHAPE_T_POLY);p=k.SHAPE_POLY_SET();p.NewOutline()
    for x,y in coords:p.Append(at(x+dx,y+dy))
    for hole in holes:
        h=p.NewHole()
        for x,y in hole:p.Append(at(x+dx,y+dy),0,h)
    if holes:p.Fracture()
    s.SetPolyShape(p);s.SetLayer(layer);s.SetWidth(0);s.SetFilled(True)
    if n:s.SetNet(n)
    b.Add(s)
def circle(x,y,r,count=64):return [(x+r*math.cos(i*2*math.pi/count),y+r*math.sin(i*2*math.pi/count)) for i in range(count)]
def outline(b,w,h):
    pts=[(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]
    for p,q in zip(pts,pts[1:]+pts[:1]):
        e=k.PCB_SHAPE(b);e.SetShape(k.SHAPE_T_SEGMENT);e.SetLayer(k.Edge_Cuts)
        e.SetStart(at(*p));e.SetEnd(at(*q));e.SetWidth(mm(.05));b.Add(e)
def foot(b,name,x,y):
    f=k.FOOTPRINT(b);f.SetReference(name);f.SetValue(name);f.SetPosition(at(x,y))
    f.Reference().SetVisible(False);f.Value().SetVisible(False);b.Add(f);return f
def pad(f,num,x,y,size,n=None,drill=None,layer=None,npth=False):
    p=k.PAD(f);p.SetNumber(num);p.SetShape(k.PAD_SHAPE_CIRCLE);p.SetPosition(at(x,y));p.SetSize(xy(size,size))
    p.SetAttribute(k.PAD_ATTRIB_NPTH if npth else k.PAD_ATTRIB_PTH if drill else k.PAD_ATTRIB_SMD)
    if drill:p.SetDrillSize(xy(drill,drill))
    ls=k.LSET.AllCuMask() if layer is None else k.LSET()
    if layer is not None:ls.AddLayer(layer)
    p.SetLayerSet(ls)
    if n:p.SetNet(n)
    f.Add(p)
def text(b,s,x,y):
    t=k.PCB_TEXT(b);t.SetText(s);t.SetLayer(k.F_Fab);t.SetPosition(at(x,y));t.SetTextSize(xy(.8,.8));t.SetTextThickness(mm(.12));b.Add(t)
def save(b,name,h,material,er,td):
    dest=out/name;dest.mkdir(exist_ok=True);fn=dest/(name+'.kicad_pcb')
    b.GetDesignSettings().SetBoardThickness(mm(h+.09));k.SaveBoard(str(fn),b)
    layers=[]
    for s in ['F.SilkS','F.Paste','F.Mask','F.Cu','dielectric 1','B.Cu','B.Mask','B.Paste','B.SilkS']:
        typ='core' if s=='dielectric 1' else 'copper' if s.endswith('.Cu') else 'Top Solder Mask' if s=='F.Mask' else 'Bottom Solder Mask' if s=='B.Mask' else 'Top Silk Screen' if s=='F.SilkS' else 'Bottom Silk Screen' if s=='B.SilkS' else 'Top Solder Paste' if s=='F.Paste' else 'Bottom Solder Paste'
        extra=f' (thickness {h}) (material "{material}") (epsilon_r {er}) (loss_tangent {td})' if s=='dielectric 1' else ' (thickness 0.035)' if s.endswith('.Cu') else ' (thickness 0.01)' if s.endswith('.Mask') else ''
        layers.append(f'(layer "{s}" (type "{typ}"){extra})')
    st='(stackup '+' '.join(layers)+' (copper_finish "ENIG") (dielectric_constraints yes))'
    fn.write_text(fn.read_text(encoding='utf8').replace('(setup\n','(setup\n'+st+'\n',1),encoding='utf8')
    bb=k.LoadBoard(str(fn));k.SaveBoard(str(fn),bb)
    project=fn.with_suffix('.kicad_pro');cfg=json.loads(project.read_text(encoding='utf8'))
    for nc in cfg['net_settings']['classes']:nc['clearance']=.15
    cfg['board']['design_settings']['rules']['min_clearance']=.15
    cfg['board']['design_settings']['rule_severities']['solder_mask_bridge']='warning'
    project.write_text(json.dumps(cfg,indent=2),encoding='utf8');print('KICAD_OK',name,len(bb.GetFootprints()))

b=k.BOARD();outline(b,186.1125,68.3125)
for row in range(4):
    for col,y in enumerate((-20,20)):
        i=row*2+col;x=(row-1.5)*52.6;nets={s:net(b,f'E{i+1:02}_{s}') for s in sorted({p['net'] for p in art['lands']})}
        for p in art['lands']:poly(b,k.F_Cu if p['layer']=='F' else k.B_Cu,p['outer'],p['holes'],nets[p['net']],x,y)
        for layer in (k.F_Mask,k.B_Mask):poly(b,layer,[(-13.90625,-13.90625),(13.90625,-13.90625),(13.90625,13.90625),(-13.90625,13.90625)],dx=x,dy=y)
        for pol,(px,py) in art['ports'].items():
            f=foot(b,f'J{2*i+1+(pol=="B")}',x+px,y+py)
            pad(f,'1',x+px,y+py,1.2,nets['SIG_'+pol],.85)
            pad(f,'2',x+px+1.05,y+py,.25,nets['RET_'+pol],layer=k.B_Cu)
        for px,py in art['vias']:
            v=k.PCB_VIA(b);v.SetPosition(at(x+px,y+py));v.SetWidth(mm(.726));v.SetDrill(mm(.40));v.SetNet(nets['SIG_B']);b.Add(v)
        text(b,f'E{i+1:02} A/B',x-7,y+11.5)
save(b,'P2M21_Modulo_2x4',.76,'RO4350B',3.66,.0037)
for n in (4,8):
    g=json.loads((root/f'divisor_1x{n}/geometria.json').read_text());b=k.BOARD();outline(b,39,78)
    nets={s:net(b,s) for s in ('A','B','GND')}
    holes=[circle(x,y,1.515) for _,x,y in g['ports']]+[circle(x,y,2.25) for x,y in g['montagem_furos']]
    poly(b,k.B_Cu,[(-19,-38.5),(19,-38.5),(19,38.5),(-19,38.5)],holes,nets['GND'])
    for pol,coords in g['copper'].items():
        poly(b,k.F_Cu,coords,n=nets[pol]);poly(b,k.F_Mask,coords)
    for i,(name,x,y) in enumerate(g['ports'],1):
        f=foot(b,'J%d'%i,x,y);pad(f,'1',x,y,1.46,nets[name[0]],1.05)
        pad(f,'2',x+1.85,y,.3,nets['GND'],layer=k.B_Cu)
        poly(b,k.B_Mask,circle(x,y,2.3));text(b,name,x+1,y+2.8)
    for i,(x,y) in enumerate(g['montagem_furos'],1):pad(foot(b,'H%d'%i,x,y),'',x,y,3.2,drill=3.2,npth=True)
    save(b,f'P2M21_Duplo_1x{n}',1.52,'ZYF300CA-C',2.94,.0016)
