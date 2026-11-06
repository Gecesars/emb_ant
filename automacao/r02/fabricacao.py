"""Mapa completo dos 26 cabos e componentes usinados específicos da R02."""
import csv
import json
import os
from pathlib import Path

import FreeCAD as App
import Part

folder=Path(os.environ["P1H_R02"])/"compacta"
doc=App.openDocument(str(folder/"P1H_R02_compacta.FCStd"))
lengths=json.loads((folder/"verificacao_cad.json").read_text())["comprimentos_mm"]
with (folder/"chicote_26_cabos.csv").open("w",newline="",encoding="utf8") as f:
    writer=csv.writer(f)
    writer.writerow(["cabo","origem","destino","eixo_entre_interfaces_mm","raio_eixo_mm","menor_Z_externo_mm"])
    for name,length in sorted(lengths.items()):
        toks=name.split("_")
        if name.startswith("IN_"):
            pol=toks[1];start="N_"+pol;end="Inferior/R"+pol+"_IN"
        elif name.startswith("TR_"):
            group,pol=toks[1:]
            start="Inferior/R"+pol+("1" if group=="INF" else "2")
            end=("Inferior" if group=="INF" else "Superior")+"/"+pol+"_IN"
        else:
            group,port=toks
            start=("Inferior" if group=="INF" else "Superior")+"/"+port
            end="E%02d"%(int(port[1:])+(0 if group=="INF" else 5))+"/"+port[0]
        writer.writerow([name,start,end,round(length,6),4.4,round(doc.getObject(name).Shape.BoundBox.ZMin,6)])
parts=folder/"componentes"
parts.mkdir(exist_ok=True)
for name in ["Berco_2","Trilho_INF_E","Trilho_INF_D","Trilho_RAIZ_E","Trilho_RAIZ_D","Trilho_SUP_E","Trilho_SUP_D"]:
    sh=doc.getObject(name).Shape.copy()
    assert sh.isValid() and len(sh.Solids)==1
    path=parts/(name+".step")
    sh.exportStep(str(path))
    check=Part.read(str(path))
    assert len(check.Solids)==1 and abs(check.Volume-sh.Volume)<1e-5
print("SETUP_MEC_OK",len(lengths))
