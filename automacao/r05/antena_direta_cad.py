"""Extrair a placa contínua com refletor e vinte planos de alimentação para diagnóstico."""
import json
import os
import sys
from pathlib import Path

import FreeCAD as App
import Import
import Part


repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo / "freecad/mecanica_R01/fonte"))
from dimensoes import PIN, PASSO


source = Path(os.environ["P1H_CAD_BASE"])
destination = Path(os.environ["P1H_R05"]) / "antena_direta"
cad = destination / "cad"
cad.mkdir(parents=True, exist_ok=True)
doc = App.newDocument("Antena_direta")
clip = Part.makeBox(700, 200, 100, App.Vector(-350, -100, -4))
rules = {
    "AL5052": ("",),
    "RO4350B_R01": ("",),
    "POM_nom": ("Berco_", "Batente_"),
    "Silicone_nom": ("Passa_",),
    "aco_nom": ("Par_", "Arruela_"),
    "folha_cu": ("Ant",),
    "copper": ("Via", "Sinal_INF_", "Sinal_SUP_", "Capa_INF_", "Capa_SUP_"),
    "PTFE_cabo": ("Isol_INF_", "Isol_SUP_"),
}
manifest = {}
for material, prefixes in rules.items():
    imported = App.newDocument("Origem")
    input_path = Path(os.environ["P1H_REFLETOR_STEP"]) if material == "AL5052" and os.environ.get("P1H_REFLETOR_STEP") else source / (material + ".step")
    Import.insert(str(input_path), imported.Name)
    objects = []
    for original in imported.Objects:
        if original.TypeId != "Part::Feature":
            continue
        name = original.Label
        if not name.startswith(prefixes):
            continue
        shape = original.Shape.copy()
        if name.startswith(("Sinal_", "Capa_", "Isol_")):
            shape = shape.common(clip)
        if material == "aco_nom" and shape.BoundBox.ZMax <= 0:
            continue
        assert shape.isValid() and not shape.isNull(), name
        obj = doc.addObject("Part::Feature", name)
        obj.Label = name
        obj.Shape = shape
        objects.append(obj)
        manifest[name] = material
    assert objects, material
    Import.export(objects, str(cad / (material + ".step")))
    App.closeDocument(imported.Name)
ports = [dict(name="E%02d_%s" % (i + 1, pol),
              x=(i - 4.5) * PASSO + PIN, y=sign * PIN, z=-4)
         for i in range(10) for pol, sign in [("A", -1), ("B", 1)]]
(cad / "portas.json").write_text(json.dumps(ports, indent=2), encoding="utf-8")
(cad / "manifesto.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print("ANTENA_DIRETA_CAD_OK", len(manifest))
