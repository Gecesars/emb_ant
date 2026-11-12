"""Tesselacao apenas para ilustracao; nao e malha HFSS nem sera versionada."""
from pathlib import Path
import json,os
import FreeCAD as A
root=Path(os.environ['P2S13_ROOT']);cfg=json.loads((root/'configuracao.json').read_text());d=A.openDocument(str(root/cfg['cad_native']))
out=[]
for o in d.Objects:
    if not hasattr(o,'Shape'):continue
    points,tri=o.Shape.tessellate(.15)
    out.append(dict(nome=o.Name,material=o.Material_nominal,vertices=[[v.x,v.y,v.z] for v in points],triangulos=tri))
(root/'visualizacao_local.json').write_text(json.dumps(out));A.closeDocument(d.Name);print('VISUALIZACAO',len(out))
