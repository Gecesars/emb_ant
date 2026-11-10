"""Cria 4_elementos no KiCad 10 a partir da arte R13 C12, sem novo solve HFSS.

Executar com o Python distribuido com o KiCad. As figuras RF sao poligonos
editaveis com redes; pads e vias sao objetos eletricos nativos do KiCad.
"""
import hashlib
import json
from pathlib import Path
import pcbnew as k

REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / 'projetos/P2M21/quatro_elementos_casamento_banda/c12_raiz_intermediaria'
OUT = REPO / 'projetos/P2M21/kicad/4_elementos'
OUT.mkdir(parents=True, exist_ok=True)
g = json.loads((SOURCE / 'geometria.json').read_text(encoding='utf-8'))
assert not g['shorts'] and g['radiadores'] == 4
assert g['outline'] == [[-92., -35.], [92., -35.], [92., 35.], [-92., 35.]]
assert g['h'] == .76 and g['cu'] == .035 and g['pitch'] == 48
mm = k.FromMM
b = k.BOARD()
nets = {}
for name in sorted({x['net'] for x in g['lands']}):
    n = k.NETINFO_ITEM(b, name)
    b.Add(n)
    nets[name] = n


def pos(x, y):
    # HFSS X = eixo vertical; Y = horizontal. PCB apresentada em pe.
    return k.VECTOR2I(mm(80 + y), mm(110 - x))


def polygon(layer, coordinates, holes=(), net=None):
    p = k.SHAPE_POLY_SET()
    p.NewOutline()
    for x, y in coordinates:
        p.Append(pos(x, y))
    for points in holes:
        h = p.NewHole()
        for x, y in points:
            p.Append(pos(x, y), 0, h)
    if holes:
        p.Fracture()
    s = k.PCB_SHAPE(b)
    s.SetShape(k.SHAPE_T_POLY)
    s.SetPolyShape(p)
    s.SetLayer(layer)
    s.SetWidth(0)
    s.SetFilled(True)
    if net:
        s.SetNet(nets[net])
    b.Add(s)


def label(value, x, y):
    t = k.PCB_TEXT(b)
    t.SetText(value)
    t.SetPosition(pos(x, y))
    t.SetLayer(k.F_Fab)
    t.SetTextSize(k.VECTOR2I(mm(.8), mm(.8)))
    t.SetTextThickness(mm(.12))
    b.Add(t)


for a, c in zip(g['outline'], g['outline'][1:] + g['outline'][:1]):
    e = k.PCB_SHAPE(b)
    e.SetShape(k.SHAPE_T_SEGMENT)
    e.SetLayer(k.Edge_Cuts)
    e.SetStart(pos(*a))
    e.SetEnd(pos(*c))
    e.SetWidth(mm(.05))
    b.Add(e)
for land in g['lands']:
    geom = land['geometry']
    polygons = [geom['coordinates']] if geom['type'] == 'Polygon' else geom['coordinates']
    for coords in polygons:
        polygon(k.F_Cu if land['layer'] == 'F' else k.B_Cu, coords[0], coords[1:], land['net'])

# O HFSS nao tinha mascara. Abertura completa nas duas faces, sem serigrafia
# sobre o cobre. Toda identificacao fica em F.Fab (nao fabricacao).
for layer in (k.F_Mask, k.B_Mask):
    polygon(layer, g['outline'])

for x, y in g['vias']:
    v = k.PCB_VIA(b)
    v.SetPosition(pos(x, y))
    v.SetWidth(mm(.726))
    v.SetDrill(mm(.4))
    v.SetLayerPair(k.F_Cu, k.B_Cu)
    v.SetNet(nets['SIG_B'])
    b.Add(v)

for i, ip in enumerate(g['inputs'], 1):
    f = k.FOOTPRINT(b)
    f.SetReference('J' + str(i))
    f.SetValue('COAX_' + ip['name'] + '_UT141')
    f.SetPosition(pos(ip['x'], ip['y']))
    f.Reference().SetVisible(False)
    f.Value().SetVisible(False)
    f.SetAttributes(k.FP_EXCLUDE_FROM_BOM | k.FP_EXCLUDE_FROM_POS_FILES)
    b.Add(f)
    p = k.PAD(f)
    p.SetNumber('1')
    p.SetPosition(pos(ip['x'], ip['y']))
    p.SetShape(k.PAD_SHAPE_CIRCLE)
    p.SetSize(k.VECTOR2I(mm(1.6), mm(1.6)))
    p.SetDrillSize(k.VECTOR2I(mm(1.1), mm(1.1)))
    p.SetAttribute(k.PAD_ATTRIB_PTH)
    p.SetLayerSet(k.LSET.AllCuMask())
    p.SetNet(nets[ip['sig']])
    f.Add(p)
    # Pad de identificacao de rede inteiramente dentro da area RET ja simulada.
    p = k.PAD(f)
    p.SetNumber('2')
    p.SetPosition(pos(ip['x'] + 2.1, ip['y']))
    p.SetShape(k.PAD_SHAPE_CIRCLE)
    p.SetSize(k.VECTOR2I(mm(.4), mm(.4)))
    p.SetAttribute(k.PAD_ATTRIB_SMD)
    layers = k.LSET()
    layers.AddLayer(k.B_Cu)
    p.SetLayerSet(layers)
    p.SetNet(nets[ip['ret']])
    f.Add(p)
    label('J%d / %s' % (i, ip['name']), ip['x'] - 4, ip['y'])

label('4_elementos | R13 C12 | RO4350B 0.76 mm', 87, 3.5)
label('SEM MASCARA | ENIG | Cu 35 um', -87, 3.5)
b.GetDesignSettings().SetBoardThickness(mm(.83))
title = b.GetTitleBlock()
title.SetTitle('4_elementos - quatro radiadores verticais / dois divisores 1:4')
title.SetRevision('R01 / arte HFSS R13 C12')
title.SetDate('2026-11-10')
title.SetComment(0, '48 mm entre centros; duas entradas A/B; sem mascara RF')
fn = OUT / '4_elementos.kicad_pcb'
k.SaveBoard(str(fn), b)
raw = fn.read_text(encoding='utf-8')
stack = '''(stackup
 (layer "F.SilkS" (type "Top Silk Screen"))
 (layer "F.Paste" (type "Top Solder Paste"))
 (layer "F.Mask" (type "Top Solder Mask") (thickness 0))
 (layer "F.Cu" (type "copper") (thickness 0.035))
 (layer "dielectric 1" (type "core") (thickness 0.76) (material "RO4350B") (epsilon_r 3.66) (loss_tangent 0.0037))
 (layer "B.Cu" (type "copper") (thickness 0.035))
 (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0))
 (layer "B.Paste" (type "Bottom Solder Paste"))
 (layer "B.SilkS" (type "Bottom Silk Screen"))
 (copper_finish "ENIG") (dielectric_constraints yes))'''
assert '(stackup' not in raw
fn.write_text(raw.replace('(setup\n', '(setup\n' + stack + '\n', 1), encoding='utf-8')
loaded = k.LoadBoard(str(fn))
k.SaveBoard(str(fn), loaded)
cfgfile = fn.with_suffix('.kicad_pro')
cfg = json.loads(cfgfile.read_text(encoding='utf-8'))
for nc in cfg['net_settings']['classes']:
    nc['clearance'] = .15
rules = cfg['board']['design_settings']['rules']
rules['min_clearance'] = .15
rules['min_copper_edge_clearance'] = .15
cfg['board']['design_settings']['rule_severities']['solder_mask_bridge'] = 'warning'
cfgfile.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# Exportacao de leitura do arquivo salvo para auditoria independente geometrica.
evidence = dict(kicad_version=k.Version(),source=str(SOURCE / 'geometria.json'),
    source_sha256=hashlib.sha256((SOURCE / 'geometria.json').read_bytes()).hexdigest(),
    transformacao='KiCad X=80+HFSS Y; KiCad Y=110-HFSS X; mm',
    radiadores=4,spacing_mm=48,board_mm=[70,184],core_mm=.76,copper_mm=.035,
    thickness_nominal_mm=.83,mask='aberta em toda a PCB nas duas faces',
    native_sha256=hashlib.sha256(fn.read_bytes()).hexdigest(),drawings=[],pads=[],vias=[])
def unpos(v):
    return [110-k.ToMM(v.y), k.ToMM(v.x)-80]
for item in loaded.GetDrawings():
    if not isinstance(item,k.PCB_SHAPE) or item.GetLayer() not in (k.F_Cu,k.B_Cu):
        continue
    ps=item.GetPolyShape()
    contours=[]
    for i in range(ps.OutlineCount()):
        line=ps.COutline(i)
        contours.append([unpos(line.CPoint(j)) for j in range(line.PointCount())])
    evidence['drawings'].append(dict(layer='F' if item.GetLayer()==k.F_Cu else 'B',net=item.GetNetname(),contours=contours))
for foot in loaded.GetFootprints():
    for pad in foot.Pads():
        evidence['pads'].append(dict(ref=foot.GetReference(),number=pad.GetNumber(),net=pad.GetNetname(),
            center=unpos(pad.GetPosition()),diameter=k.ToMM(pad.GetSize().x),drill=k.ToMM(pad.GetDrillSize().x),
            layers=[a for a,l in [('F',k.F_Cu),('B',k.B_Cu)] if pad.IsOnLayer(l)]))
for via in loaded.GetTracks():
    evidence['vias'].append(dict(center=unpos(via.GetPosition()),diameter=k.ToMM(via.GetWidth(k.F_Cu)),drill=k.ToMM(via.GetDrill()),net=via.GetNetname()))
assert len(evidence['pads'])==4 and len(evidence['vias'])==8
(OUT/'leitura_kicad.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({key:evidence[key] for key in ['kicad_version','board_mm','native_sha256']},indent=2))
