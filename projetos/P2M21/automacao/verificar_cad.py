"""Reabrir nativos e verificar intersecoes volumetricas; contatos tangentes sao permitidos."""
import json
from pathlib import Path
import FreeCAD as A
root=Path('D:/dev/EMBRAER/P2M21/R00_Concepcao')
for folder,name in [('antena','P2M21_Antena'),('divisor_1x4','P2M21_Duplo_1x4'),('divisor_1x8','P2M21_Duplo_1x8')]:
    d=A.openDocument(str(root/folder/(name+'.FCStd')))
    objs=[o for o in d.Objects if hasattr(o,'Shape')];bad=[];tested=0
    for i,o in enumerate(objs):
        assert o.Shape.isValid() and o.Shape.Volume>0,o.Name
        a=o.Shape.BoundBox
        for q in objs[i+1:]:
            b=q.Shape.BoundBox
            if min(a.XMax,b.XMax)-max(a.XMin,b.XMin)<=1e-6:continue
            if min(a.YMax,b.YMax)-max(a.YMin,b.YMin)<=1e-6:continue
            if min(a.ZMax,b.ZMax)-max(a.ZMin,b.ZMin)<=1e-6:continue
            tested+=1;v=o.Shape.common(q.Shape).Volume
            if v>1e-7:bad.append([o.Name,q.Name,v])
    result=dict(objetos=len(objs),pares_booleanos=tested,intersecoes=bad,aprovado=not bad)
    (root/folder/'cad/intersecoes.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(folder,result,flush=True);A.closeDocument(d.Name)
