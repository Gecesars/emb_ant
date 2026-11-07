"""Construir comprimentos iguais ajustados eletricamente, com curvas e folgas verificadas."""
import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import brentq
from scipy.spatial import cKDTree

repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo / "automacao/r02"))
from ramais import PIN, PASSO, N_Y, DIV_B, SEPARACAO, generate, fillet, lengths, sample


def adjust(source, target, input_length, trunk_length, branch_length):
    routes = json.loads((source / "caminhos.json").read_text())
    for edges in routes.values():
        shift = (branch_length - sum(lengths(edges))) / 2
        assert shift >= 0
        for i, edge in enumerate(edges):
            for j, point in enumerate(edge[1:]):
                if (i == 0 and j == 0) or (i == len(edges)-1 and j == len(edge)-2):
                    continue
                point[2] -= shift
        assert abs(sum(lengths(edges)) - branch_length) < 1e-7
    clouds = [sample(value, .5) for value in routes.values()]
    tree = cKDTree(np.vstack(clouds))
    # Encontrar quatro enlaces do mesmo comprimento sem tocar nos ramais.
    options = {}
    for half, side in [("INF", -1), ("SUP", 1)]:
        for pol, sign in [("A", -1), ("B", 1)]:
            name = "TR_" + half + "_" + pol
            start = np.array([PIN+side*15.2, sign*N_Y, DIV_B])
            end = np.array([PIN+side*2.5*PASSO, sign*N_Y, DIV_B])
            options[name] = []
            for off in range(-34,35,2):
                for frac in ([.5] if off == 0 else [.15,.25,.35,.5,.65,.75,.85]):
                    mid = None if off == 0 else start[:2]+frac*(end[:2]-start[:2])+[0,off]
                    try:
                        edges = generate((start, end, mid), trunk_length)
                    except ValueError:
                        continue
                    points = sample(edges, .5)
                    clearance = min(tree.query(points)[0])
                    if clearance >= SEPARACAO:
                        options[name].append((abs(off), -clearance, edges, cKDTree(points), points))
            options[name].sort(key=lambda value: value[:2])
            assert options[name], name
    order = sorted(options, key=lambda name: len(options[name]))
    def search(depth, chosen):
        if depth == len(order):
            return {name:value[2] for name,value in chosen.items()}
        name = order[depth]
        for option in options[name]:
            if any(min(other[3].query(option[4])[0]) < SEPARACAO for other in chosen.values()):
                continue
            chosen[name] = option
            result = search(depth+1, chosen)
            if result:
                return result
            del chosen[name]
        return None
    trunks = search(0, {})
    assert trunks, "Sem combinacao dos quatro enlaces"
    tree = cKDTree(np.vstack(clouds + [sample(value, .5) for value in trunks.values()]))
    candidates = []
    for off in [0,2,-2,4,-4,6,-6,8,-8,10,-10,12,-12,16,20,24,28,32]:
        for early in [-234,-212,-185]:
            for late in [-64,-48,-33,-22]:
                def route(z, sign):
                    y = sign*N_Y
                    lane = sign*(N_Y+off)
                    return fillet([[-260,y,-31],[-243,y,-31],[early,lane,z],
                                   [late,lane,z],[PIN,y,z],[PIN,y,DIV_B]])
                samples = []
                for z in np.linspace(-75,-21.5,30):
                    try:
                        candidate = route(z,-1)
                        samples.append((z, sum(lengths(candidate))-input_length))
                    except ValueError:
                        pass
                for (z1,f1),(z2,f2) in zip(samples,samples[1:]):
                    if f1*f2 > 0:
                        continue
                    try:
                        z = brentq(lambda height:sum(lengths(route(height,-1)))-input_length,z1,z2)
                    except ValueError:
                        continue
                    pair = {"IN_A":route(z,-1), "IN_B":route(z,1)}
                    if any(lengths(edges)[-1] < 5.5 for edges in pair.values()):
                        continue
                    a,b = [sample(value,.5) for value in pair.values()]
                    clearance = min(min(tree.query(a)[0]), min(tree.query(b)[0]), min(cKDTree(a).query(b)[0]))
                    if clearance >= SEPARACAO:
                        candidates.append((abs(off), -clearance, pair))
    assert candidates, "Entradas sem comprimento/folga realizavel"
    chosen = min(candidates,key=lambda value:value[:2])
    joins = dict(trunks, **chosen[2])
    all_routes = dict(routes, **joins)
    minimum = float("inf")
    names = list(all_routes)
    clouds = [sample(all_routes[name],.35) for name in names]
    for i in range(len(names)):
        for j in range(i):
            minimum = min(minimum, min(cKDTree(clouds[j]).query(clouds[i])[0]))
    assert minimum >= SEPARACAO-.015
    target.mkdir(parents=True,exist_ok=True)
    (target/"caminhos.json").write_text(json.dumps(routes,indent=1),encoding="utf8")
    (target/"enlaces.json").write_text(json.dumps(joins,indent=1),encoding="utf8")
    record = dict(entrada_mm=input_length, tronco_mm=trunk_length, ramal_mm=branch_length,
        comprimento_total_mm=2*input_length+4*trunk_length+20*branch_length,
        distancia_minima_eixos_mm=minimum, folga_minima_estimada_mm=minimum-2*1.7905,
        verificacao="Amostragem de eixos; conferir intersecoes OCCT no conjunto antes de aprovar")
    (target/"chicote_ajustado.json").write_text(json.dumps(record,indent=2),encoding="utf8")
    print(json.dumps(record,indent=2))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("origem", type=Path)
    parser.add_argument("destino", type=Path)
    parser.add_argument("--comprimentos", type=float, nargs=3, required=True, metavar=("ENTRADA","TRONCO","RAMAL"))
    args=parser.parse_args()
    adjust(args.origem,args.destino,*args.comprimentos)
