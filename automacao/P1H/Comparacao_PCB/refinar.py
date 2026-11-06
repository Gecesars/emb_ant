# -*- coding: utf-8 -*-
import os,traceback
import ScriptEnv
ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
base=os.path.dirname(os.path.abspath(__file__));case=os.environ["P1H_PCB"];folder=os.path.join(base,case)
try:
    p=oDesktop.OpenProject(os.path.join(folder,"P1H_"+case+".aedt"))
    d=p.SetActiveDesign("Synth_DipoleArray");ed=d.SetActiveEditor("3D Modeler")
    objs=list(ed.GetObjectsInGroup("Sheets"))+list(ed.GetObjectsInGroup("Solids"))
    chosen=[n for n in objs if any(k in n for k in ("_Pad_","_Metal_","_Feed_","Crossover_Bridge","_Pin_"))]
    assert len(chosen)==100,len(chosen)
    d.GetModule("MeshSetup").AssignTrueSurfOp(["NAME:Contornos_das_sondas","Objects:=",chosen,"CurvedSurfaceApproxChoice:=","ManualSettings","SurfDevChoice:=",2,"SurfDev:=","0.002mm","NormalDevChoice:=",2,"NormalDev:=","10deg","AspectRatioChoice:=",1,"AspectRatio:=","10"])
    p.Save();assert d.ValidateDesign()==1
    with open(os.path.join(folder,"refino.log"),"w") as f:f.write("REFINO_OK %d\n"%len(chosen))
except:
    with open(os.path.join(folder,"refino.log"),"w") as f:f.write(traceback.format_exc())
