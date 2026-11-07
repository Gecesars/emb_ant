# -*- coding: utf-8 -*-
"""Resolver os dois corpos de prova do lançamento coaxial no HFSS 2024 R2."""
import os
import traceback
import ScriptEnv

ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
root = os.environ["P1H_BOBINA"]


def log(message):
    with open(os.path.join(root, "cupom.log"), "a") as f:
        f.write(str(message) + "\n")


def mm(x):
    return "%.12gmm" % x


def make_port(editor, boundaries, name, z, x=2.50916841304063, y=-19.25,
              axis="Z", inner=.45975, outer=1.515):
    sheet = "Secao_" + name
    inside = "Interior_" + name
    for obj, rad in [(sheet, outer), (inside, inner)]:
        editor.CreateCircle(["NAME:CircleParameters", "IsCovered:=", True, "XCenter:=", mm(x), "YCenter:=", mm(y),
            "ZCenter:=", mm(z), "Radius:=", mm(rad), "WhichAxis:=", axis, "NumSegments:=", "0"],
            ["NAME:Attributes", "Name:=", obj, "MaterialValue:=", '"vacuum"', "SolveInside:=", True])
    editor.Subtract(["NAME:Selections","Blank Parts:=",sheet,"Tool Parts:=",inside],["NAME:SubtractParameters","KeepOriginals:=",False])
    if axis == "X":
        start, end = [mm(x), mm(y + inner), mm(z)], [mm(x), mm(y + outer), mm(z)]
    else:
        start, end = [mm(x + inner), mm(y), mm(z)], [mm(x + outer), mm(y), mm(z)]
    bounds = ["NAME:IntLine", "Start:=", start, "End:=", end]
    boundaries.AssignLumpedPort(["NAME:" + name, "Objects:=", [sheet], "DoDeembed:=", False, "RenormalizeAllTerminals:=", True,
        ["NAME:Modes", ["NAME:Mode1", "ModeNum:=", 1, "UseIntLine:=", True, bounds, "AlignmentGroup:=", 0,
         "CharImp:=", "Zpi", "RenormImp:=", "50ohm"]], "Impedance:=", "50ohm"])


def solve(case, desktop=None, ports=None, conductivity=None, extra_dielectrics=None):
    folder = os.path.join(root, case)
    desktop = desktop or oDesktop
    project = desktop.NewProject()
    project.InsertDesign("HFSS", case, "DrivenModal", "")
    d = project.SetActiveDesign(case)
    ed = d.SetActiveEditor("3D Modeler")
    ed.SetModelUnits(["NAME:Units Parameter","Units:=","mm","Rescale:=",False])
    project.GetDefinitionManager().AddMaterial(["NAME:PTFE_cabo", "CoordinateSystemType:=", "Cartesian",
        "BulkOrSurfaceType:=", 1, ["NAME:PhysicsTypes","set:=",["Electromagnetic"]],
        "permittivity:=", "2.036363533774732", "dielectric_loss_tangent:=", "0.00027683055"])
    metal = "copper"
    if conductivity is not None:
        metal = "Metal_cupom"
        project.GetDefinitionManager().AddMaterial(["NAME:" + metal, "CoordinateSystemType:=", "Cartesian",
            "BulkOrSurfaceType:=", 1, ["NAME:PhysicsTypes", "set:=", ["Electromagnetic"]],
            "conductivity:=", str(conductivity)])
    imports = [("copper",metal,False),("PTFE","PTFE_cabo",True)]
    for key, permittivity, tangent in (extra_dielectrics or []):
        project.GetDefinitionManager().AddMaterial(["NAME:" + key, "CoordinateSystemType:=", "Cartesian",
            "BulkOrSurfaceType:=", 1, ["NAME:PhysicsTypes", "set:=", ["Electromagnetic"]],
            "permittivity:=", str(permittivity), "dielectric_loss_tangent:=", str(tangent)])
        imports.append((key,key,True))
    for key, mat, solve_inside in imports:
        before = set(ed.GetObjectsInGroup("Solids"))
        ed.Import(["NAME:NativeBodyParameters","HealOption:=",0,"Options:=","-1","FileType:=","UnRecognized",
            "MaxStitchTol:=",-1,"ImportFreeSurfaces:=",True,"GroupByAssembly:=",False,"CreateGroup:=",False,
            "MergeFacesAngle:=",-1,"PointCoincidenceTol:=",1e-6,"CreateLightweightPart:=",False,
            "ImportMaterialNames:=",False,"SeparateDisjointLumps:=",True,"SourceFile:=",os.path.join(folder,key+".step"),
            "STLFileUnit:=","mm"])
        names = set(ed.GetObjectsInGroup("Solids")) - before
        assert names
        ed.AssignMaterial(["NAME:Selections","Selections:=",",".join(names)],
            ["NAME:Attributes","MaterialValue:=",'"'+mat+'"',"SolveInside:=",solve_inside])
    bd = d.GetModule("BoundarySetup")
    if ports is None:
        ports = [dict(name="Entrada", z=-15.52), dict(name="Saida", z=-3.52)]
    for port in ports:
        make_port(ed, bd, **port)
    d.GetModule("ModelSetup").CreateOpenRegion(["NAME:Settings","OpFreq:=","5.09GHz","Boundary:=","Radiation","ApplyInfiniteGP:=",False])
    an = d.GetModule("AnalysisSetup")
    an.InsertSetup("HfssDriven",["NAME:Cupom","SolveType:=","Single","Frequency:=","5.17GHz","MaxDeltaS:=",.008,
        "MaximumPasses:=",14,"MinimumPasses:=",3,"MinimumConvergedPasses:=",2,"PercentRefinement:=",24,"BasisOrder:=",-1])
    an.InsertFrequencySweep("Cupom",["NAME:Banda","IsEnabled:=",True,"Type:=","Discrete","RangeType:=","LinearStep",
        "RangeStart:=","5090MHz","RangeEnd:=","5250MHz","RangeStep:=","10MHz","SaveFields:=",False,"SaveRadFields:=",False])
    assert d.ValidateDesign()==1
    project.SaveAs(os.path.join(folder,case+".aedt"),True)
    log("SOLVER " + case)
    d.Analyze("Cupom")
    d.ExportConvergence("Cupom","",os.path.join(folder,"convergencia.txt"))
    assert "Converged : Yes" in open(os.path.join(folder,"convergencia.txt")).read()
    d.GetModule("Solutions").ExportNetworkData("",["Cupom : Banda"],3,os.path.join(folder,"cupom.s2p"),
        ["All"],True,50,"S",-1,1,15,False,True,False)
    project.Save()
    desktop.CloseProject(project.GetName())
    log("OK " + case)


if __name__ == "__main__":
    for case in ["Controle", "Com_bobina"]:
        try:
            solve(case)
        except:
            log(traceback.format_exc())
