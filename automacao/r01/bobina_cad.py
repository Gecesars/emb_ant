"""Corpo de prova coaxial de duas portas para isolar o efeito da bobina real da R01."""
import os
import sys
from pathlib import Path
import FreeCAD as App
import Import
import Part

repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo / "freecad/mecanica_R01/fonte"))
import construir as m

out = Path(os.environ["P1H_BOBINA"])
V = App.Vector
x, y, plane = m.DIV_X, -m.N_Y, m.DIV_B


def cylinder(r, z, height):
    return Part.makeCylinder(r, height, V(x, y, z))


def annulus(outer, inner, z, length):
    return cylinder(outer, z, length).cut(cylinder(inner, z, length))


def make(case):
    directory = out / case
    directory.mkdir(exist_ok=True, parents=True)
    d = App.newDocument("Cupom_" + case)

    def export(material, shapes):
        parts = []
        for label, shape in shapes:
            assert shape.isValid() and len(shape.Solids) == 1, label
            obj = d.addObject("Part::Feature", label)
            obj.Shape = shape
            parts.append(obj)
        Import.export(parts, str(directory / (material + ".step")))

    # Referência inferior 4 mm antes da janela. Referência superior 4 mm depois da janela.
    bottom = plane - 8
    center = cylinder(.45975, bottom, 12)
    lower = annulus(1.7905, 1.515, bottom, 4)
    tongues = [m.bx(x-1.75, y-.32, plane-4, .35, .64, 4), m.bx(x-.3, y+1.45, plane-4, .6, .35, 4)]
    flange = annulus(4.0, 1.515, plane, .18)
    upper = annulus(1.7905, 1.515, plane, 4)
    outer = m.union([lower] + tongues + [flange, upper])
    assert len(outer.Solids) == 1
    metals = [("Malha", outer), ("Pino", center)]
    if case == "Com_bobina":
        source = App.newDocument("Cobre_painel")
        Import.insert(str(Path(os.environ["P1H_R01"]) / "cad/copper.step"), source.Name)
        launch = next(o for o in source.Objects if o.Label == "Lancamento_A")
        cropped = launch.Shape.common(m.bx(x-5, y-5, bottom, 10, 10, 8))
        metal = m.union([cropped, cylinder(.45975, plane, 4), flange, upper])
        metals = [("Curto_e_linha", metal)]
        App.closeDocument(source.Name)
    export("copper", metals)
    export("PTFE", [("Isol_in", annulus(1.515,.45975,bottom,4)),
                    ("Isol_out", annulus(1.515,.45975,plane,4))])
    App.closeDocument(d.Name)


for case in ["Com_bobina","Controle"]:
    make(case)
print("CUPONS_OK")
