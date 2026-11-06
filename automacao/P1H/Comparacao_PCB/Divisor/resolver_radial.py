# -*- coding: utf-8 -*-
import ScriptEnv,os,traceback
ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
root=os.path.dirname(os.path.abspath(__file__))
def log(s):
    with open(os.path.join(root,"solucao_placa.log"),"a") as out: out.write(str(s)+"\n")
try:
    p=oDesktop.OpenProject(os.path.join(root,"Divisor_2x10_PTFE.aedt"))
    d=p.SetActiveDesign("Duplo_radial")
    an=d.GetModule("AnalysisSetup")
    if "Banda" not in list(an.GetSweeps("Divisor")):
        an.InsertFrequencySweep("Divisor",["NAME:Banda","IsEnabled:=",True,"RangeType:=","LinearStep","RangeStart:=","5090MHz","RangeEnd:=","5250MHz","RangeStep:=","10MHz","Type:=","Discrete","SaveFields:=",False,"SaveRadFields:=",False])
    assert d.ValidateDesign()==1
    p.Save()
    log("Inicio: layout duplo com 22 portas")
    d.Analyze("Divisor")
    log(list(oDesktop.GetMessages(p.GetName(),d.GetName(),1)))
    d.ExportConvergence("Divisor","",os.path.join(root,"convergencia_placa.txt"))
    sol=d.GetModule("Solutions")
    sol.ExportNetworkData("",["Divisor : Banda"],3,os.path.join(root,"distribuidor_EM.s22p"),["All"],True,50,"S",-1,1,15,False,True,False)
    p.Save()
    log("PCB_FEM_COMPLETO")
except:
    log(traceback.format_exc())



