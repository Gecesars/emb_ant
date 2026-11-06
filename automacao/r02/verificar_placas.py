"""Comparar contornos e furação do CAM às interfaces usadas no modelo e embalar os Gerbers."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from shapely.geometry import LineString, Polygon
from shapely.ops import polygonize


def verify(folder):
    g=json.loads((folder/"geometria.json").read_text())
    name=g["arquivo"]
    fab=folder/"gerber"
    points=re.findall(r"^X(-?\d+)Y(-?\d+)D0([12])\*$",next(fab.glob("*.gm1")).read_text(),re.M)
    lines=[]
    for x,y,kind in points:
        xy=(int(x)*1e-6-80,int(y)*1e-6+65)
        if kind=="1":lines.append(LineString([last,xy]))
        last=xy
    loops=sorted(polygonize(lines),key=lambda p:p.area,reverse=True)
    assert len(loops)==2
    geometry=Polygon(g["outline"],[g["janela"]])
    assert geometry.symmetric_difference(loops[0]).area<.0001
    drills=next(fab.glob("*-PTH.drl")).read_text()
    assert "T1C1.000" in drills
    coords=sorted((float(x)-80,float(y)+65) for x,y in re.findall(r"^X([-\d.]+)Y([-\d.]+)$",drills,re.M))
    expected=sorted((x,y) for name,x,y in g["ports"])
    # Duas coordenadas nominalmente coincidentes em X podem diferir apenas na representação binária.
    assert len(coords)==len(expected)
    assert max(min(max(abs(px-x),abs(py-y)) for x,y in coords) for px,py in expected)<.00051
    report=(folder/"drc.rpt").read_text(encoding="utf8")
    assert "Found 0 DRC violations" in report and "Found 0 unconnected pads" in report
    files=[p for p in fab.iterdir() if not p.name.endswith("-NPTH.drl")]
    assert {p.suffix for p in files}=={".gtl",".gbl",".gts",".gbs",".gto",".gbo",".gm1",".drl",".gbrjob"}
    package=folder/("Gerber_"+g["arquivo"]+".zip")
    with ZipFile(package,"w",ZIP_DEFLATED) as archive:
        for f in sorted(files):archive.write(f,f.name)
    with ZipFile(package) as archive:assert archive.testzip() is None
    return dict(pcb=g["arquivo"],furos=len(coords),contornos=len(loops),sha256=hashlib.sha256(package.read_bytes()).hexdigest())


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("placas",type=Path)
    args=p.parse_args()
    print(json.dumps([verify(args.placas/side) for side in ("Inferior","Superior")],indent=2))
