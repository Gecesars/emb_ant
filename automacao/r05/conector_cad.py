"""Extrair o modelo nominal do N para aferir sua transição separadamente."""
import os
from pathlib import Path

import FreeCAD as App
import Import


source = Path(os.environ["P1H_CAD_BASE"])
output = Path(os.environ["P1H_R05"]) / "cupons/Conector_N"
output.mkdir(parents=True, exist_ok=True)
for material, names, filename in [
    ("latao_nom", ["N_corpo_A", "N_pino_A"], "copper.step"),
    ("PTFE_cabo", ["N_isol_A"], "PTFE.step")
]:
    document = App.newDocument("Conector")
    Import.insert(str(source / (material + ".step")), document.Name)
    objects = [obj for obj in document.Objects if obj.Label in names]
    assert len(objects) == len(names)
    Import.export(objects, str(output / filename))
    App.closeDocument(document.Name)
print("CONECTOR_CAD_OK")
