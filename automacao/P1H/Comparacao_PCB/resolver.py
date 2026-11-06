# -*- coding: utf-8 -*-
"""Solve the imported KiCad panel and export the physical 20-port data and radiated fields."""
import os,traceback
import ScriptEnv
ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
root=os.path.dirname(os.path.abspath(__file__))
case=os.environ["P1H_PCB"];folder=os.path.join(root,case)
def log(s):
    with open(os.path.join(folder,"solucao.log"),"a") as f:f.write(str(s)+"\n")
try:
    assert open(os.path.join(folder,"modelo.log")).read().strip().endswith("MODELO_OK")
    p=oDesktop.OpenProject(os.path.join(folder,"P1H_"+case+".aedt"));d=p.SetActiveDesign("Synth_DipoleArray")
    s=d.GetModule("Solutions");an=d.GetModule("AnalysisSetup");r=d.GetModule("ReportSetup")
    setup="Setup_Multiband"
    def cuts(solution,tag,f):
        for axis,phi in [("H",90),("V",0)]:
            name="%s_%s_%d"%(tag,axis,f)
            r.CreateReport(name,"Far Fields","Rectangular Plot",setup+" : "+solution,["Context:=","AB_Eixos"],
                ["Theta:=",["All"],"Phi:=",[str(phi)+"deg"],"Freq:=",[str(f)+"MHz"]],["X Component:=","Theta","Y Component:=",["dB(RealizedGainTotal)"]])
            file=os.path.join(folder,name+".csv");r.ExportToFile(name,file,False);assert os.path.getsize(file)>20000
            r.DeleteReports([name])
    def export(sw,file):
        s.ExportNetworkData("",[setup+" : "+sw],3,os.path.join(folder,file),["All"],True,50,"S",-1,1,15,False,True,False)
    assert len(s.GetAllSources())==20
    log("ADAPTATIVO_INICIADO");d.Analyze(setup)
    d.ExportConvergence(setup,"",os.path.join(folder,"convergencia.txt"))
    assert "Converged : Yes" in open(os.path.join(folder,"convergencia.txt")).read()
    cuts("LastAdaptive","Centro",5170);export("LastAdaptive","centro.s20p");p.Save()
    log("CENTRO_CONVERGIDO")
    sw="Banda_10MHz"
    an.InsertFrequencySweep(setup,["NAME:"+sw,"IsEnabled:=",True,"RangeType:=","LinearStep","RangeStart:=","5090MHz","RangeEnd:=","5250MHz","RangeStep:=","10MHz","Type:=","Discrete","SaveFields:=",True,"SaveRadFields:=",True])
    p.Save();d.Analyze(setup);log(list(oDesktop.GetMessages(p.GetName(),d.GetName(),1)))
    export(sw,"painel.s20p")
    for f in range(5090,5251,10):cuts(sw,"Direto",f)
    p.Save();log("FEM_OK")
except:log(traceback.format_exc())
