# -*- coding: utf-8 -*-
"""Linhas microstrip de 20 e 120 mm para extração de perda por matriz de transferência."""
import json,os,re,traceback,ScriptEnv
ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
root=os.environ["P1H_R03"]
def mm(x):return "%.9gmm"%x
def run(mat,length):
    base=os.path.join(root,mat)
    dest=os.path.join(base,"cupom_%d"%length)
    if not os.path.isdir(dest):os.makedirs(dest)
    def log(x):
        with open(os.path.join(dest,"ensaio.log"),"a") as stream:stream.write(str(x)+"\n")
    convpath=os.path.join(dest,"convergencia.txt")
    def convergiu():
        if not os.path.exists(convpath):return False
        txt=open(convpath).read()
        n=re.search(r"Current Consecutive Passes\s*:\s*(\d+)",txt)
        return "Converged : Yes" in txt and n and int(n.group(1))>=2
    if os.path.isfile(os.path.join(dest,"linha.s2p")) and convergiu():return
    g=json.load(open(os.path.join(base,"Superior","geometria.json")))
    width=json.load(open(os.path.join(base,"linhas.json")))["larguras"]["50.0"]["largura_mm"]
    h=g["h"];half=15.0
    name="Linha_"+mat.replace("-","_")+"_"+str(length)
    setup=["NAME:Perda","Frequency:=","5.17GHz","MaxDeltaS:=",.003,"MaximumPasses:=",25,
        "MinimumPasses:=",4,"MinimumConvergedPasses:=",2,"PercentRefinement:=",26,"BasisOrder:=",1,"SaveAnyFields:=",True]
    def finish(project,d):
        try:
            assert d.ValidateDesign()==1
            log("VALIDO");d.Analyze("Perda");d.ExportConvergence("Perda","",convpath)
            assert convergiu(),"Exigidos dois passes consecutivos."
            destfile=os.path.join(dest,"linha.s2p")
            d.GetModule("Solutions").ExportNetworkData("",["Perda : Banda"],3,destfile,["All"],True,50,"S",-1,1,15,False,True,False)
            assert os.path.getsize(destfile)>2000
            project.Save();log("CUPOM_OK")
        except:log(traceback.format_exc());log(list(oDesktop.GetMessages(project.GetName(),d.GetName(),2)))
        oDesktop.CloseProject(project.GetName())
    native=os.path.join(dest,name+".aedt")
    if os.path.isfile(native):
        project=oDesktop.OpenProject(native);d=project.SetActiveDesign("Linha")
        d.GetModule("AnalysisSetup").EditSetup("Perda",setup)
        project.Save();finish(project,d);return
    project=oDesktop.NewProject();project.InsertDesign("HFSS","Linha","DrivenModal","")
    d=project.SetActiveDesign("Linha");ed=d.SetActiveEditor("3D Modeler")
    bc=d.GetModule("BoundarySetup");an=d.GetModule("AnalysisSetup")
    def atr(n,material):
        return ["NAME:Attributes","Name:=",n,"MaterialValue:=",'"'+material+'"',"SolveInside:=",True]
    ed.SetModelUnits(["NAME:Units Parameter","Units:=","mm","Rescale:=",False])
    material=mat.replace("-","_")
    project.GetDefinitionManager().AddMaterial(["NAME:"+material,"CoordinateSystemType:=","Cartesian","BulkOrSurfaceType:=",1,["NAME:PhysicsTypes","set:=",["Electromagnetic"]],"permittivity:=",str(g["dk"]),"dielectric_loss_tangent:=",str(g["df"])])
    ed.CreateBox(["NAME:BoxParameters","XPosition:=","0mm","YPosition:=",mm(-half),"ZPosition:=","0mm","XSize:=",mm(length),"YSize:=",mm(2*half),"ZSize:=",mm(h)],atr("Laminado",material))
    def rect(n,axis,x,y,z,w,hh):
        ed.CreateRectangle(["NAME:RectangleParameters","IsCovered:=",True,"XStart:=",mm(x),"YStart:=",mm(y),"ZStart:=",mm(z),
             "Width:=",mm(w),"Height:=",mm(hh),"WhichAxis:=",axis],atr(n,"vacuum"))
    rect("GND","Z",0,-half,0,length,2*half);rect("Trilha","Z",0,-width/2,h,length,width)
    bc.AssignFiniteCond(["NAME:Cobre","Objects:=",["Trilha","GND"],"UseMaterial:=",True,"Material:=","copper",
        "UseThickness:=",True,"Thickness:=","0.035mm","Roughness:=","0.5um","InfGroundPlane:=",False,"IsTwoSided:=",False])
    for tag,x in [("E",0),("S",length)]:
        n="Secao_"+tag;rect(n,"X",x,-width/2,0,width,h)
        bc.AssignLumpedPort(["NAME:"+tag,"Objects:=",[n],"DoDeembed:=",False,"RenormalizeAllTerminals:=",True,
            ["NAME:Modes",["NAME:Mode1","ModeNum:=",1,"UseIntLine:=",True,["NAME:IntLine","Start:=",[mm(x),"0mm",mm(h)],"End:=",[mm(x),"0mm","0mm"]],"AlignmentGroup:=",0,"CharImp:=","Zpi","RenormImp:=","50ohm"]],
            "ShowReporterFilter:=",False,"ReporterFilter:=",[True],"Impedance:=","50ohm"])
    d.GetModule("ModelSetup").CreateOpenRegion(["NAME:Settings","OpFreq:=","5.09GHz","Boundary:=","Radiation","ApplyInfiniteGP:=",False])
    an.InsertSetup("HfssDriven",setup)
    an.InsertFrequencySweep("Perda",["NAME:Banda","IsEnabled:=",True,"RangeType:=","LinearStep","RangeStart:=","5090MHz",
        "RangeEnd:=","5250MHz","RangeStep:=","10MHz","Type:=","Discrete","SaveFields:=",False,"SaveRadFields:=",False])
    project.SaveAs(native,True)
    finish(project,d)
for material in ["ZYF300CA-C","ZYF255DA","ZYF265D","ZYF300CA-P"]:
    for length in [20,120]:run(material,length)
