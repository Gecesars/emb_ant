# -*- coding: utf-8 -*-
"""Resolver o painel no AEDT. P1H_R01 aponta para o diretório local da campanha."""
import os
import traceback
import ScriptEnv

ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
folder = os.path.join(os.environ["P1H_R01"], "estudo")


class CentroSomente(Exception):
    pass


def log(line):
    with open(os.path.join(folder, "solucao.log"), "a") as stream:
        stream.write(str(line) + "\n")


def export_fields(solution, prefix, frequencies):
    for freq in frequencies:
        for axis, phi in [("H", 90), ("V", 0)]:
            name = "%s_%s_%d" % (prefix, axis, freq)
            if name in reports.GetAllReportNames():
                reports.DeleteReports([name])
            reports.CreateReport(name, "Far Fields", "Rectangular Plot", solution, ["Context:=", "HV"],
                ["Theta:=", ["All"], "Phi:=", [str(phi) + "deg"], "Freq:=", [str(freq) + "MHz"]],
                ["X Component:=", "Theta", "Y Component:=", ["dB(RealizedGainTotal)"]])
            path = os.path.join(folder, name + ".csv")
            reports.ExportToFile(name, path, False)
            assert os.path.getsize(path) > 20000, name
            reports.DeleteReports([name])


def export_matrix(solution, filename):
    path = os.path.join(folder, filename)
    solutions.ExportNetworkData("", [solution], 3, path, ["All"], True, 50, "S", -1, 1, 15, False, True, False)
    assert os.path.isfile(path)


try:
    project = oDesktop.OpenProject(os.path.join(folder, os.environ.get("P1H_NOME","P1H_R01")+".aedt"))
    design = project.SetActiveDesign("Painel_montado")
    solutions = design.GetModule("Solutions")
    reports = design.GetModule("ReportSetup")
    setup = design.GetModule("AnalysisSetup")
    assert len(solutions.GetAllSources()) == 2
    if os.environ.get("P1H_ITERATIVO") == "1":
        order=int(os.environ.get("P1H_ORDEM","-1"))
        assert order in (-1,0,1)
        setup.EditSetup("Banda", ["NAME:Banda", "SolveType:=", "Single", "Frequency:=", "5.17GHz",
            "MaxDeltaS:=", .015, "MaximumPasses:=", 15, "MinimumPasses:=", 3, "MinimumConvergedPasses:=", 2,
            "PercentRefinement:=", 15, "BasisOrder:=", order, "DrivenSolverType:=", "Iterative Solver",
            "IterativeResidual:=", .00001, "SaveAnyFields:=", True, "SaveRadFieldsOnly:=", False])
        project.Save()
    assert design.ValidateDesign() == 1
    log("ADAPTATIVO_INICIADO")
    design.Analyze("Banda")
    log(list(oDesktop.GetMessages(project.GetName(), design.GetName(), 2)))
    design.ExportConvergence("Banda", "", os.path.join(folder, "convergencia.txt"))
    assert "Converged : Yes" in open(os.path.join(folder, "convergencia.txt")).read(), "Sem convergencia"
    export_matrix("Banda : LastAdaptive", "centro.s2p")
    export_fields("Banda : LastAdaptive", "Centro", [5170])
    project.Save()
    log("CENTRO_CONVERGIDO")
    if os.environ.get("P1H_SOMENTE_CENTRO")=="1":
        oDesktop.CloseProject(project.GetName())
        raise CentroSomente()
    sweep = "Discreta_10MHz"
    if sweep not in setup.GetSweeps("Banda"):
        setup.InsertFrequencySweep("Banda", ["NAME:" + sweep, "IsEnabled:=", True,
            "RangeType:=", "LinearStep", "RangeStart:=", "5090MHz", "RangeEnd:=", "5250MHz",
            "RangeStep:=", "10MHz", "Type:=", "Discrete", "SaveFields:=", True, "SaveRadFields:=", True])
    project.Save()
    design.Analyze("Banda")
    log(list(oDesktop.GetMessages(project.GetName(), design.GetName(), 2)))
    export_matrix("Banda : " + sweep, "painel.s2p")
    export_fields("Banda : " + sweep, "Discreta", range(5090, 5251, 10))
    project.Save()
    log("FEM_OK")
except CentroSomente:
    pass
except:
    log(traceback.format_exc())
