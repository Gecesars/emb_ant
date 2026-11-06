# -*- coding: utf-8 -*-
"""Matriz completa do divisor de grupo ou do primeiro estágio, com todas as outras portas casadas."""
import os,json,traceback,ScriptEnv
ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
root=os.environ["P1H_RADIAL_DIR"]
g=json.load(open(os.path.join(root,"geometria.json")))
def log(x):
    with open(os.path.join(root,"solver.log"),"a") as f:f.write(str(x)+"\n")
try:
    p=oDesktop.OpenProject(os.path.join(root,g["arquivo"]+".aedt"))
    d=p.SetActiveDesign("Duplo_radial");an=d.GetModule("AnalysisSetup")
    assert d.ValidateDesign()==1
    an.EditSetup("Divisor",["NAME:Divisor","Frequency:=","5.17GHz","MaxDeltaS:=",.012,
        "MaximumPasses:=",16,"MinimumPasses:=",3,"MinimumConvergedPasses:=",2,"PercentRefinement:=",24,"BasisOrder:=",1])
    if "Banda" not in an.GetSweeps("Divisor"):
        an.InsertFrequencySweep("Divisor",["NAME:Banda","IsEnabled:=",True,"RangeType:=","LinearStep","RangeStart:=","5090MHz",
            "RangeEnd:=","5250MHz","RangeStep:=","10MHz","Type:=","Discrete","SaveFields:=",False,"SaveRadFields:=",False])
    p.Save();log("ADAPTATIVO")
    d.Analyze("Divisor")
    d.ExportConvergence("Divisor","",os.path.join(root,"convergencia.txt"))
    assert "Converged : Yes" in open(os.path.join(root,"convergencia.txt")).read()
    n=len(g["ports"])
    d.GetModule("Solutions").ExportNetworkData("",["Divisor : Banda"],3,os.path.join(root,"divisor.s%dp"%n),
        ["All"],True,50,"S",-1,1,15,False,True,False)
    p.Save();log("FEM_OK")
except:log(traceback.format_exc())
