# -*- coding: utf-8 -*-
"""Exportar ganho aceito e diretividade do campo convergido sem executar nova solução."""
import os
import traceback

import ScriptEnv


ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
folder = os.path.join(os.environ["P1H_R01"], "estudo")
try:
    project = oDesktop.OpenProject(os.path.join(folder, os.environ["P1H_NOME"] + ".aedt"))
    design = project.SetActiveDesign("Painel_montado")
    solution = design.GetModule("Solutions")
    source_settings = [["IncludePortPostProcessing:=", False, "SpecifySystemPower:=", False]]
    source_settings.extend([
        ["Name:=", "N_" + pol + ":1", "Magnitude:=", "0.5W", "Phase:=", "0deg"]
        for pol in "AB"
    ])
    solution.EditSources(source_settings)
    reports = design.GetModule("ReportSetup")
    name = "Balanco_frontal"
    if name in reports.GetAllReportNames():
        reports.DeleteReports([name])
    reports.CreateReport(
        name, "Far Fields", "Rectangular Plot", "Banda : LastAdaptive",
        ["Context:=", "HV"],
        ["Theta:=", ["0deg"], "Phi:=", ["90deg"], "Freq:=", ["5.17GHz"]],
        ["X Component:=", "Freq", "Y Component:=", [
            "dB(DirTotal)", "dB(GainTotal)", "dB(RealizedGainTotal)"
        ]]
    )
    destination = os.path.join(folder, "diretividade_Centro.csv")
    reports.ExportToFile(name, destination, False)
    assert os.path.getsize(destination) > 100
    reports.DeleteReports([name])
    oDesktop.CloseProject(project.GetName())
    with open(os.path.join(folder, "balanco.ok"), "w") as stream:
        stream.write("OK")
except:
    with open(os.path.join(folder, "balanco.err"), "w") as stream:
        stream.write(traceback.format_exc())
