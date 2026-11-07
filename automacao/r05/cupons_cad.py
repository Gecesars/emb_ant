"""Comparar a entrada coaxial com abertura localizada e três bobinas de duas espiras."""
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


V = App.Vector
origin = V(mechanical.DIV_X, -mechanical.N_Y, mechanical.DIV_B)
destination = Path(os.environ["P1H_R05"]) / "cupons"


def cylinder(radius, bottom, height):
    return Part.makeCylinder(radius, height, origin + V(0, 0, bottom))


def ring(outer, inner, bottom, height):
    return cylinder(outer, bottom, height).cut(cylinder(inner, bottom, height))


def lead(start, end):
    return Part.makeCylinder(.15, (end - start).Length, start, end - start)


def geometry(radius):
    center = cylinder(.45975, -8, 12)
    # Abertura radial de 1 mm para soldar o fio, preservando o restante da blindagem.
    window = Part.makeCylinder(.5, 2.4, origin + V(0, 0, -2.8), V(1, 0, 0))
    shield = ring(1.7905, 1.515, -8, 12).cut(window)
    shield = shield.fuse(ring(4, 1.515, 0, .18)).removeSplitter()
    dielectric = ring(1.515, .45975, -8, 12).cut(window)
    metals = [("Blindagem", shield), ("Pino", center)]
    if radius:
        helix = Part.makeHelix(.73, 1.46, radius)
        helix.rotate(V(), V(0, 1, 0), 90)
        helix.translate(origin + V(2.2, 0, -2.8 + radius))
        first = helix.Edges[0].valueAt(helix.Edges[0].FirstParameter)
        last = helix.Edges[-1].valueAt(helix.Edges[-1].LastParameter)
        pin_contact = origin + V(0, 0, -2.8)
        ground_contact = origin + V(1.70, 0, -4.3)
        coil = mechanical.tube(Part.Wire(helix.Edges), .15)
        pieces = [shield, center, coil, lead(pin_contact, first), lead(last, ground_contact),
                  Part.makeSphere(.18, first), Part.makeSphere(.18, last),
                  Part.makeSphere(.18, ground_contact)]
        metal = mechanical.union(pieces)
        assert len(metal.Solids) == 1, "Curto em CC interrompido"
        assert metal.common(dielectric).Volume < 1e-7, "Metal penetra no PTFE"
        metals = [("Linha_e_bobina", metal)]
    assert dielectric.isValid() and len(dielectric.Solids) == 1
    return metals, dielectric


def export_case(name, radius):
    folder = destination / name
    folder.mkdir(parents=True, exist_ok=True)
    doc = App.newDocument(name)
    metals, dielectric = geometry(radius)
    for material, shapes in [("copper", metals), ("PTFE", [("Dieletrico", dielectric)])]:
        objects = []
        for label, shape in shapes:
            assert shape.isValid() and len(shape.Solids) == 1
            obj = doc.addObject("Part::Feature", label)
            obj.Shape = shape
            objects.append(obj)
        Import.export(objects, str(folder / (material + ".step")))
    doc.recompute()
    doc.saveAs(str(folder / (name + ".FCStd")))
    App.closeDocument(doc.Name)
    return dict(nome=name, raio_medio_mm=radius, espiras=2 if radius else 0,
                passo_mm=.73, fio_mm=.30, abertura_mm=1.0,
                planos_z_mm=[origin.z - 8, origin.z + 4])


if __name__ == "__main__":
    cases = [("Controle_fechado", 0), ("Bobina_r065", .65),
             ("Bobina_r075", .75), ("Bobina_r090", .90)]
    records = [export_case(name, radius) for name, radius in cases]
    (destination / "casos.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    print("CUPONS_R05_OK", len(records))
