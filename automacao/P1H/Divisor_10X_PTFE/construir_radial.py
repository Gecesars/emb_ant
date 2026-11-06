# -*- coding: utf-8 -*-
"""Build the finite dual-polarization distribution board in HFSS 2024 R2."""
import os,json,traceback
import ScriptEnv
ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
root=os.environ.get("P1H_RADIAL_DIR",os.path.dirname(os.path.abspath(__file__)))
g=json.load(open(os.path.join(root,"geometria.json")))
h=g["h"];hy=g["half_y"];hx=g["half_x"]
def log(value):
    with open(os.path.join(root,"hfss_placa.log"),"a") as out: out.write(str(value)+"\n")
def u(value):return "%.8fmm"%value
def attrs(name,material="vacuum",inside=True):
    return ["NAME:Attributes","Name:=",name,"Flags:=","","Color:=","(200 151 80)" if material=="vacuum" else "(96 120 145)",
            "Transparency:=",0.45 if material.startswith("ZY") else 0,"PartCoordinateSystem:=","Global","MaterialValue:=",'"'+material+'"',"SolveInside:=",inside]
def sheet(name,pts):
    pts=list(pts)+[pts[0]]
    points=["NAME:PolylinePoints"]+[["NAME:PLPoint","X:=",u(x),"Y:=",u(y),"Z:=",u(z)] for x,y,z in pts]
    seg=["NAME:PolylineSegments"]+[["NAME:PLSegment","SegmentType:=","Line","StartIndex:=",i,"NoOfPoints:=",2] for i in range(len(pts)-1)]
    ed.CreatePolyline(["NAME:PolylineParameters","IsPolylineCovered:=",True,"IsPolylineClosed:=",True,points,seg,
                       ["NAME:PolylineXSection","XSectionType:=","None","XSectionOrient:=","Auto","XSectionWidth:=","0mm","XSectionTopWidth:=","0mm","XSectionHeight:=","0mm","XSectionNumSegments:=","0","XSectionBendType:=","Corner"]],attrs(name))
def rect(name,x1,y1,x2,y2,z):
    sheet(name,[(x1,y1,z),(x2,y1,z),(x2,y2,z),(x1,y2,z)])
def vec(x,y,z):return [u(x),u(y),u(z)]
try:
    target=os.path.join(root,g.get("arquivo","Divisor_2x10_PTFE")+".aedt")
    if os.path.exists(target): raise RuntimeError("Projeto existente: abrir ou usar nova revisao")
    p=oDesktop.NewProject()
    p.InsertDesign("HFSS","Duplo_radial","DrivenModal","")
    d=p.SetActiveDesign("Duplo_radial")
    ed=d.SetActiveEditor("3D Modeler")
    b=d.GetModule("BoundarySetup")
    mat="ZYF300CA_C"
    p.GetDefinitionManager().AddMaterial(["NAME:"+mat,"CoordinateSystemType:=","Cartesian","BulkOrSurfaceType:=",1,
        ["NAME:PhysicsTypes","set:=",["Electromagnetic"]],"permittivity:=","2.94","dielectric_loss_tangent:=","0.0016","conductivity:=","0"])
    ed.CreateBox(["NAME:BoxParameters","XPosition:=",u(-hx),"YPosition:=",u(-hy),"ZPosition:=","0mm","XSize:=",u(2*hx),"YSize:=",u(2*hy),"ZSize:=",u(h)],attrs("Laminado",mat))
    rect("GND",-hx+.52,-hy+.52,hx-.52,hy-.52,0)
    copper=["GND"]
    for pol,pts in g["copper"].items():
        ed_name="Estrela_"+pol
        sheet(ed_name,[(x,y,h) for x,y in pts]);copper.append(ed_name)
    def circle(name,x,y,r,z=0):
        ed.CreateCircle(["NAME:CircleParameters","IsCovered:=",True,"XCenter:=",u(x),"YCenter:=",u(y),"ZCenter:=",u(z),"Radius:=",u(r),"WhichAxis:=","Z","NumSegments:=","24"],attrs(name))
    def sub(n,tools,keep=False):
        ed.Subtract(["NAME:Selections","Blank Parts:=",n,"Tool Parts:=",",".join(tools)],["NAME:SubtractParameters","KeepOriginals:=",keep])
    # Nominal coax-to-board soldered launch. The 1.5 mm coax segment is included in the RF model.
    dm=p.GetDefinitionManager()
    dm.AddMaterial(["NAME:SAC305","CoordinateSystemType:=","Cartesian","BulkOrSurfaceType:=",1,["NAME:PhysicsTypes","set:=",["Electromagnetic"]],"conductivity:=","7575758","permeability:=","1"])
    dm.AddMaterial(["NAME:PTFE_UT141","CoordinateSystemType:=","Cartesian","BulkOrSurfaceType:=",1,["NAME:PhysicsTypes","set:=",["Electromagnetic"]],"permittivity:=","2.036","dielectric_loss_tangent:=","0.0002"])
    def cyl(name,x,y,r,z,dz,material):
        ed.CreateCylinder(["NAME:CylinderParameters","XCenter:=",u(x),"YCenter:=",u(y),"ZCenter:=",u(z),"Radius:=",u(r),"Height:=",u(dz),"WhichAxis:=","Z","NumSides:=","24"],attrs(name,material,material=="PTFE_UT141"))
    disks=[];pins=[]
    for name,x,y in g["ports"]:
        disk="Abertura_"+name
        circle(disk,x,y,1.515);disks.append(disk)
        pin="Pino_"+name
        # The plated barrel, filled bore and conductor are represented by their continuous outer surface through the core.
        cyl(pin,x,y,.525,0,h,"copper")
        pins.append(pin)
        land="Anel_"+name
        circle(land,x,y,.73)
        copper.append(land)
        shell="Blindagem_"+name
        core="PTFE_"+name
        inner="Central_"+name
        cyl(shell,x,y,1.7905,-1.5,1.5,"copper")
        cyl(core,x,y,1.515,-1.5,1.5,"PTFE_UT141")
        sub(shell,[core],True)
        cyl(inner,x,y,.45975,-1.5,1.5,"copper")
        sub(core,[inner],True)
        fillet="Solda_ext_"+name
        tool="Recorte_ext_"+name
        cyl(fillet,x,y,2.13,-.18,.18,"SAC305")
        cyl(tool,x,y,1.7905,-.18,.18,"copper")
        sub(fillet,[tool])
        tip="Solda_top_"+name
        cyl(tip,x,y,.74,h,.17,"SAC305")
    sub("GND",disks,False);sub("Laminado",pins,True)
    if "janela" in g:
        sheet("Canal_mecanico",[(x,y,0) for x,y in g["janela"]])
        ed.SweepAlongVector(["NAME:Selections","Selections:=","Canal_mecanico","NewPartsModelFlag:=","Model"],
            ["NAME:VectorSweepParameters","DraftAngle:=","0deg","DraftType:=","Round","CheckFaceFaceIntersection:=",False,
             "SweepVectorX:=","0mm","SweepVectorY:=","0mm","SweepVectorZ:=",u(h)])
        sub("Laminado",["Canal_mecanico"])
        sheet("Folga_massa",[(x,y,0) for x,y in g["janela_sem_cobre"]])
        sub("GND",["Folga_massa"])
    b.AssignFiniteCond(["NAME:Cobre_35um","Objects:=",copper,"UseMaterial:=",True,"Material:=","copper","UseThickness:=",True,"Thickness:=","0.035mm","Roughness:=","0.5um","InfGroundPlane:=",False,"IsTwoSided:=",False])
    for name,x,y in g["ports"]:
        s="Porta_"+name
        circle(s,x,y,1.515,-1.5)
        inner="Buraco_"+name
        circle(inner,x,y,.45975,-1.5)
        sub(s,[inner])
        b.AssignLumpedPort(["NAME:"+name,"Objects:=",[s],"DoDeembed:=",False,"RenormalizeAllTerminals:=",True,
            ["NAME:Modes",["NAME:Mode1","ModeNum:=",1,"UseIntLine:=",True,["NAME:IntLine","Start:=",vec(x+.45975,y,-1.5),"End:=",vec(x+1.515,y,-1.5)],"AlignmentGroup:=",0,"CharImp:=","Zpi","RenormImp:=","50ohm"]],
            "ShowReporterFilter:=",False,"ReporterFilter:=",[True],"Impedance:=","50ohm"])
    d.GetModule("ModelSetup").CreateOpenRegion(["NAME:Settings","OpFreq:=","5.09GHz","Boundary:=","Radiation","ApplyInfiniteGP:=",False])
    an=d.GetModule("AnalysisSetup")
    an.InsertSetup("HfssDriven",["NAME:Divisor","Frequency:=","5.17GHz","MaxDeltaS:=",0.015,"MaximumPasses:=",14,"MinimumPasses:=",2,"MinimumConvergedPasses:=",1,"PercentRefinement:=",28,"BasisOrder:=",1])
    assert len(d.GetModule("Solutions").GetAllSources())==len(g["ports"])
    p.SaveAs(target,True)
    valid=d.ValidateDesign()
    log(("valid",valid,list(oDesktop.GetMessages(p.GetName(),d.GetName(),1))))
    assert valid==1
    log("PCB_READY")
except:
    log(traceback.format_exc())

