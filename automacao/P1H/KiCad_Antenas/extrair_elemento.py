"""Read the solved HFSS element's planar operations and final substrate dimensions."""
import json
import re
from pathlib import Path

from shapely.geometry import Point, Polygon

root = Path(__file__).resolve().parent
source = (root.parent / "P1H_AB_em_fase.aedt").read_text(encoding="utf8", errors="replace")
parts = {}
for block in re.findall(r"\$begin 'GeometryPart'(.*?)\$end 'GeometryPart'", source, re.S):
    name = re.search(r"Name='([^']+)'", block)[1]
    if name.startswith("E001_P1H_"):
        parts[name.removeprefix("E001_P1H_")] = block

def dim(name, key):
    return float(re.search(rf"\b{key}='([-\d.]+)mm'", parts[name])[1])

def copper(name):
    points = re.findall(r"X='([-\d.]+)mm'\s+Y='([-\d.]+)mm'\s+Z='([-\d.]+)mm'", parts[name])
    assert points[0] == points[-1] and len({p[2] for p in points}) == 1
    assert "SegmentType='Arc'" not in parts[name]
    return Polygon([(float(x), float(y)) for x,y,_ in points]), float(points[0][2])

def disk(x,y,r):
    return Point(x,y).buffer(r,quad_segs=96)

outline = [dim("Substrate","XSize"),dim("Substrate","YSize")]
h = dim("Substrate","ZSize")
z = dim("Substrate","ZPosition")
assert outline == [28.3125,28.3125] and h == .76
lands = []
def land(name, layer, net, poly):
    assert poly.is_valid and poly.geom_type == "Polygon"
    lands.append(dict(name=name,layer=layer,net=net,outer=list(poly.exterior.coords)[:-1],
                      holes=[list(r.coords)[:-1] for r in poly.interiors],area=poly.area))
ports = {}
for pol in "AB":
    shield = "Shield_"+pol
    x,y = dim(shield,"XCenter"),dim(shield,"YCenter")
    ports[pol] = [x,y]
    assert dim("Pin_"+pol,"Radius") == .362981
for i,net,pol in [(1,"RET_B","B"),(2,"Q2",None),(3,"Q3",None),(4,"RET_A","A")]:
    name="Ring_Q"+str(i)
    outer,level = copper(name)
    hole,_ = copper(name+"_opening")
    ring=outer.difference(hole)
    assert level==z
    if pol:
        x,y=ports[pol]
        outer_radius=dim(name+"_coax_"+pol,"Radius")
        inner_radius=dim("Shield_"+pol+"_Inner","Radius")
        ring=ring.difference(disk(x,y,outer_radius))
        # Planar land under the modelled soldered shield, continuous with its quadrant.
        shell=disk(x,y,outer_radius).difference(disk(x,y,inner_radius))
        ring=ring.union(shell)
    land(name,"B",net,ring)
for name,layer,net in [("Crossover_Bridge","B","SIG_B"),("Feed_A","F","SIG_A"),
                       ("Feed_B_Outer","F","SIG_B"),("Feed_B_Inner","F","SIG_B")]:
    poly,level=copper(name)
    assert abs(level-(z+(h if layer=="F" else 0)))<1e-9
    # KiCad PTH pads and their actual finished drills define the pin openings.
    land(name,layer,net,poly)
vias=[[dim("Via_"+str(i),"XCenter"),dim("Via_"+str(i),"YCenter")] for i in (1,2)]
data=dict(outline=outline,core=h,pitch=52.6,ports=ports,vias=vias,lands=lands)
(root/"elemento_hfss.json").write_text(json.dumps(data,separators=(",",":")),encoding="utf8")
print("HFSS",outline,len(lands),ports,vias)
