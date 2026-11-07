# -*- coding: utf-8 -*-
"""Diagnóstico com vinte fontes nas terminações coaxiais da placa contínua e mecânica."""
import json
import os
import traceback

import ScriptEnv


ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
folder = os.path.join(os.environ["P1H_R05"], "antena_direta")
cad = os.path.join(folder, "cad")


def log(message):
    with open(os.path.join(folder, "solucao.log"), "a") as stream:
        stream.write(str(message) + "\n")


def mm(value):
    return "%.12gmm" % value


try:
    project = oDesktop.NewProject()
    project.InsertDesign("HFSS", "Antena_direta", "DrivenModal", "")
    design = project.SetActiveDesign("Antena_direta")
    editor = design.SetActiveEditor("3D Modeler")
    editor.SetModelUnits(["NAME:Units Parameter", "Units:=", "mm", "Rescale:=", False])
    boundaries = design.GetModule("BoundarySetup")
    definitions = project.GetDefinitionManager()
    dielectrics = {"POM_nom": (3.4, .01), "Silicone_nom": (2.77, .02),
                   "RO4350B_R01": (3.66, .0037), "PTFE_cabo": (2.036363533774732, .00027683054882040843)}
    conductors = {"AL5052": 2e7, "aco_nom": 1.4e6}
    for name, values in dielectrics.items():
        definitions.AddMaterial(["NAME:" + name, "CoordinateSystemType:=", "Cartesian",
            "BulkOrSurfaceType:=", 1, ["NAME:PhysicsTypes", "set:=", ["Electromagnetic"]],
            "permittivity:=", str(values[0]), "dielectric_loss_tangent:=", str(values[1])])
    for name, conductivity in conductors.items():
        definitions.AddMaterial(["NAME:" + name, "CoordinateSystemType:=", "Cartesian",
            "BulkOrSurfaceType:=", 1, ["NAME:PhysicsTypes", "set:=", ["Electromagnetic"]],
            "conductivity:=", str(conductivity)])
    for material in sorted(list(dielectrics) + list(conductors) + ["copper", "folha_cu"]):
        group = "Sheets" if material == "folha_cu" else "Solids"
        previous = set(editor.GetObjectsInGroup(group))
        editor.Import(["NAME:NativeBodyParameters", "HealOption:=", 0, "Options:=", "-1",
            "FileType:=", "UnRecognized", "MaxStitchTol:=", -1, "ImportFreeSurfaces:=", True,
            "GroupByAssembly:=", False, "CreateGroup:=", False, "MergeFacesAngle:=", -1,
            "PointCoincidenceTol:=", 1e-6, "CreateLightweightPart:=", False,
            "ImportMaterialNames:=", False, "SeparateDisjointLumps:=", True,
            "SourceFile:=", os.path.join(cad, material + ".step"), "STLFileUnit:=", "mm"])
        names = sorted(set(editor.GetObjectsInGroup(group)) - previous)
        assert names, material
        if material == "folha_cu":
            boundaries.AssignFiniteCond(["NAME:Cobre_35um", "Objects:=", names,
                "UseMaterial:=", True, "Material:=", "copper", "UseThickness:=", True,
                "Thickness:=", "0.035mm", "Roughness:=", "0.5um", "InfGroundPlane:=", False,
                "IsTwoSided:=", False])
        else:
            editor.AssignMaterial(["NAME:Selections", "Selections:=", ",".join(names)],
                ["NAME:Attributes", "MaterialValue:=", '"' + material + '"',
                 "SolveInside:=", material in dielectrics])
    ports = json.load(open(os.path.join(cad, "portas.json")))
    for port in ports:
        name, x, y, z = [port[key] for key in ["name", "x", "y", "z"]]
        for suffix, radius in [("_externo", 1.515), ("_interno", .45975)]:
            editor.CreateCircle(["NAME:CircleParameters", "IsCovered:=", True,
                "XCenter:=", mm(x), "YCenter:=", mm(y), "ZCenter:=", mm(z),
                "Radius:=", mm(radius), "WhichAxis:=", "Z", "NumSegments:=", "0"],
                ["NAME:Attributes", "Name:=", name + suffix, "MaterialValue:=", '"vacuum"', "SolveInside:=", True])
        editor.Subtract(["NAME:Selections", "Blank Parts:=", name + "_externo",
            "Tool Parts:=", name + "_interno"], ["NAME:SubtractParameters", "KeepOriginals:=", False])
        boundaries.AssignLumpedPort(["NAME:" + name, "Objects:=", [name + "_externo"],
            "DoDeembed:=", False, "RenormalizeAllTerminals:=", True,
            ["NAME:Modes", ["NAME:Mode1", "ModeNum:=", 1, "UseIntLine:=", True,
             ["NAME:IntLine", "Start:=", [mm(x + .45975), mm(y), mm(z)],
              "End:=", [mm(x + 1.515), mm(y), mm(z)]], "AlignmentGroup:=", 0,
             "CharImp:=", "Zpi", "RenormImp:=", "50ohm"]], "Impedance:=", "50ohm"])
    design.GetModule("ModelSetup").CreateOpenRegion(["NAME:Settings", "OpFreq:=", "5.09GHz",
        "Boundary:=", "Radiation", "ApplyInfiniteGP:=", False])
    design.GetModule("RadField").InsertInfiniteSphereSetup(["NAME:HV",
        "UseCustomRadiationSurface:=", False, "CSDefinition:=", "Theta-Phi", "Polarization:=", "Linear",
        "ThetaStart:=", "-180deg", "ThetaStop:=", "180deg", "ThetaStep:=", "0.25deg",
        "PhiStart:=", "0deg", "PhiStop:=", "90deg", "PhiStep:=", "90deg", "UseLocalCS:=", False])
    analysis = design.GetModule("AnalysisSetup")
    analysis.InsertSetup("HfssDriven", ["NAME:Centro", "SolveType:=", "Single", "Frequency:=", "5.17GHz",
        "MaxDeltaS:=", .012, "MaximumPasses:=", 16, "MinimumPasses:=", 3,
        "MinimumConvergedPasses:=", 2, "PercentRefinement:=", 20, "BasisOrder:=", -1,
        "DrivenSolverType:=", "Iterative Solver", "IterativeResidual:=", .00001,
        "SaveAnyFields:=", True, "SaveRadFieldsOnly:=", False])
    solutions = design.GetModule("Solutions")
    solutions.EditSources([["IncludePortPostProcessing:=", False, "SpecifySystemPower:=", False]] + [
        ["Name:=", port["name"] + ":1", "Magnitude:=", "0.05W", "Phase:=", "0deg"] for port in ports])
    project.SaveAs(os.path.join(folder, "Antena_direta.aedt"), True)
    valid = design.ValidateDesign()
    log(("validacao", valid, list(oDesktop.GetMessages(project.GetName(), design.GetName(), 2))))
    assert valid == 1
    log("SOLVER_CENTRO")
    design.Analyze("Centro")
    design.ExportConvergence("Centro", "", os.path.join(folder, "convergencia.txt"))
    solutions.ExportNetworkData("", ["Centro : LastAdaptive"], 3, os.path.join(folder, "antena.s20p"),
        ["All"], True, 50, "S", -1, 1, 15, False, True, False)
    reports = design.GetModule("ReportSetup")
    for axis, phi in [("H", 90), ("V", 0)]:
        reports.CreateReport(axis, "Far Fields", "Rectangular Plot", "Centro : LastAdaptive",
            ["Context:=", "HV"], ["Theta:=", ["All"], "Phi:=", [str(phi) + "deg"], "Freq:=", ["5.17GHz"]],
            ["X Component:=", "Theta", "Y Component:=", [
                "dB(RealizedGainTotal)", "dB(GainTotal)", "dB(DirTotal)"]])
        reports.ExportToFile(axis, os.path.join(folder, "Centro_" + axis + ".csv"), False)
    project.Save()
    oDesktop.CloseProject(project.GetName())
    log("ANTENA_DIRETA_OK")
except:
    log(traceback.format_exc())
