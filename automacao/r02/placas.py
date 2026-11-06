"""Geometrias de fabricação das duas PCBs físicas R02, no referencial do centro de cada grupo."""
import argparse
import json
import math
from pathlib import Path

from shapely.geometry import box
from shapely.ops import unary_union


def physical(working):
    g5=json.loads((working/"revisao/1x5/geometria.json").read_text())
    g2=json.loads((working/"revisao/1x2/geometria.json").read_text())
    for lower in (True,False):
        group="Inferior" if lower else "Superior"
        outlines=[box(-19.5,-39,19.5,39)]
        if lower:
            outlines.extend([box(19.5,30,112,39),box(112,-39,151,39)])
        outer=unary_union(outlines)
        g=dict(g5,arquivo="R02_"+group,legenda="P1H "+group.upper(),legenda_xy=[0,37.0],
               ports=[],port_net={},rotulos={},copper={},outline=list(outer.exterior.coords)[:-1],
               outline_gnd=list(outer.buffer(-.52,join_style="mitre").exterior.coords)[:-1])
        heads=[(g5,0,"")] + ([(g2,131.5,"R")] if lower else [])
        for source,dx,prefix in heads:
            for pol,pts in source["copper"].items():
                g["copper"][prefix+pol]=[(x+dx,y) for x,y in pts]
            for name,x,y in source["ports"]:
                key=prefix+name
                g["ports"].append([key,dx+x,y])
                g["port_net"][key]=prefix+name[0]
                cy=-19.25 if name[0]=="A" else 19.25
                if name.endswith("IN"):
                    offset=(0,3.8)
                else:
                    a=math.atan2(y-cy,x)
                    offset=(3.7*math.cos(a),3.7*math.sin(a))
                    if abs(x)>14:offset=(0,3.8)
                    if abs(y)>33:offset=(3.3,0)
                g["rotulos"][key]=[key.replace("_"," "),dx+x+offset[0],y+offset[1]]
        folder=working/"placas"/group
        folder.mkdir(parents=True,exist_ok=True)
        (folder/"geometria.json").write_text(json.dumps(g,indent=1),encoding="utf8")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("estudo",type=Path)
    physical(parser.parse_args().estudo)
