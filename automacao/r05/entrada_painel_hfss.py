# -*- coding: utf-8 -*-
"""Aplicar as entradas R05 numa cópia nativa da montagem contínua R02."""
import os
import traceback

import ScriptEnv


ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
folder = os.environ["P1H_R05_WORK"]
filename = os.path.join(folder, "estudo", "P1H_R05.aedt")


def log(message):
    with open(os.path.join(folder, "estudo", "modelo.log"), "a") as stream:
        stream.write(str(message) + "\n")


try:
    project = oDesktop.OpenProject(filename)
    design = project.SetActiveDesign("Painel_montado")
    editor = design.SetActiveEditor("3D Modeler")
    replacements = ["Lancamento_A", "Lancamento_B", "Isol_IN_A", "Isol_IN_B"]
    assert set(replacements).issubset(set(editor.GetObjectsInGroup("Solids")))
    editor.Delete(["NAME:Selections", "Selections:=", ",".join(replacements)])
    for material in ["copper", "PTFE_cabo"]:
        before = set(editor.GetObjectsInGroup("Solids"))
        editor.Import(["NAME:NativeBodyParameters", "HealOption:=", 0, "Options:=", "-1",
            "FileType:=", "UnRecognized", "MaxStitchTol:=", -1, "ImportFreeSurfaces:=", True,
            "GroupByAssembly:=", False, "CreateGroup:=", False, "MergeFacesAngle:=", -1,
            "PointCoincidenceTol:=", 1e-6, "CreateLightweightPart:=", False,
            "ImportMaterialNames:=", False, "SeparateDisjointLumps:=", True,
            "SourceFile:=", os.path.join(folder, "cad", material + ".step"), "STLFileUnit:=", "mm"])
        names = sorted(set(editor.GetObjectsInGroup("Solids")) - before)
        assert len(names) == 2, names
        editor.AssignMaterial(["NAME:Selections", "Selections:=", ",".join(names)],
            ["NAME:Attributes", "MaterialValue:=", '"' + material + '"',
             "SolveInside:=", material == "PTFE_cabo"])
    project.Save()
    valid = design.ValidateDesign()
    log(("validacao", valid, list(oDesktop.GetMessages(project.GetName(), design.GetName(), 2))))
    assert valid == 1
    project.Save()
    oDesktop.CloseProject(project.GetName())
    log("MODELO_R05_OK")
except:
    log(traceback.format_exc())
