"""Substituir as duas janelas de entrada da R02 pela bobina coaxial ensaiada."""
import json
import os
import sys
from pathlib import Path

import FreeCAD as App
import Import
import Part


repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo / "freecad/mecanica_R01/fonte"))
import construir as mechanical
from cupons_cad import geometry, origin


V = App.Vector
radius = float(os.environ["P1H_RAIO_BOBINA"])
work = Path(os.environ["P1H_R05_WORK"])
output = work / "cad"
output.mkdir(parents=True, exist_ok=True)
source = Path(os.environ["P1H_CAD_BASE"])
board_bottom = -11.52
new_metal, new_dielectric = geometry(radius)
clip = Part.makeBox(12, 12, 5, origin + V(-6, -6, -5))
metal_chunk = new_metal[0][1].common(clip)
dielectric_chunk = new_dielectric.common(clip)


def positioned(shape, polarity):
    result = shape.copy()
    result.translate(V(0, 2 * mechanical.N_Y if polarity == "B" else 0,
                       board_bottom - origin.z))
    return result


document = App.newDocument("Entradas_R05")
record = {"raio_bobina_mm": radius, "abertura_mm": 1.0, "espiras": 2}
for material, prefix, chunk in [("copper", "Lancamento_", metal_chunk),
                                ("PTFE_cabo", "Isol_IN_", dielectric_chunk)]:
    original = App.newDocument("Original")
    Import.insert(str(source / (material + ".step")), original.Name)
    objects = []
    for polarity in "AB":
        name = prefix + polarity
        old = next(obj.Shape for obj in original.Objects if obj.Label == name)
        lower_clip = Part.makeBox(700, 200, 200, V(-350, -100, board_bottom - 205))
        lower = old.common(lower_clip)
        updated = lower.fuse(positioned(chunk, polarity))
        if material == "copper":
            x, y = origin.x, (-1 if polarity == "A" else 1) * mechanical.N_Y
            barrel = Part.makeCylinder(.525, 1.52, V(x, y, board_bottom))
            flange = Part.makeCylinder(4, .18, V(x, y, board_bottom - .18)).cut(
                Part.makeCylinder(1.515, .18, V(x, y, board_bottom - .18)))
            updated = mechanical.union([updated, barrel, flange])
        updated = updated.removeSplitter()
        assert updated.isValid() and len(updated.Solids) == 1, name
        obj = document.addObject("Part::Feature", name)
        obj.Label = name
        obj.Shape = updated
        objects.append(obj)
        record[name] = dict(volume_mm3=updated.Volume, solids=len(updated.Solids))
    Import.export(objects, str(output / (material + ".step")))
    App.closeDocument(original.Name)
for polarity in "AB":
    conductor = document.getObject("Lancamento_" + polarity).Shape
    insulator = document.getObject("Isol_IN_" + polarity).Shape
    overlap = conductor.common(insulator).Volume
    assert overlap < 1e-5, (polarity, overlap)
record["interferencia_cobre_ptfe_mm3"] = 0
document.recompute()
document.saveAs(str(output / "Entradas_R05.FCStd"))
(output / "verificacao.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
print("ENTRADAS_R05_OK", record)
