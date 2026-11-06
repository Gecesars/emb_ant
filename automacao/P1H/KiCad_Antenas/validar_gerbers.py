"""Validate the actual KiCad X2 regions, flashed pads, drills, and closed board outlines."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile

from shapely import affinity, make_valid
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

root=Path(__file__).resolve().parent
g=json.loads((root/"elemento_hfss.json").read_text())

def plotted_copper(path):
    text=path.read_text()
    assert "%FSLAX46Y46*%" in text and "%MOMM*%" in text
    apertures={int(i):float(d) for i,d in re.findall(r"%ADD(\d+)C,([.\d]+)\*%",text)}
    assert "%LPC" not in text
    parts=[];region=None;aperture=None
    for line in text.splitlines():
        if line=="G36*":region=[]
        elif line=="G37*":
            parts.append(make_valid(Polygon(region)));region=None
        elif match:=re.fullmatch(r"D(\d+)\*",line):aperture=int(match[1])
        elif match:=re.fullmatch(r"X(-?\d+)Y(-?\d+)D0([123])\*",line):
            x,y,op=int(match[1])/1e6,int(match[2])/1e6,match[3]
            if op=="3":parts.append(Point(x,y).buffer(apertures[aperture]/2,quad_segs=96))
            else:
                assert region is not None
                region.append((x,y))
    return unary_union(parts)

for name,n in [("P1H_Individual",1),("P1H_Coluna_10",10)]:
    folder=root/name
    d=folder/"gerber"
    polygons={k:[] for k in "FB"}
    for i in range(n):
        elems={k:[] for k in "FB"}
        for land in g["lands"]:elems[land["layer"]].append(Polygon(land["outer"],land["holes"]))
        for x,y in g["ports"].values():
            for shapes in elems.values():shapes.append(Point(x,y).buffer(.60,quad_segs=96))
            elems["B"].append(Point(x+1.05,y).buffer(.125,quad_segs=96))
        for x,y in g["vias"]:
            for shapes in elems.values():shapes.append(Point(x,y).buffer(.363,quad_segs=96))
        for face,shapes in elems.items():
            polygons[face].append(affinity.translate(unary_union(shapes),xoff=22+i*g["pitch"],yoff=-40))
    for face,ext in [("F","gtl"),("B","gbl")]:
        actual=plotted_copper(next(d.glob("*."+ext)))
        expected=unary_union(polygons[face])
        diff=expected.symmetric_difference(actual).area
        assert diff<.005*n,(face,diff)
        print(name,face,"delta area exported [mm2]",diff)
    drill=(d/(name+".drl")).read_text()
    pts=re.findall(r"^X([-\d.]+)Y([-\d.]+)$",drill,re.M)
    assert len(pts)==4*n and "T1C0.400" in drill and "T2C0.850" in drill
    for tool,centers in [(1,g["vias"]),(2,list(g["ports"].values()))]:
        coordinates=re.search(rf"^T{tool}\n((?:X[^\n]+\n)+)",drill,re.M)[1]
        actual=sorted((float(x),float(y)) for x,y in re.findall(r"X([-\d.]+)Y([-\d.]+)",coordinates))
        expected=sorted((22+i*52.6+x,-40+y) for i in range(n) for x,y in centers)
        assert len(actual)==len(expected) and max(abs(v-w) for p,q in zip(actual,expected) for v,w in zip(p,q))<.00051
    outline=next(d.glob("*.gm1")).read_text()
    corners=[(int(x)/1e6,int(y)/1e6) for x,y in re.findall(r"X(-?\d+)Y(-?\d+)D0[12]",outline)]
    assert len(corners)==8 and set(Counter(corners).values())=={2}
    assert abs(max(x for x,y in corners)-min(x for x,y in corners)-28.3125-(n-1)*52.6)<1e-6
    assert abs(max(y for x,y in corners)-min(y for x,y in corners)-28.3125)<1e-6
    drc=json.loads((folder/"drc.json").read_text(encoding="utf8"))
    assert all(v["type"]=="solder_mask_bridge" and v["severity"]=="warning" for v in drc["violations"])
    assert not drc["unconnected_items"]
    archive=folder/("Gerber_"+name+".zip")
    with ZipFile(archive,"w",ZIP_DEFLATED) as pkg:
        for f in sorted(d.iterdir()):pkg.write(f,f.name)
    with ZipFile(archive) as pkg:assert len(pkg.namelist())==9 and pkg.testzip() is None
    print(name,len(pts),"plated holes",hashlib.sha256(archive.read_bytes()).hexdigest())
