# -*- coding: utf-8 -*-
"""Modelo HFSS dos dois divisores alongados, com condições de fase iguais em A e B."""
import os,json,re,traceback,ScriptEnv
ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
root=os.environ["P1H_R03"]
def u(x):return "%.10gmm"%x

def model(mat):
    path=os.path.join(root,mat,"rede_hfss")
    native="R03_Alongada_"+mat.replace("-","_")
    file=os.path.join(path,native+".aedt")
    def log(msg):
        with open(os.path.join(path,"calculo.log"),"a") as stream:stream.write(str(msg)+"\n")
    solve=os.environ.get("P1H_CALCULAR_REDE")=="1"
    try:
        if os.path.isfile(file):
            p=oDesktop.OpenProject(file);d=p.SetActiveDesign("Rede_par")
            an=d.GetModule("AnalysisSetup")
        else:
            p=oDesktop.NewProject();p.InsertDesign("HFSS","Rede_par","DrivenModal","")
            d=p.SetActiveDesign("Rede_par");ed=d.SetActiveEditor("3D Modeler");bd=d.GetModule("BoundarySetup");an=d.GetModule("AnalysisSetup")
            dm=p.GetDefinitionManager()
            ed.SetModelUnits(["NAME:Units Parameter","Units:=","mm","Rescale:=",False])
            g=json.load(open(os.path.join(root,mat,"Inferior","geometria.json")))
            for name,prop in [("LAM",[g["dk"],g["df"]]),("cabo",[2.036,.000277])]:
                dm.AddMaterial(["NAME:"+name,"CoordinateSystemType:=","Cartesian","BulkOrSurfaceType:=",1,["NAME:PhysicsTypes","set:=",["Electromagnetic"]],"permittivity:=",str(prop[0]),"dielectric_loss_tangent:=",str(prop[1])])
            dm.AddMaterial(["NAME:SAC305","CoordinateSystemType:=","Cartesian","BulkOrSurfaceType:=",1,["NAME:PhysicsTypes","set:=",["Electromagnetic"]],"conductivity:=","7575758"])
            for key in ["LAM","cabo","copper","SAC305","folha"]:
                category="Sheets" if key=="folha" else "Solids"
                old=set(ed.GetObjectsInGroup(category))
                ed.Import(["NAME:NativeBodyParameters","HealOption:=",0,"Options:=","-1","FileType:=","UnRecognized","MaxStitchTol:=",-1,
                           "ImportFreeSurfaces:=",True,"GroupByAssembly:=",False,"CreateGroup:=",False,"MergeFacesAngle:=",-1,
                           "PointCoincidenceTol:=",1e-6,"CreateLightweightPart:=",False,"ImportMaterialNames:=",False,"SeparateDisjointLumps:=",True,
                           "SourceFile:=",os.path.join(path,key+".step"),"STLFileUnit:=","mm"])
                names=list(set(ed.GetObjectsInGroup(category))-old)
                assert names,key
                if key=="folha":
                    bd.AssignFiniteCond(["NAME:Cu_35um","Objects:=",names,"UseMaterial:=",True,"Material:=","copper","UseThickness:=",True,
                        "Thickness:=","0.035mm","Roughness:=","0.5um","InfGroundPlane:=",False,"IsTwoSided:=",False])
                else:
                    ed.AssignMaterial(["NAME:Selections","Selections:=",",".join(names)],["NAME:Attributes","MaterialValue:=",'"'+key+'"',"SolveInside:=",key in ("LAM","cabo")])
            def attr(n):return ["NAME:Attributes","Name:=",n,"MaterialValue:=",'"vacuum"',"SolveInside:=",True]
            for key,x,y in json.load(open(os.path.join(path,"portas.json"))):
                name="Porta_"+key;blank="Centro_"+key
                for tag,r in [(name,1.515),(blank,.45975)]:
                    ed.CreateCircle(["NAME:CircleParameters","IsCovered:=",True,"XCenter:=",u(x),"YCenter:=",u(y),"ZCenter:=","-1.5mm","Radius:=",u(r),
                        "WhichAxis:=","Z","NumSegments:=","0"],attr(tag))
                ed.Subtract(["NAME:Selections","Blank Parts:=",name,"Tool Parts:=",blank],["NAME:SubtractParameters","KeepOriginals:=",False])
                bd.AssignLumpedPort(["NAME:"+key,"Objects:=",[name],"DoDeembed:=",False,"RenormalizeAllTerminals:=",True,
                    ["NAME:Modes",["NAME:Mode1","ModeNum:=",1,"UseIntLine:=",True,["NAME:IntLine","Start:=",[u(x+.45975),u(y),"-1.5mm"],"End:=",[u(x+1.515),u(y),"-1.5mm"]],"AlignmentGroup:=",0,"CharImp:=","Zpi","RenormImp:=","50ohm"]],
                    "ShowReporterFilter:=",False,"ReporterFilter:=",[True],"Impedance:=","50ohm"])
            padding=["NAME:RegionParameters"]
            for axis in ["+X","-X","+Y","-Y","+Z","-Z"]:
                padding.extend([axis+"PaddingType:=","Absolute Offset",axis+"Padding:=","0mm" if axis=="-Y" else "18mm"])
            ed.CreateRegion(padding,["NAME:Attributes","Name:=","Region","Flags:=","Wireframe#","MaterialValue:=",'"vacuum"',"SolveInside:=",True])
            other=[];plane=[]
            for face in list(ed.GetFaceIDs("Region")):
                center=ed.GetFaceCenter(int(face))
                if abs(float(center[1]))<.0001:plane.append(int(face))
                else:other.append(int(face))
            assert len(plane)==1 and len(other)==5,(plane,other)
            bd.AssignRadiation(["NAME:Radiacao","Faces:=",other,"IsFssReference:=",False,"IsForPML:=",False])
            bd.AssignSymmetry(["NAME:Simetria_magnetica","Faces:=",plane,"IsPerfectE:=",False])
            an.InsertSetup("HfssDriven",["NAME:Rede","Frequency:=","5.17GHz","MaxDeltaS:=",.009,"MaximumPasses:=",16,"MinimumPasses:=",3,"MinimumConvergedPasses:=",2,"PercentRefinement:=",22,"BasisOrder:=",1,"SaveAnyFields:=",True])
            p.SaveAs(file,True)
        assert d.ValidateDesign()==1,list(oDesktop.GetMessages(p.GetName(),d.GetName(),2))
        assert len(d.GetModule("Solutions").GetAllSources())==11
        log("REDE_VALIDA")
        if solve:
            if os.path.isfile(os.path.join(path,"placa.s11p")) and "REDE_OK" in open(os.path.join(path,"calculo.log")).read():
                oDesktop.CloseProject(p.GetName());return
            an.EditSetup("Rede",["NAME:Rede","Frequency:=","5.17GHz","MaxDeltaS:=",.009,"MaximumPasses:=",22,
                "MinimumPasses:=",3,"MinimumConvergedPasses:=",2,"PercentRefinement:=",22,"BasisOrder:=",1,
                "DrivenSolverType:=","Iterative Solver","IterativeResidual:=",.00001,"SaveAnyFields:=",True])
            p.Save()
            log("ADAPTATIVO");d.Analyze("Rede");d.ExportConvergence("Rede","",os.path.join(path,"convergencia.txt"))
            conv=open(os.path.join(path,"convergencia.txt")).read()
            assert "Converged : Yes" in conv and int(re.search(r"Current Consecutive Passes\s*:\s*(\d+)",conv).group(1))>=2
            s=d.GetModule("Solutions")
            s.ExportNetworkData("",["Rede : LastAdaptive"],3,os.path.join(path,"centro.s11p"),["All"],True,50,"S",-1,1,15,False,True,False)
            log("CENTRO_OK")
            if "Banda" not in an.GetSweeps("Rede"):
                an.InsertFrequencySweep("Rede",["NAME:Banda","IsEnabled:=",True,"RangeType:=","LinearStep","RangeStart:=","5090MHz",
                    "RangeEnd:=","5250MHz","RangeStep:=","10MHz","Type:=","Discrete","SaveFields:=",False,"SaveRadFields:=",False])
            p.Save();d.Analyze("Rede")
            s.ExportNetworkData("",["Rede : Banda"],3,os.path.join(path,"placa.s11p"),["All"],True,50,"S",-1,1,15,False,True,False)
            assert os.path.getsize(os.path.join(path,"placa.s11p"))>8000
            p.Save();log("REDE_OK")
        oDesktop.CloseProject(p.GetName())
    except:log(traceback.format_exc())

for mat in os.environ.get("P1H_MATERIAIS","ZYF300CA-C,ZYF255DA").split(","):model(mat)
