"""Verificar CAM de cada placa e exportar o corte e as linhas de dobra do refletor."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from shapely.geometry import LineString, Polygon
from shapely.ops import polygonize


def embalar(p):
    g=json.loads((p/"geometria.json").read_text())
    fab=p/"gerber"
    def xy(x,y):return float(x)-g["origem_x"],float(y)+65
    edges=[]
    for x,y,k in re.findall(r"^X(-?\d+)Y(-?\d+)D0([12])\*$",next(fab.glob("*.gm1")).read_text(),re.M):
        current=xy(int(x)*1e-6,int(y)*1e-6)
        if k=="1":edges.append(LineString([last,current]))
        last=current
    loops=list(polygonize(edges))
    assert len(loops)==1 and loops[0].symmetric_difference(Polygon(g["outline"])).area<1e-4
    def conferir(tag,diam,nominal):
        data=next(fab.glob("*-"+tag+".drl")).read_text()
        assert "T1C"+diam in data
        actual=[xy(x,y) for x,y in re.findall(r"^X([-\d.]+)Y([-\d.]+)$",data,re.M)]
        assert len(actual)==len(nominal)
        assert all(sum(max(abs(x-a),abs(y-b))<.00051 for a,b in actual)==1 for x,y in nominal)
    conferir("PTH","1.000",[(x,y) for _,x,y in g["ports"]])
    conferir("NPTH","2.800",g["fixacao"])
    assert all(t in (p/"drc.rpt").read_text(encoding="utf8") for t in ("Found 0 DRC violations","Found 0 unconnected pads"))
    files=sorted(fab.iterdir())
    assert len(files)==10 and {f.suffix for f in files}=={".drl",".gm1",".gtl",".gbl",".gts",".gbs",".gto",".gbo",".gbrjob"}
    pkg=p/("Gerber_"+g["arquivo"]+".zip")
    with ZipFile(pkg,"w",ZIP_DEFLATED) as z:
        for f in files:z.write(f,f.name)
    with ZipFile(pkg) as z:assert z.testzip() is None
    return dict(pcb=g["arquivo"],PTH=len(g["ports"]),NPTH=len(g["fixacao"]),sha256=hashlib.sha256(pkg.read_bytes()).hexdigest())


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("estudo",type=Path)
    parser.add_argument("--material",default="ZYF300CA-C")
    args=parser.parse_args();folder=args.estudo/args.material
    results=[embalar(folder/s) for s in ["Inferior","Superior"]]
    (folder/"verificacao_cam.json").write_text(json.dumps(results,indent=2))
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"freecad/mecanica_R01/fonte"))
    import dimensoes
    dimensoes.SAIDA=args.estudo/"mecanica"
    dimensoes.ref_bolts=lambda:json.loads((dimensoes.SAIDA/"verificacao.json").read_text())["furos_fixacao_mm"]
    import exportar_corte
    exportar_corte.main()
    print(results)
