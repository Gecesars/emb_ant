"""Pesquisar ramais iguais para duas redes 1:5 por polarização. Toda a geometria está em mm."""
import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

repo=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(repo/"freecad/mecanica_R01/fonte"))
from dimensoes import PIN, PASSO, PLACA_Z, R_CABO, N_Y
from formar_cabos import fillet, lengths, sample, R

DIV_B=-11.52
STRAIGHT=1.5
SEPARACAO=2*R_CABO+.42


def generate(points, length):
    start,end,mid=points
    planar=[start[:2],end[:2]] if mid is None else [start[:2],mid,end[:2]]
    def at(z):return fillet([start]+[[*p,z] for p in planar]+[end])
    # Baixar o plano de dobra aumenta os dois trechos verticais pelo mesmo valor.
    deep=-150
    z=deep+(sum(lengths(at(deep)))-length)/2
    if z>DIV_B-R-STRAIGHT+1e-6:raise ValueError("trecho de solda insuficiente")
    e=at(z)
    assert abs(sum(lengths(e))-length)<1e-6
    return e


def search(ports, length):
    entries=[]
    for key,x,y in ports:
        if key.endswith("_IN"):continue
        s=np.array([x,y,DIV_B])
        idx=int(key[1:])-3
        e=np.array([idx*PASSO, -PIN if key[0]=="A" else PIN,PLACA_Z])
        entries.append((key,s,e))
    candidates={}
    for key,start,end in entries:
        other=[]
        for other_name,s,e in entries:
            if other_name==key:continue
            other.extend([[e[0],e[1],z] for z in np.arange(-35,18,.5)])
            other.extend([[s[0],s[1],z] for z in np.arange(DIV_B-R-STRAIGHT,DIV_B+.1,.5)])
        # Reservar lançamentos das duas entradas da placa divisora.
        for y in [-N_Y,N_Y]:
            other.extend([[0,y,z] for z in np.arange(-30,DIV_B+.1,.5)])
        obstacles=cKDTree(other)
        direct=end[:2]-start[:2];normal=np.array([-direct[1],direct[0]])/np.linalg.norm(direct)
        valid=[]
        for off in [0,3,-3,6,-6,9,-9,12,-12,16,-16,23,-23,30,-30,40,-40]:
            for frac in ([.5] if not off else [.5,.25,.75]):
                mid=None if not off else start[:2]+frac*direct+off*normal
                try:edges=generate((start,end,mid),length)
                except ValueError:continue
                cloud=sample(edges,.7)
                if min(obstacles.query(cloud)[0])<SEPARACAO:continue
                valid.append((.15*abs(off)+.01*abs(min(cloud[:,2])),edges,cloud,cKDTree(cloud)))
        if not valid:return None
        candidates[key]=sorted(valid,key=lambda a:a[0])
    ordered=sorted(candidates,key=lambda name:len(candidates[name]))
    def fit(depth,chosen):
        if depth==len(ordered):return {k:v[1] for k,v in chosen.items()}
        name=ordered[depth]
        for route in candidates[name]:
            if any(np.min(r[3].query(route[2])[0])<SEPARACAO for r in chosen.values()):continue
            chosen[name]=route
            solved=fit(depth+1,chosen)
            if solved:return solved
            del chosen[name]
        return None
    return fit(0,{})


def compact(geometry):
    ports=geometry["ports"]
    proj=max(math.hypot((int(n[1:])-3)*PASSO-x,(-PIN if n[0]=="A" else PIN)-y)
             for n,x,y in ports if not n.endswith("_IN"))
    # Duas curvas tangentes de 90°, com a primeira após o trecho reto de solda.
    lower_bound=proj+(PLACA_Z-DIV_B)+2*(R+STRAIGHT)-2*R*(2-math.pi/2)
    for length in range(math.ceil(lower_bound),170):
        routes=search(ports,length)
        if routes:return length,lower_bound,routes
    raise RuntimeError("A faixa de comprimentos pesquisada não produziu um chicote.")


def export_geometry(out, routes, length, bound):
    out.mkdir(parents=True,exist_ok=True)
    all_routes={}
    for half,delta in [("INF",PIN-2.5*PASSO),("SUP",PIN+2.5*PASSO)]:
        for key,edges in routes.items():
            full=[[tag,*[[x+delta,y,z] for x,y,z in coords]] for tag,*coords in edges]
            all_routes[half+"_"+key]=full
    (out/"caminhos.json").write_text(json.dumps(all_routes,indent=1),encoding="utf8")
    with (out/"ramais.csv").open("w",encoding="utf8",newline="") as f:
        w=csv.writer(f)
        w.writerow(["placa","porta","elemento","comprimento_eixo_mm","raio_dobra_mm","saida_X_mm","saida_Y_mm","antena_X_mm","antena_Y_mm","traseira_min_Z_mm"])
        for name,edges in sorted(all_routes.items()):
            half,port=name.split("_");idx=int(port[1:])+(5 if half=="SUP" else 0)
            pts=sample(edges,.5)
            w.writerow([half,port,idx,round(sum(lengths(edges)),5),R,*edges[0][1][:2],*edges[-1][-1][:2],round(min(pts[:,2])-R_CABO,3)])
    print("20 ramais",length,"mm. Limite da familia de curvas:",round(bound,3))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("geometria",type=Path);p.add_argument("destino",type=Path)
    args=p.parse_args()
    length,bound,routes=compact(json.loads(args.geometria.read_text()))
    export_geometry(args.destino,routes,length,bound)
