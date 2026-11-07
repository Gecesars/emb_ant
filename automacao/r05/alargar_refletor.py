"""Alargar a alma e deslocar as nervuras, preservando furos e flange inferior da R02."""
import json
import os
from pathlib import Path

import FreeCAD as App
import Import
import Part


source = Path(os.environ["P1H_CAD_BASE"]) / "AL5052.step"
output = Path(os.environ["P1H_R05"]) / "refletor"
output.mkdir(parents=True, exist_ok=True)
width = float(os.environ.get("P1H_FACE_MM", "40"))
extra = (width - 36) / 2
assert 0 < extra <= 6
doc = App.newDocument("Refletor_largura")
Import.insert(str(source), doc.Name)
original = [obj for obj in doc.Objects if hasattr(obj, "Shape") and obj.Shape.Volume > 0]
assert len(original) == 1
base = original[0].Shape.copy()
original[0].Label = "Refletor_R02_36mm"
pieces = []
for side in [-1, 1]:
    cutter = Part.makeBox(600, 100, 100, App.Vector(-252, 18 if side > 0 else -118, -50))
    rib = base.common(cutter)
    base = base.cut(cutter)
    assert not rib.isNull()
    rib.translate(App.Vector(0, side * extra, 0))
    pieces.append(rib)
    pieces.append(Part.makeBox(510, extra, 2, App.Vector(-252, 18 if side > 0 else -18-extra, -2)))
    points = [App.Vector(x, side*y, -2) for x,y in [(-259,41),(-252,18),(-252,18+extra)]]
    pieces.append(Part.Face(Part.makePolygon(points + points[:1])).extrude(App.Vector(0,0,2)))
shape = base.multiFuse(pieces).removeSplitter()
assert shape.isValid() and len(shape.Solids) == 1
obj = doc.addObject("Part::Feature", "Refletor_R05")
obj.Shape = shape
obj.addProperty("App::PropertyLength", "LarguraAlma", "Dimensoes").LarguraAlma = width
doc.recompute()
doc.saveAs(str(output / "Refletor.FCStd"))
Import.export([obj], str(output / "AL5052.step"))
(output / "verificacao.json").write_text(json.dumps(dict(largura_mm=width, solidos=1,
    valido=shape.isValid(), volume_mm3=shape.Volume,
    origem=str(source), metodo="Translacao das nervuras e extensao da alma; furos preservados"), indent=2), encoding="utf8")
print("REFLETOR_OK", width, shape.Volume)
