"""Buscar os menores pares de entrada UT-141C no recorte de acesso da placa alongada."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np

repo=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(repo/"freecad/mecanica_R01/fonte"))
from formar_cabos import fillet, lengths, sample
from dimensoes import N_Y, PIN, PLACA_Z, R_CABO


def candidatos():
    result=[]
    for u in [-245.,-241.,-237.,-233.]:
        for y in [24.15,24.75,25.35,25.75]:
            for height in [-.3,.2,1.,2.,4.]:
                for first in [-245.0,-243.0,-241.0]:
                    pts=[[-260,N_Y,-31],[first,N_Y,-31],[PIN+u,y,-31],
                         [PIN+u,y,height],[PIN-230,31,height],[PIN-230,31,-10]]
                    try:route=fillet(pts)
                    except ValueError:continue
                    lens=lengths(route)
                    if lens[0]<15.5 or lens[-1]<5.1:continue
                    pts=sample(route,.35)
                    if min(pts[pts[:,2]>-7,1])<22+R_CABO+.2:continue
                    result.append((sum(lens),route))
    return sorted(result,key=lambda q:q[0])


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("out",type=Path)
    args=p.parse_args();result=candidatos()
    assert result
    args.out.write_text(json.dumps(result),encoding="utf8")
    print(len(result),"opções Mín.",round(result[0][0],4),"mm. Verificar em B-rep.")
