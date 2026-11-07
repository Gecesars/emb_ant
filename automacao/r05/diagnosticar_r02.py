# -*- coding: utf-8 -*-
"""Extrair campos e perdas da solução R02 existente, sem nova análise."""
import json
import os
import traceback

import ScriptEnv


ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
destination = os.environ["P1H_R05"]
source = os.environ["P1H_DIAGNOSTICO"]


def log(message):
    with open(os.path.join(destination, "diagnostico.log"), "a") as stream:
        stream.write(str(message) + "\n")


def set_sources(a, b):
    solutions.EditSources([
        ["IncludePortPostProcessing:=", False, "SpecifySystemPower:=", False],
        ["Name:=", "N_A:1", "Magnitude:=", str(a) + "W", "Phase:=", "0deg"],
        ["Name:=", "N_B:1", "Magnitude:=", str(b) + "W", "Phase:=", "0deg"]
    ])


def integrate_loss(name, volume):
    fields.CalcStack("clear")
    fields.EnterQty("VolumeLossDensity" if volume else "SurfaceLossDensity")
    if volume:
        fields.EnterVol(name)
    else:
        fields.EnterSurf(name)
    fields.CalcOp("Integrate")
    path = os.path.join(destination, "loss_scalar.fld")
    fields.CalculatorWrite(path, ["Solution:=", "Banda : LastAdaptive"],
                           ["Freq:=", "5.17GHz", "Phase:=", "0deg"])
    with open(path) as stream:
        return float(stream.readlines()[-1].strip())


try:
    project = oDesktop.OpenProject(source)
    design = project.SetActiveDesign("Painel_montado")
    editor = design.SetActiveEditor("3D Modeler")
    solutions = design.GetModule("Solutions")
    reports = design.GetModule("ReportSetup")
    fields = design.GetModule("FieldsReporter")
    set_sources(.5, .5)
    records = []
    solids = list(editor.GetObjectsInGroup("Solids"))
    sheets = list(editor.GetObjectsInGroup("Sheets"))
    with open(os.path.join(destination, "objetos_r02.json"), "w") as stream:
        json.dump({"solids": solids, "sheets": sheets}, stream, indent=2)
    volumes = [name for name in solids if name.startswith((
        "RO4350", "PCB_", "Berco_", "Trilho_", "Isol_", "N_isol_"
    )) and "par" not in name]
    surfaces = [name for name in solids + sheets if name.startswith((
        "Lancamento_", "N_corpo_", "N_pino_", "Estrela_", "Massa_"
    ))]
    for volume, names in [(True, volumes), (False, surfaces)]:
        for name in names:
            value = integrate_loss(name, volume)
            records.append({"objeto": name, "volume": volume, "watts": value})
            log((name, value))
            with open(os.path.join(destination, "perdas_r02.json"), "w") as stream:
                json.dump(records, stream, indent=2)
    for label, a, b in [("A", 1, 0), ("B", 0, 1)]:
        set_sources(a, b)
        for axis, phi in [("H", 90), ("V", 0)]:
            name = "Diagnostico_" + label + "_" + axis
            reports.CreateReport(
                name, "Far Fields", "Rectangular Plot", "Banda : LastAdaptive",
                ["Context:=", "HV"],
                ["Theta:=", ["All"], "Phi:=", [str(phi) + "deg"], "Freq:=", ["5.17GHz"]],
                ["X Component:=", "Theta", "Y Component:=", [
                    "re(rETheta)", "im(rETheta)", "re(rEPhi)", "im(rEPhi)",
                    "dB(RealizedGainTotal)"
                ]]
            )
            reports.ExportToFile(name, os.path.join(destination, name + ".csv"), False)
            reports.DeleteReports([name])
    set_sources(.5, .5)
    oDesktop.CloseProject(project.GetName())
    log("DIAGNOSTICO_OK")
except:
    log(traceback.format_exc())
