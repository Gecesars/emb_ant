# -*- coding: utf-8 -*-
"""Recalcular os divisores compactos com Cu/NiP/Au e faces orientadas no HFSS."""
import json
import math
import os
import re
import traceback
import ScriptEnv

ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
root = os.environ["P1H_ENIG"]


def log(value):
    with open(os.path.join(root, "enig.log"), "a") as stream:
        stream.write(str(value) + "\n")


try:
    for kind, ports in [("1x2", 6), ("1x5", 12)]:
        output = os.path.join(root, kind)
        project = oDesktop.OpenProject(os.path.join(output, "ENIG_" + kind + ".aedt"))
        design = project.SetActiveDesign("Duplo_radial")
        editor = design.SetActiveEditor("3D Modeler")
        boundaries = design.GetModule("BoundarySetup")
        geometry = json.load(open(os.path.join(output, "geometria.json")))
        # ENIG somente nas faces expostas. Sob pinos e solda existe metal
        # volumetrico; tais patches nao admitem shell entre dois dieletricos.
        for port, x, y in geometry["ports"]:
            for blank, radius, z in [("GND", 2.13, 0), ("Anel_" + port, .525, 0),
                                      ("Estrela_" + port[0], .74, geometry["h"])]:
                tool = "Recorte_ENIG_" + blank + "_" + port
                editor.CreateCircle(["NAME:CircleParameters", "IsCovered:=", True,
                    "XCenter:=", str(x)+"mm", "YCenter:=", str(y)+"mm", "ZCenter:=", str(z)+"mm",
                    "Radius:=", str(radius)+"mm", "WhichAxis:=", "Z", "NumSegments:=", "24"],
                    ["NAME:Attributes", "Name:=", tool, "MaterialValue:=", '"vacuum"', "SolveInside:=", True])
                editor.Subtract(["NAME:Selections", "Blank Parts:=", blank, "Tool Parts:=", tool],
                    ["NAME:SubtractParameters", "KeepOriginals:=", False])
        # Shell elements nao aceitam Roughness. Reproduzir Groiss do cobre
        # por sigma efetiva no extremo superior da banda (limite conservador).
        skin = math.sqrt(1 / (math.pi * 5.25e9 * (4*math.pi*1e-7) * 5.8e7))
        correction = 1 + math.exp(-(skin / (2*.5e-6))**1.6)
        copper_conductivity = 5.8e7 / correction**2
        for name, conductivity in [("NiP_estimado", 1.5e6), ("Ouro_nom", 4.1e7),
                                   ("Cobre_Groiss_equivalente", copper_conductivity)]:
            project.GetDefinitionManager().AddMaterial(["NAME:" + name,
                "CoordinateSystemType:=", "Cartesian", "BulkOrSurfaceType:=", 1,
                ["NAME:PhysicsTypes", "set:=", ["Electromagnetic"]],
                "conductivity:=", str(conductivity), "permeability:=", "1"])
        names = [name for name in editor.GetObjectsInGroup("Sheets")
                 if name == "GND" or name.startswith(("Estrela_", "Anel_"))]
        assert len(names) == ports + 3
        orientations = {}
        groups = {True: [], False: []}
        for name in names:
            # Verificar a normal nativa: espessar apenas uma copia descartavel.
            before = set(editor.GetObjectsInGroup("Sheets"))
            original_z = [float(editor.GetVertexPosition(v)[2]) for v in editor.GetVertexIDsFromObject(name)]
            assert max(original_z) - min(original_z) < 1e-7
            z = original_z[0]
            editor.DuplicateAlongLine(["NAME:Selections", "Selections:=", name, "NewPartsModelFlag:=", "Model"],
                ["NAME:DuplicateToAlongLineParameters", "CreateNewObjects:=", True,
                 "XComponent:=", "0mm", "YComponent:=", "0mm", "ZComponent:=", "100mm", "Numclones:=", "2"],
                ["NAME:Options", "DuplicateAssignments:=", False])
            copies = set(editor.GetObjectsInGroup("Sheets")) - before
            assert len(copies) == 1
            copy_name = list(copies)[0]
            editor.ThickenSheet(["NAME:Selections", "Selections:=", copy_name, "NewPartsModelFlag:=", "Model"],
                ["NAME:SheetThickenParameters", "Thickness:=", "1mm", "BothSides:=", False])
            probe_z = [float(editor.GetVertexPosition(v)[2]) for v in editor.GetVertexIDsFromObject(copy_name)]
            normal = 1 if max(probe_z) > z + 100.5 else -1
            assert abs((max(probe_z) - min(probe_z)) - 1) < 1e-6
            editor.Delete(["NAME:Selections", "Selections:=", copy_name])
            outward = 1 if name.startswith("Estrela_") else -1
            groups[normal == outward].append(name)
            orientations[name] = dict(z_mm=z, normal=normal, exposto=outward)
        boundaries.DeleteBoundaries(["Cobre_35um"])
        for gold_first, objects in groups.items():
            if not objects:
                continue
            layers = [("Ouro_nom", ".0254um"), ("NiP_estimado", "4.5um"), ("Cobre_Groiss_equivalente", "35um")]
            if not gold_first:
                layers.reverse()
            data = ["NAME:Layers"] + [["NAME:Layer%d" % (i+1), "Thickness:=", thickness,
                "Material:=", material] for i, (material, thickness) in enumerate(layers)]
            boundaries.AssignLayeredImp(["NAME:ENIG_" + ("direto" if gold_first else "inverso"),
                "Objects:=", objects, "Frequency:=", "0GHz", "Roughness:=", "0um",
                "IsTwoSided:=", True, "IsShellElement:=", True, data, "InfGroundPlane:=", False])
        with open(os.path.join(output, "orientacoes.json"), "w") as stream:
            json.dump(orientations, stream, indent=2)
        setup = design.GetModule("AnalysisSetup")
        setup.EditSetup("Divisor", ["NAME:Divisor", "Frequency:=", "5.17GHz", "MaxDeltaS:=", .012,
            "MaximumPasses:=", 16, "MinimumPasses:=", 3, "MinimumConvergedPasses:=", 2,
            "PercentRefinement:=", 24, "BasisOrder:=", 1])
        if "Banda" not in setup.GetSweeps("Divisor"):
            setup.InsertFrequencySweep("Divisor", ["NAME:Banda", "IsEnabled:=", True,
                "RangeType:=", "LinearStep", "RangeStart:=", "5090MHz", "RangeEnd:=", "5250MHz",
                "RangeStep:=", "10MHz", "Type:=", "Discrete", "SaveFields:=", False, "SaveRadFields:=", False])
        assert design.ValidateDesign() == 1
        project.Save()
        log(kind + " SOLVENDO_ENIG")
        design.Analyze("Divisor")
        convergence_path = os.path.join(output, "convergencia.txt")
        design.ExportConvergence("Divisor", "", convergence_path)
        convergence = open(convergence_path).read()
        assert int(re.search(r"Current Consecutive Passes\s*:\s*(\d+)", convergence).group(1)) >= 2
        design.GetModule("Solutions").ExportNetworkData("", ["Divisor : Banda"], 3,
            os.path.join(output, "divisor.s%dp" % ports), ["All"], True, 50, "S", -1, 1, 15, False, True, False)
        project.Save()
        oDesktop.CloseProject(project.GetName())
        log(kind + " ENIG_OK")
except:
    log(traceback.format_exc())
