"""Equilibrar a ligação dos dois N e os quatro enlaces da primeira divisão RF."""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from ramais import DIV_B, PIN, PASSO, N_Y, SEPARACAO, generate, fillet, lengths, sample


def connect(branches):
    cloud=np.vstack([sample(v,.6) for v in branches.values()])
    tree=cKDTree(cloud)
    for length in range(125,175):
        chosen={}
        for half,side in [("INF",-1),("SUP",1)]:
            for pol,sgn in [("A",-1),("B",1)]:
                s=np.array([PIN+side*15.2,sgn*N_Y,DIV_B])
                e=np.array([PIN+side*2.5*PASSO,sgn*N_Y,DIV_B])
                options=[]
                for off in [0,4,-4,8,-8,12,-12,18,-18,25,-25,34,-34]:
                    for frac in ([.5] if off==0 else [.25,.5,.75]):
                        mid=None if off==0 else s[:2]+frac*(e[:2]-s[:2])+[0,off]
                        try:route=generate((s,e,mid),length)
                        except ValueError:continue
                        pts=sample(route,.6)
                        distances=[float(min(tree.query(pts)[0]))]+[float(min(cKDTree(sample(v,.6)).query(pts)[0])) for v in chosen.values()]
                        if min(distances)>=SEPARACAO:options.append((abs(off),-min(distances),route))
                if options:
                    chosen["TR_"+half+"_"+pol]=min(options,key=lambda z:z[:2])[2]
        if len(chosen)==4:break
    else:raise RuntimeError("Os quatro enlaces não couberam no intervalo.")
    tree=cKDTree(np.vstack([cloud]+[sample(v,.6) for v in chosen.values()]))
    options=[]
    # Saída do conector em +X. Entrada do divisor em +Z, com 4 mm reservados à bobina.
    for off in np.arange(-14,34.1,2):
        for z in [-22,-25,-28,-31,-34,-38,-42,-48,-55]:
            for early in [-234,-212,-185]:
                for late in [-64,-48,-33,-22]:
                    pair={}
                    for pol,sgn in [("A",-1),("B",1)]:
                        y=sgn*N_Y; lane=sgn*(N_Y+off)
                        points=[[-260,y,-31],[-243,y,-31],[early,lane,z],[late,lane,z],
                                [PIN,y,z],[PIN,y,DIV_B]]
                        try:wire=fillet(points)
                        except (ValueError,FloatingPointError):break
                        if lengths(wire)[-1]<5.5:break
                        pts=sample(wire,.8)
                        if min(tree.query(pts)[0])<SEPARACAO:break
                        pair["IN_"+pol]=wire
                    if len(pair)==2:
                        if np.min(cKDTree(sample(pair["IN_A"],.8)).query(sample(pair["IN_B"],.8))[0])>=SEPARACAO:
                            options.append((sum(lengths(pair["IN_A"])),pair))
    if not options:raise RuntimeError("Entradas sem percurso viável.")
    feed,pair=min(options,key=lambda x:x[0])
    chosen.update(pair)
    return length,feed,chosen


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dir",type=Path)
    args=parser.parse_args()
    ramais=json.loads((args.dir/"caminhos.json").read_text())
    length,feed,lines=connect(ramais)
    (args.dir/"enlaces.json").write_text(json.dumps(lines,indent=1),encoding="utf8")
    print("4 enlaces",length,"mm; 2 entradas",feed,"mm")
