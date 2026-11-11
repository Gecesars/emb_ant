"""C07 HFSS -> KiCad 10, sem alterar cobre, contorno ou interfaces coaxiais.

Executar com Python do KiCad. Furos sao NPTH: o modelo tem pinos solidos,
nao barris metalizados. Pads de rede ficam dentro da arte ja existente.
"""
from pathlib import Path
import json, math, hashlib
import pcbnew as k

REPO=Path(__file__).resolve().parents[3]
SRC=REPO/'projetos/P2S13/divisor_duplo_1x3_correcao/c07_centro'
OUT=REPO/'projetos/P2S13/kicad/divisor_duplo_1x3_C07'
OUT.mkdir(parents=True,exist_ok=True)
NAME='divisor_duplo_1x3_C07'
cfg=json.loads((SRC/'configuracao.json').read_text(encoding='utf8'))
assert cfg['board']==[220,64] and cfg['h']==1.52 and cfg['cu']==.035
assert not cfg.get('mask_windows') and not cfg.get('shield') and not cfg['resistores']
b=k.BOARD(); mm=k.FromMM; nets={}
for name in ['SIG_A','SIG_B','GND']:
    n=k.NETINFO_ITEM(b,name);b.Add(n);nets[name]=n
def pos(x,y):return k.VECTOR2I(mm(120+x),mm(42-y))
def unpos(v):return [k.ToMM(v.x)-120,42-k.ToMM(v.y)]
def poly(layer,coords,holes=(),net=None):
    ps=k.SHAPE_POLY_SET();ps.NewOutline()
    for xy in coords:ps.Append(pos(*xy))
    for pts in holes:
        hole=ps.NewHole()
        for xy in pts:ps.Append(pos(*xy),0,hole)
    if holes:ps.Fracture()
    s=k.PCB_SHAPE(b);s.SetShape(k.SHAPE_T_POLY);s.SetPolyShape(ps)
    s.SetLayer(layer);s.SetWidth(0);s.SetFilled(True)
    if net:s.SetNet(nets[net])
    b.Add(s)
def label(text,x,y):
    s=k.PCB_TEXT(b);s.SetText(text);s.SetPosition(pos(x,y));s.SetLayer(k.F_Fab)
    s.SetTextSize(k.VECTOR2I(mm(.9),mm(.9)));s.SetTextThickness(mm(.12));b.Add(s)
outline=[[-110,-32],[110,-32],[110,32],[-110,32]]
for a,c in zip(outline,outline[1:]+outline[:1]):
    s=k.PCB_SHAPE(b);s.SetShape(k.SHAPE_T_SEGMENT);s.SetLayer(k.Edge_Cuts)
    s.SetStart(pos(*a));s.SetEnd(pos(*c));s.SetWidth(mm(.05));b.Add(s)
for pol,data in cfg['signals'].items():poly(k.F_Cu,data['exterior'],data['holes'],'SIG_'+pol)
circles=[]
for p in cfg['portas']:
    circles.append([[p['x']+p['ro']*math.cos(i*math.tau/2048),p['y']+p['ro']*math.sin(i*math.tau/2048)] for i in range(2048)])
poly(k.B_Cu,outline,circles,'GND')
for layer in [k.F_Mask,k.B_Mask]:poly(layer,outline)
for i,ip in enumerate(cfg['portas'],1):
    f=k.FOOTPRINT(b);f.SetReference('J'+str(i));f.SetValue(ip['name']+'_COAX_SOLDADO')
    f.SetPosition(pos(ip['x'],ip['y']));f.Reference().SetVisible(False);f.Value().SetVisible(False)
    f.SetAttributes(k.FP_EXCLUDE_FROM_BOM|k.FP_EXCLUDE_FROM_POS_FILES);b.Add(f)
    hole=k.PAD(f);hole.SetNumber('');hole.SetPosition(pos(ip['x'],ip['y']))
    hole.SetShape(k.PAD_SHAPE_CIRCLE);hole.SetSize(k.VECTOR2I(mm(2*ip['ri']),mm(2*ip['ri'])))
    hole.SetDrillSize(hole.GetSize());hole.SetAttribute(k.PAD_ATTRIB_NPTH);hole.SetLayerSet(k.LSET.AllCuMask());f.Add(hole)
    # Anchors carry net connectivity, wholly contained in pre-existing copper.
    sgn=1 if ip['name'].endswith('_A') else -1
    if ip['name'].startswith('IN'):anchor=[ip['x'],ip['y']+sgn]
    else:
        path=next(t['points'] for t in cfg['traces'] if t['name']==ip['name'][-1]+'_O'+ip['name'][1])
        dx,dy=path[-2][0]-ip['x'],path[-2][1]-ip['y'];length=math.hypot(dx,dy)
        anchor=[ip['x']+dx/length,ip['y']+dy/length]
    for number,net,layer,x,y,diam in [('1','SIG_'+ip['name'][-1],k.F_Cu,*anchor,.25),('2','GND',k.B_Cu,ip['x']+1.8,ip['y'],.4)]:
        p=k.PAD(f);p.SetNumber(number);p.SetPosition(pos(x,y));p.SetShape(k.PAD_SHAPE_CIRCLE)
        p.SetSize(k.VECTOR2I(mm(diam),mm(diam)));p.SetAttribute(k.PAD_ATTRIB_SMD)
        layers=k.LSET();layers.AddLayer(layer);p.SetLayerSet(layers);p.SetNet(nets[net]);f.Add(p)
    label(ip['name'],ip['x'],ip['y']+sgn*4)
label('C07 | ZYF300CA-C core 1.52 mm | Cu 35 um | ENIG | SEM MASCARA',0,28)
label('PRELIMINAR - GEOMETRIA HFSS PRESERVADA - REQUER DFM ESPECIAL',0,-28)
b.GetDesignSettings().SetBoardThickness(mm(1.59))
title=b.GetTitleBlock();title.SetTitle('P2S13 - Divisor duplo 1:3 C07')
title.SetRevision('C07 / KiCad R01');title.SetDate('2026-11-11')
title.SetComment(0,'NPTH 0.9195 mm; antipads B.Cu 3.03 mm; ground ate a borda')
fn=OUT/(NAME+'.kicad_pcb');k.SaveBoard(str(fn),b)
stack='''(stackup
 (layer "F.SilkS" (type "Top Silk Screen"))
 (layer "F.Paste" (type "Top Solder Paste"))
 (layer "F.Mask" (type "Top Solder Mask") (thickness 0))
 (layer "F.Cu" (type "copper") (thickness 0.035))
 (layer "dielectric 1" (type "core") (thickness 1.52) (material "ZYF300CA-C") (epsilon_r 2.94) (loss_tangent 0.0016))
 (layer "B.Cu" (type "copper") (thickness 0.035))
 (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0))
 (layer "B.Paste" (type "Bottom Solder Paste"))
 (layer "B.SilkS" (type "Bottom Silk Screen"))
 (copper_finish "ENIG") (dielectric_constraints yes))'''
raw=fn.read_text(encoding='utf8');assert '(stackup' not in raw
fn.write_text(raw.replace('(setup\n','(setup\n'+stack+'\n',1),encoding='utf8')
loaded=k.LoadBoard(str(fn));k.SaveBoard(str(fn),loaded)
pro=fn.with_suffix('.kicad_pro');settings=json.loads(pro.read_text(encoding='utf8'))
rules=settings['board']['design_settings']['rules']
rules['min_clearance']=.15;rules['min_copper_edge_clearance']=.2;rules['min_hole_clearance']=.2
for nc in settings['net_settings']['classes']:nc['clearance']=.15
settings['board']['design_settings']['rule_severities']['solder_mask_bridge']='warning'
pro.write_text(json.dumps(settings,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
e=dict(kicad_version=k.Version(),transformacao='KiCad X=120+HFSS X; KiCad Y=42-HFSS Y (mm)',
    source_sha256=hashlib.sha256((SRC/'configuracao.json').read_bytes()).hexdigest(),
    native_sha256=hashlib.sha256(fn.read_bytes()).hexdigest(),drawings=[],pads=[],outline=[],mask=[],tracks=len(loaded.GetTracks()))
for item in loaded.GetDrawings():
    if not isinstance(item,k.PCB_SHAPE):continue
    layer=item.GetLayer()
    if layer==k.Edge_Cuts:e['outline'].append([unpos(item.GetStart()),unpos(item.GetEnd())]);continue
    if layer not in (k.F_Cu,k.B_Cu,k.F_Mask,k.B_Mask):continue
    ps=item.GetPolyShape();contours=[]
    for i in range(ps.OutlineCount()):
        line=ps.COutline(i);contours.append([unpos(line.CPoint(j)) for j in range(line.PointCount())])
    rec=dict(layer=item.GetLayerName(),net=item.GetNetname(),contours=contours)
    e['mask' if layer in (k.F_Mask,k.B_Mask) else 'drawings'].append(rec)
for f in loaded.GetFootprints():
    for p in f.Pads():e['pads'].append(dict(ref=f.GetReference(),value=f.GetValue(),number=p.GetNumber(),net=p.GetNetname(),
        center=unpos(p.GetPosition()),diameter=k.ToMM(p.GetSize().x),drill=k.ToMM(p.GetDrillSize().x),
        npth=p.GetAttribute()==k.PAD_ATTRIB_NPTH,layers=[a for a,l in [('F.Cu',k.F_Cu),('B.Cu',k.B_Cu)] if p.IsOnLayer(l)]))
(OUT/'leitura_kicad.json').write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'placa':str(fn),'pads':len(e['pads']),'versao':k.Version()},indent=2))
