# -*- coding: utf-8 -*-
"""Exportar os padrões complexos de cada porta da antena montada com vinte entradas."""
import json
import os
import re
import traceback

import ScriptEnv


ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
folder = os.path.join(os.environ["P1H_R05"], "antena_direta")
output = os.path.join(folder, "padroes")
if not os.path.isdir(output):
    os.makedirs(output)


def log(message):
    with open(os.path.join(folder, "padroes.log"), "a") as stream:
        stream.write(str(message) + "\n")


try:
    with open(os.path.join(folder, "convergencia.txt")) as stream:
        convergence = stream.read()
    assert int(re.search(r"Current Consecutive Passes\s*:\s*(\d+)", convergence).group(1)) >= 2
    project = oDesktop.OpenProject(os.path.join(folder, "Antena_direta.aedt"))
    design = project.SetActiveDesign("Antena_direta")
    solutions = design.GetModule("Solutions")
    ports = list(solutions.GetAllSources())
    assert len(ports) == 20
    reports = design.GetModule("ReportSetup")
    for active in ports:
        sources = [["IncludePortPostProcessing:=", False, "SpecifySystemPower:=", False]] + [
            ["Name:=", port + ":1", "Magnitude:=", "1W" if port == active else "0W", "Phase:=", "0deg"]
            for port in ports]
        solutions.EditSources(sources)
        for axis, phi in [("H", 90), ("V", 0)]:
            name = active + "_" + axis
            reports.CreateReport(name, "Far Fields", "Rectangular Plot", "Centro : LastAdaptive",
                ["Context:=", "HV"],
                ["Theta:=", ["All"], "Phi:=", [str(phi) + "deg"], "Freq:=", ["5.17GHz"]],
                ["X Component:=", "Theta", "Y Component:=", [
                    "re(rETheta)", "im(rETheta)", "re(rEPhi)", "im(rEPhi)", "dB(RealizedGainTotal)"]])
            reports.ExportToFile(name, os.path.join(output, name + ".csv"), False)
            reports.DeleteReports([name])
        log(active)
    solutions.EditSources([["IncludePortPostProcessing:=", False, "SpecifySystemPower:=", False]] + [
        ["Name:=", port + ":1", "Magnitude:=", "0.05W", "Phase:=", "0deg"] for port in ports])
    oDesktop.CloseProject(project.GetName())
    log("PADROES_OK")
except:
    log(traceback.format_exc())
