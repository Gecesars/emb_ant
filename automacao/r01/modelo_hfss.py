# -*- coding: utf-8 -*-
"""Script interno AEDT 2024 R2. Criar o modelo integrado de duas portas em uma pasta nova."""
import ScriptEnv,os,json,traceback,math
ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
root=os.environ["P1H_R01"];cad=os.path.join(root,"cad");work=os.path.join(root,"estudo")
def log(s):
    with open(os.path.join(work,"modelo.log"),"a") as f:f.write(str(s)+"\n")
def u(x):return "%.12gmm"%x
def xyz(x,y,z):return [u(x),u(y),u(z)]
try:
    project=oDesktop.NewProject()
    project.InsertDesign("HFSS","Painel_montado","DrivenModal","")
    d=project.SetActiveDesign("Painel_montado");ed=d.SetActiveEditor("3D Modeler")
    bd=d.GetModule("BoundarySetup");dm=project.GetDefinitionManager()
    ed.SetModelUnits(["NAME:Units Parameter","Units:=","mm","Rescale:=",False])
    # Modelo nominal de PTFE. Ajuste da pequena perda dielétrica com base na atenuação de catálogo do UT-141C.
    f=5.17e9;mu=4*math.pi*1e-7;sigma=5.8e7;er=(299792458*50*95.2e-12)**2
    beta=2*math.pi*f*er**.5/299792458
    conductor=(math.pi*f*mu/sigma)**.5*(1/.00045975+1/.001515)/(4*math.pi*50)
    tand=2*((27.6+.17*2.8)/30.48/8.685889638-conductor)/beta
    log(("nominal UT141",er,tand))
    diel={"POM_nom":(3.4,.01),"Silicone_nom":(2.77,.02),"PE_nom":(2.3,.001),
          "PTFE_cabo":(er,tand),"RO4350B_R01":(3.66,.0037),"ZYF300":(2.94,.0016)}
    cond={"AL5052":2.0e7,"aco_nom":1.4e6,"latao_nom":1.6e7,"SAC305":7.575758e6}
    for key,(dk,lt) in diel.items():
        dm.AddMaterial(["NAME:"+key,"CoordinateSystemType:=","Cartesian","BulkOrSurfaceType:=",1,["NAME:PhysicsTypes","set:=",["Electromagnetic"]],"permittivity:=",str(dk),"dielectric_loss_tangent:=",str(lt)])
    for key,s in cond.items():
        dm.AddMaterial(["NAME:"+key,"CoordinateSystemType:=","Cartesian","BulkOrSurfaceType:=",1,["NAME:PhysicsTypes","set:=",["Electromagnetic"]],"conductivity:=",str(s)])
    def objs(k):return set(ed.GetObjectsInGroup(k))
    counts={}
    for mat in sorted(list(diel)+list(cond)+["copper","folha_cu"]):
        solids=objs("Solids");sheets=objs("Sheets")
        ed.Import(["NAME:NativeBodyParameters","HealOption:=",0,"Options:=","-1","FileType:=","UnRecognized","MaxStitchTol:=",-1,
                   "ImportFreeSurfaces:=",True,"GroupByAssembly:=",False,"CreateGroup:=",False,"MergeFacesAngle:=",-1,
                   "PointCoincidenceTol:=",1e-6,"CreateLightweightPart:=",False,"ImportMaterialNames:=",False,
                   "SeparateDisjointLumps:=",True,"SourceFile:=",os.path.join(cad,mat+".step"),"STLFileUnit:=","mm"])
        newsol=sorted(objs("Solids")-solids);newsh=sorted(objs("Sheets")-sheets)
        counts[mat]=(len(newsol),len(newsh));log((mat,counts[mat],(newsol+newsh)[:4]))
        if mat=="folha_cu":
            assert not newsol and len(newsh)>=10
            bd.AssignFiniteCond(["NAME:Metais_impressos_35um","Objects:=",newsh,"UseMaterial:=",True,"Material:=","copper","UseThickness:=",True,"Thickness:=","0.035mm","Roughness:=","0.5um","InfGroundPlane:=",False,"IsTwoSided:=",False])
        else:
            assert newsol and not newsh,(mat,newsol,newsh)
            ed.AssignMaterial(["NAME:Selections","Selections:=",",".join(newsol)],["NAME:Attributes","MaterialValue:=",'"'+mat+'"',"SolveInside:=",mat in diel])
    def circle(name,x,y,z,r):
        ed.CreateCircle(["NAME:CircleParameters","IsCovered:=",True,"XCenter:=",u(x),"YCenter:=",u(y),"ZCenter:=",u(z),"Radius:=",u(r),"WhichAxis:=","X","NumSegments:=","0"],["NAME:Attributes","Name:=",name,"MaterialValue:=",'"vacuum"',"SolveInside:=",True])
    for pol,sgn in [("A",-1),("B",1)]:
        y=sgn*19.25;x=-288.;z=-31.;port="Plano_N_"+pol
        plug="Miolo_"+pol
        circle(port,x,y,z,3.5);circle(plug,x,y,z,3.5/2.3)
        ed.Subtract(["NAME:Selections","Blank Parts:=",port,"Tool Parts:=",plug],["NAME:SubtractParameters","KeepOriginals:=",False])
        bd.AssignLumpedPort(["NAME:N_"+pol,"Objects:=",[port],"DoDeembed:=",False,"RenormalizeAllTerminals:=",True,["NAME:Modes",["NAME:Mode1","ModeNum:=",1,"UseIntLine:=",True,["NAME:IntLine","Start:=",xyz(x,y+3.5/2.3,z),"End:=",xyz(x,y+3.5,z)],"AlignmentGroup:=",0,"CharImp:=","Zpi","RenormImp:=","50ohm"]],"ShowReporterFilter:=",False,"ReporterFilter:=",[True],"Impedance:=","50ohm"])
    d.GetModule("ModelSetup").CreateOpenRegion(["NAME:Settings","OpFreq:=","5.09GHz","Boundary:=","Radiation","ApplyInfiniteGP:=",False])
    d.GetModule("RadField").InsertInfiniteSphereSetup(["NAME:HV","UseCustomRadiationSurface:=",False,"CSDefinition:=","Theta-Phi","Polarization:=","Linear","ThetaStart:=","-180deg","ThetaStop:=","180deg","ThetaStep:=","0.25deg","PhiStart:=","0deg","PhiStop:=","90deg","PhiStep:=","90deg","UseLocalCS:=",False])
    d.GetModule("AnalysisSetup").InsertSetup("HfssDriven",["NAME:Banda","SolveType:=","Single","Frequency:=","5.17GHz","MaxDeltaS:=",.015,"MaximumPasses:=",12,"MinimumPasses:=",3,"MinimumConvergedPasses:=",2,"PercentRefinement:=",23,"BasisOrder:=",-1,"SaveAnyFields:=",True,"SaveRadFieldsOnly:=",False])
    if os.environ.get("P1H_ITERATIVO") == "1":
        d.GetModule("MeshSetup").InitialMeshSettings(["NAME:MeshSettings",
            ["NAME:GlobalSurfApproximation","CurvedSurfaceApproxChoice:=","ManualSettings","SurfDevChoice:=",2,
             "SurfDev:=","0.035mm","NormalDevChoice:=",2,"NormalDev:=","25deg","AspectRatioChoice:=",2,"AspectRatio:=","25"],
            ["NAME:GlobalCurvilinear","Apply:=",True],["NAME:GlobalModelRes","UseAutoLength:=",False,"DefeatureLength:=","0.002mm"],
            "MeshMethod:=","AnsoftTAU","DynamicSurfaceResolution:=",False,"UseFlexMeshingForTAUvolumeMesh:=",True,
            "UseLegacyFaceterForTauVolumeMesh:=",False,"UseAlternativeMeshMethodsAsFallBack:=",True,"AllowPhiForLayeredGeometry:=",False])
    d.GetModule("Solutions").EditSources([["IncludePortPostProcessing:=",False,"SpecifySystemPower:=",False]]+[["Name:=","N_"+p+":1","Magnitude:=","0.5W","Phase:=","0deg"] for p in "AB"])
    project.SaveAs(os.path.join(work,os.environ.get("P1H_NOME","P1H_R01")+".aedt"),True)
    valid=d.ValidateDesign();log(("valid",valid,list(oDesktop.GetMessages(project.GetName(),d.GetName(),1))))
    assert valid==1 and len(d.GetModule("Solutions").GetAllSources())==2
    log("MODELO_OK")
except:log(traceback.format_exc())
