"""Inspecao somente de leitura do refletor; executar em FreeCAD headless."""
import FreeCAD as A
import json
from pathlib import Path

ROOT = Path('D:/dev/EMBRAER/P2S13/R00_Refletor_Dobrado')
rows = []
for case in sorted(ROOT.glob('v*/P2S13.FCStd')):
    doc = A.openDocument(str(case))
    shape = doc.getObject('Refletor_Al2mm').Shape
    row = dict(caso=case.parent.name, valido=shape.isValid(),
               solidos=len(shape.Solids), faces=len(shape.Faces),
               arestas=len(shape.Edges), volume_mm3=shape.Volume,
               menores_arestas_mm=sorted(e.Length for e in shape.Edges)[:12],
               menores_areas_mm2=sorted(f.Area for f in shape.Faces)[:12],
               tipos_faces={})
    for face in shape.Faces:
        key = type(face.Surface).__name__
        row['tipos_faces'][key] = row['tipos_faces'].get(key, 0) + 1
    rows.append(row)
    A.closeDocument(doc.Name)
(ROOT / 'diagnostico_dobras_cad.json').write_text(json.dumps(rows, indent=2) + '\n')
print(json.dumps(rows, indent=2))
