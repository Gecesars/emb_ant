# -*- coding: utf-8 -*-
"""Use the incident waves of the loaded 20-port panel in the solved HFSS fields."""
import os,json,csv,math,traceback
import ScriptEnv
ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
base=os.path.dirname(os.path.abspath(__file__));case=os.environ["P1H_PCB"]
folder=os.path.join(base,case);system=os.path.join(folder,"Sistema")
def log(s):
    with open(os.path.join(system,"campos.log"),"a") as f:f.write(str(s)+"\n")
try:
    p=oDesktop.OpenProject(os.path.join(folder,"P1H_"+case+".aedt"));d=p.SetActiveDesign("Synth_DipoleArray")
    sol=d.GetModule("Solutions");r=d.GetModule("ReportSetup")
    cases=json.load(open(os.path.join(system,"fontes_hfss.json")))
    assert len(cases)==17
    def sources(listing):
        sol.EditSources([["IncludePortPostProcessing:=",False,"SpecifySystemPower:=",False]]+[["Name:=",v["name"]+":1","Magnitude:=","%.15gW"%v["watts"],"Phase:=","%.12gdeg"%v["phase_deg"]] for v in listing])
    def report(name,phi,f):
        r.CreateReport(name,"Far Fields","Rectangular Plot","Setup_Multiband : Banda_10MHz",["Context:=","AB_Eixos"],["Theta:=",["All"],"Phi:=",[str(phi)+"deg"],"Freq:=",[str(f)+"MHz"]],["X Component:=","Theta","Y Component:=",["dB(RealizedGainTotal)"]])
    for entry in cases:
        f=entry["mhz"]; sources(entry["sources"]); correction=10*math.log10(entry["incident_w"])
        for axis,phi in [("H",90),("V",0)]:
            name="Rede_%s_%d"%(axis,f)
            report(name,phi,f);path=os.path.join(system,name+".csv");r.ExportToFile(name,path,False);r.DeleteReports([name])
            assert os.path.getsize(path)>20000
            if f==5170:
                with open(path,"rb") as inp,open(os.path.join(system,"Entrada_%s.csv"%axis),"wb") as dst:
                    rdr=csv.reader(inp);wr=csv.writer(dst);next(rdr)
                    wr.writerow(["Freq [GHz]","Phi [deg]","Theta [deg]","Ganho_nas_duas_entradas []"])
                    for row in rdr:wr.writerow(row[:3]+["%.12g"%(float(row[3])+correction)])
        log(f)
    sources([{"name":v["name"],"watts":.05,"phase_deg":0} for v in cases[0]["sources"]])
    for axis,phi in [("H",90),("V",0)]:
        name="Sistema_%s_5170MHz"%axis;report(name,phi,5170);r.ImportIntoReport(name,os.path.join(system,"Entrada_%s.csv"%axis))
        path=os.path.join(system,"HFSS_%s_5170.csv"%axis);r.ExportToFile(name,path,False)
        assert "Ganho_nas_duas_entradas" in open(path).readline()
    p.Save();log("CAMPOS_OK")
except:log(traceback.format_exc())
