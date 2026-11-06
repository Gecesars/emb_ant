# -*- coding: utf-8 -*-
"""Build the two KiCad panel revisions from the native dual-polarized HFSS element."""
import os, traceback
import ScriptEnv
ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
base=os.path.dirname(os.path.abspath(__file__))
case=os.environ["P1H_PCB"]
folder=os.path.join(base,case)
prefix="E001_P1H_"
mat="P1H_RO4350B_DesignDk"
z=16.61
h=.76
pitch=52.6
a=14.15625

def log(s):
    with open(os.path.join(folder,"modelo.log"),"a") as f:f.write(str(s)+"\n")
def u(v):return "%.12gmm"%v
def attrs(n,m):
    return ["NAME:Attributes","Name:=",n,"Flags:=","","PartCoordinateSystem:=","Global","MaterialValue:=",'"'+m+'"',"SolveInside:=",m not in ("copper","pec"),"Color:=","(110 152 170)"]
def box(n,x,y,zb,w,l,t,m):
    ed.CreateBox(["NAME:BoxParameters","XPosition:=",u(x),"YPosition:=",u(y),"ZPosition:=",u(zb),"XSize:=",u(w),"YSize:=",u(l),"ZSize:=",u(t)],attrs(n,m))
def cyl(n,x,y,zb,r,t,m):
    ed.CreateCylinder(["NAME:CylinderParameters","XCenter:=",u(x),"YCenter:=",u(y),"ZCenter:=",u(zb),"Radius:=",u(r),"Height:=",u(t),"WhichAxis:=","Z","NumSides:=","0"],attrs(n,m))
def disk(n,x,y,zb,r):
    ed.CreateCircle(["NAME:CircleParameters","IsCovered:=",True,"XCenter:=",u(x),"YCenter:=",u(y),"ZCenter:=",u(zb),"Radius:=",u(r),"WhichAxis:=","Z","NumSegments:=","0"],attrs(n,"vacuum"))
def sub(n,tools):
    ed.Subtract(["NAME:Selections","Blank Parts:=",n,"Tool Parts:=",",".join(tools)],["NAME:SubtractParameters","KeepOriginals:=",False])
def unite(names):
    ed.Unite(["NAME:Selections","Selections:=",",".join(names)],["NAME:UniteParameters","KeepOriginals:=",False])
def positions(n):
    return [list(map(float,ed.GetVertexPosition(v))) for v in ed.GetVertexIDsFromObject(n)]
def extent(n):
    pts=positions(n)
    return [(min(p[j] for p in pts),max(p[j] for p in pts)) for j in range(3)]
try:
    assert case in ("Continua","Separadas")
    pr=oDesktop.OpenProject(os.path.join(folder,"P1H_"+case+".aedt"))
    des=pr.SetActiveDesign("Synth_DipoleArray");ed=des.SetActiveEditor("3D Modeler")
    sol=des.GetModule("Solutions");ana=des.GetModule("AnalysisSetup");bounds=des.GetModule("BoundarySetup")
    reports=des.GetModule("ReportSetup");rr=list(reports.GetAllReportNames())
    if rr:reports.DeleteReports(rr)
    for sw in list(ana.GetSweeps("Setup_Multiband")):ana.DeleteSweep("Setup_Multiband",sw)
    des.GetModule("RadField").EditAntennaArraySetup(["NAME:ArraySetupInfo","UseOption:=","NoArray"])
    bounds.DeleteBoundaries(["E001_P1H_Copper_Traces"])
    substrate=prefix+"Substrate"
    ed.Delete(["NAME:Selections","Selections:=",",".join([substrate,prefix+"Via_1",prefix+"Via_2"])])
    box(substrate,-a,-a,z,2*a,2*a,h,mat)
    metals=[prefix+n for n in ("Ring_Q1","Ring_Q2","Ring_Q3","Ring_Q4","Feed_A","Feed_B_Inner","Feed_B_Outer","Crossover_Bridge")]
    holes=[]
    for label,x,y,r in [("A",2.50916841304063,-2.50916841304063,.45),("B",2.50916841304063,2.50916841304063,.45),
                         ("V1",-.747411867714055,-.747411867714055,.225),("V2",.747411867714055,.747411867714055,.225)]:
        tool="FuroCore_"+label;cyl(tool,x,y,z-.05,r,h+.10,"vacuum");holes.append(tool)
        isvia=label.startswith("V")
        bore=.20 if isvia else .362981
        barrel=prefix+"Metal_"+label
        cutter="FuroMetal_"+label
        cyl(barrel,x,y,z,r,h,"copper");cyl(cutter,x,y,z-.05,bore,h+.1,"vacuum");sub(barrel,[cutter])
        if not isvia:unite([prefix+"Pin_"+label,barrel])
        for side,zb in [("B",z),("F",z+h)]:
            pad=prefix+"Pad_"+label+"_"+side
            disk(pad,x,y,zb,.363 if isvia else .6)
            target=None
            if isvia:
                target="Crossover_Bridge" if side=="B" else ("Feed_B_Outer" if label=="V1" else "Feed_B_Inner")
            elif side=="F":target="Feed_A" if label=="A" else "Feed_B_Inner"
            if target:
                target=prefix+target; unite([target,pad])
            else:
                target=pad;metals.append(pad)
            cutter="FuroPad_"+label+"_"+side
            # The metal solid itself supplies the land between the bore and r on both faces.
            # Trim only the coincident sheet, so the generated mesh has one physical conductor surface.
            disk(cutter,x,y,zb,r);sub(target,[cutter])
    sub(substrate,holes)
    bounds.AssignFiniteCond(["NAME:Cobre_PCB_35um","Objects:=",metals,"UseMaterial:=",True,"Material:=","copper","UseThickness:=",True,"Thickness:=","0.035mm","Roughness:=","0um","InfGroundPlane:=",False,"IsTwoSided:=",False])
    objs=list(ed.GetObjectsInGroup("Solids"))+list(ed.GetObjectsInGroup("Sheets"))
    parts=[n for n in objs if n.startswith(prefix) or n=="Array_Refletor"]
    assert "Array_Refletor" in parts and len(sol.GetAllSources())==2
    group=["NAME:Selections","Selections:=",",".join(parts),"NewPartsModelFlag:=","Model"]
    ed.Move(group,["NAME:TranslateParameters","TranslateVectorX:=","-236.7mm","TranslateVectorY:=","0mm","TranslateVectorZ:=","0mm"])
    ed.DuplicateAlongLine(group,["NAME:DuplicateToAlongLineParameters","CreateNewObjects:=",True,"XComponent:=","52.6mm","YComponent:=","0mm","ZComponent:=","0mm","Numclones:=","10"],["NAME:Options","DuplicateAssignments:=",True])
    original=[n for n in ed.GetObjectsInGroup("Solids") if n.startswith(substrate)]
    assert len(original)==10
    if case=="Continua":
        bridges=[]
        for i in range(9):
            name="Laminado_entre_%02d"%i
            box(name,-236.7+i*pitch+a,-a,z,pitch-2*a,2*a,h,mat);bridges.append(name)
        unite([substrate]+[n for n in original if n!=substrate]+bridges)
    cores=[n for n in ed.GetObjectsInGroup("Solids") if n.startswith(substrate)]
    dims=[extent(n) for n in cores]
    assert len(cores)==(1 if case=="Continua" else 10)
    for xyz in dims:
        for ext,w in zip(xyz,[501.7125 if case=="Continua" else 28.3125,28.3125,h]):assert abs(ext[1]-ext[0]-w)<.0001
    names=list(sol.GetAllSources())
    assert len(names)==20 and len([n for n in ed.GetObjectsInGroup("Sheets") if n.startswith("Array_Refletor")])==10
    sol.EditSources([["IncludePortPostProcessing:=",False,"SpecifySystemPower:=",False]]+[["Name:=",n+":1","Magnitude:=","0.05W","Phase:=","0deg"] for n in names])
    ana.EditSetup("Setup_Multiband",["NAME:Setup_Multiband","SolveType:=","Single","Frequency:=","5.17GHz","MaxDeltaS:=",0.02,"MaximumPasses:=",11,"MinimumPasses:=",2,"MinimumConvergedPasses:=",1,"PercentRefinement:=",25,"BasisOrder:=",1,"SaveAnyFields:=",True,"SaveRadFieldsOnly:=",False])
    pr.Save()
    ok=des.ValidateDesign()
    log(("core",mat,dims,"ports",names,"validation",ok,list(oDesktop.GetMessages(pr.GetName(),des.GetName(),1))))
    assert ok==1
    log("MODELO_OK")
except:log(traceback.format_exc())
