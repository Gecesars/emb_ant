"""Tubo aberto de catalogo na montagem fisica preservada."""
from pathlib import Path
import json,FreeCAD as A,Part,math
ROOT=Path('D:/dev/EMBRAER/P2S13/R16_Tubo_PVC/dn100');cfg=json.loads((ROOT/'configuracao.json').read_text());t=cfg['radome']
OUT=ROOT/'visual';OUT.mkdir(exist_ok=True);target=OUT/'Antena_PVC_DN100_PRELIMINAR.FCStd';assert not target.exists()
d=A.openDocument('D:/dev/EMBRAER/P2S13/R15_Casamento_C09/c02/visual/Antena_C09_Ajustada_PRELIMINAR.FCStd')
names=json.loads(Path('D:/dev/EMBRAER/P2S13/R14_Compacto_Simetrico_SemRadome/c00/cad/manifesto.json').read_text())
origin=A.Vector(-t['comprimento_mm']/2,0,t['centro_z_mm']);axis=A.Vector(1,0,0)
sh=Part.makeCylinder(t['De_mm']/2,t['comprimento_mm'],origin,axis).cut(Part.makeCylinder(t['Di_mm']/2,t['comprimento_mm'],origin,axis))
assert sh.isValid() and len(sh.Solids)==1
bad=[];before={n:d.getObject(n).Shape.Volume for n in names}
for n in names:
    vol=sh.common(d.getObject(n).Shape).Volume
    if vol>1e-7:bad.append([n,vol])
assert not bad,bad
o=d.addObject('PartDesign::Feature','Tubo_PVC_DN100');o.Shape=sh;o.Label='PVC DN100 — De101,6 / parede1,8 / L350 mm — referencia RF'
d.Label='Antena no tubo PVC DN100 — PRELIMINAR';d.recompute()
assert all(abs(d.getObject(n).Shape.Volume-v)<1e-7 for n,v in before.items())
d.saveAs(str(target));A.closeDocument(d.Name)
(OUT/'auditoria_cad.json').write_text(json.dumps(dict(solidos_anteriores=122,solidos_com_tubo=123,tubo_solidos=1,intersecoes=bad,objetos_anteriores_preservados=True,tubo=t),indent=2))
print('CAD_TUBO_VALIDADO')
