# -*- coding: utf-8 -*-
"""Junta proposta entre UT-141C e a sonda coaxial existente do elemento."""
import os,traceback
import ScriptEnv
ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
root=os.path.dirname(os.path.abspath(__file__))
def log(msg):
    with open(os.path.join(root,"solucao.log"),"a") as f:f.write(str(msg)+"\n")
def u(x):return "%.9fmm"%x
def attr(name,mat,inside):
    return ["NAME:Attributes","Name:=",name,"MaterialValue:=",'"'+mat+'"',"SolveInside:=",inside]
def cyl(name,z,h,r,m,inside=False):
    ed.CreateCylinder(["NAME:CylinderParameters","XCenter:=","0mm","YCenter:=","0mm","ZCenter:=",u(z),"Radius:=",u(r),"Height:=",u(h),"WhichAxis:=","Z","NumSides:=","32"],attr(name,m,inside))
def circle(n,z,r):
    ed.CreateCircle(["NAME:CircleParameters","IsCovered:=",True,"XCenter:=","0mm","YCenter:=","0mm","ZCenter:=",u(z),"Radius:=",u(r),"WhichAxis:=","Z","NumSegments:=","32"],attr(n,"vacuum",True))
def subtract(n,tool,keep):
    ed.Subtract(["NAME:Selections","Blank Parts:=",n,"Tool Parts:=",tool],["NAME:SubtractParameters","KeepOriginals:=",keep])
def port(n,z,a,b):
    face="Face_"+n
    circle(face,z,b);circle("hole_"+n,z,a);subtract(face,"hole_"+n,False)
    bd.AssignLumpedPort(["NAME:"+n,"Objects:=",[face],"DoDeembed:=",False,"RenormalizeAllTerminals:=",True,
          ["NAME:Modes",["NAME:Mode1","ModeNum:=",1,"UseIntLine:=",True,["NAME:IntLine","Start:=",[u(a),"0mm",u(z)],"End:=",[u(b),"0mm",u(z)]],"AlignmentGroup:=",0,"CharImp:=","Zpi","RenormImp:=","50ohm"]],
          "ShowReporterFilter:=",False,"ReporterFilter:=",[True],"Impedance:=","50ohm"])
try:
    p=oDesktop.NewProject();p.InsertDesign("HFSS","Junta_coaxial","DrivenModal","")
    d=p.SetActiveDesign("Junta_coaxial");ed=d.SetActiveEditor("3D Modeler");bd=d.GetModule("BoundarySetup")
    dm=p.GetDefinitionManager()
    dm.AddMaterial(["NAME:SAC305","CoordinateSystemType:=","Cartesian","BulkOrSurfaceType:=",1,["NAME:PhysicsTypes","set:=",["Electromagnetic"]],"conductivity:=","7575758"])
    dm.AddMaterial(["NAME:PTFE_UT141","CoordinateSystemType:=","Cartesian","BulkOrSurfaceType:=",1,["NAME:PhysicsTypes","set:=",["Electromagnetic"]],"permittivity:=","2.036","dielectric_loss_tangent:=","0.0002"])
    cyl("Capa_UT",-1.5,1.5,1.7905,"copper");cyl("PTFE",-1.5,1.5,1.515,"PTFE_UT141",True);subtract("Capa_UT","PTFE",True)
    cyl("Centro_UT",-1.5,1.5,.45975,"copper");subtract("PTFE","Centro_UT",True)
    cyl("Adaptador_externo",0,.25,1.7905,"SAC305");cyl("vazio",0,.25,.834856,"vacuum",True);subtract("Adaptador_externo","vazio",False)
    cyl("Junta_central",0,.25,.362981,"SAC305")
    # Short retained air-coax section, additional to the original antenna reference.
    cyl("Blindagem_ponta",.25,.75,1.2704335,"aluminum");cyl("vazio_ponta",.25,.75,.834856,"vacuum",True);subtract("Blindagem_ponta","vazio_ponta",False)
    cyl("Pino_ponta",.25,.75,.362981,"copper")
    port("CABO",-1.5,.45975,1.515);port("P1H",1.,.362981,.834856)
    d.GetModule("ModelSetup").CreateOpenRegion(["NAME:Settings","OpFreq:=","5.17GHz","Boundary:=","Radiation","ApplyInfiniteGP:=",False])
    an=d.GetModule("AnalysisSetup")
    an.InsertSetup("HfssDriven",["NAME:Junta","Frequency:=","5.17GHz","MaxDeltaS:=",0.008,"MaximumPasses:=",12,"MinimumPasses:=",2,"MinimumConvergedPasses:=",1,"PercentRefinement:=",30,"BasisOrder:=",1])
    an.InsertFrequencySweep("Junta",["NAME:Banda","IsEnabled:=",True,"RangeType:=","LinearStep","RangeStart:=","5090MHz","RangeEnd:=","5250MHz","RangeStep:=","10MHz","Type:=","Discrete","SaveFields:=",False,"SaveRadFields:=",False])
    p.SaveAs(os.path.join(root,"Junta_UT141_P1H.aedt"),True)
    assert d.ValidateDesign()==1
    log("Inicio")
    d.Analyze("Junta")
    d.ExportConvergence("Junta","",os.path.join(root,"convergencia.txt"))
    d.GetModule("Solutions").ExportNetworkData("",["Junta : Banda"],3,os.path.join(root,"junta.s2p"),["All"],True,50,"S",-1,1,15,False,True,False)
    p.Save()
    log("FIM")
except:
    log(traceback.format_exc())

