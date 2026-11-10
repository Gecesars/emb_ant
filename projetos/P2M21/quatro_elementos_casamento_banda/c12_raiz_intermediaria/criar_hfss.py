# -*- coding: utf-8 -*-
"""Criar o projeto HFSS de quatro elementos. Nao executa solver automaticamente."""
import os,json,sys,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')

repo='D:/dev/EMBRAER/emb_ant'
sys.path.insert(0,os.path.join(repo,'automacao','r05'))
from enig_solido import apply
root='D:/dev/EMBRAER/P2M21/R13_Casamento_Banda/c12_raiz_intermediaria'
def mm(v):return '%.12gmm'%v
def read(path):
    with open(path) as f:return json.load(f)
def log(s):
    with open(os.path.join(root,'hfss_criacao.log'),'a') as f:f.write(str(s)+'\n')
for folder,filename in [('', 'P2M21_4_elementos')]:
    try:
        dest=os.path.join(root,folder);cad=os.path.join(dest,'cad')
        assert read(os.path.join(cad,'intersecoes.json'))['aprovado']
        p=oDesktop.NewProject();p.InsertDesign('HFSS','Quatro_elementos','DrivenModal','')
        d=p.SetActiveDesign('Quatro_elementos');e=d.SetActiveEditor('3D Modeler')
        e.SetModelUnits(['NAME:Units Parameter','Units:=','mm','Rescale:=',False])
        defs=p.GetDefinitionManager();bd=d.GetModule('BoundarySetup')
        dies={'RO4350B_R01':(3.66,.0037),'POM_nom':(3.4,.01),'ZYF300':(2.94,.0016),
              'PTFE_terminal':(2.036363533774732,.00027683054882040843)}
        for name,(er,td) in dies.items():
            defs.AddMaterial(['NAME:'+name,'CoordinateSystemType:=','Cartesian','BulkOrSurfaceType:=',1,
             ['NAME:PhysicsTypes','set:=',['Electromagnetic']],'permittivity:=',str(er),'dielectric_loss_tangent:=',str(td)])
        for name,sigma in [('AL5052',2e7),('SAC305',7.575758e6)]:
            defs.AddMaterial(['NAME:'+name,'CoordinateSystemType:=','Cartesian','BulkOrSurfaceType:=',1,
             ['NAME:PhysicsTypes','set:=',['Electromagnetic']],'conductivity:=',str(sigma)])
        manifest=read(os.path.join(cad,'manifesto.json'));records=read(os.path.join(cad,'folhas_solidas.json'))
        for material in sorted(set(manifest.values())):
            before=set(e.GetObjectsInGroup('Solids'))
            e.Import(['NAME:NativeBodyParameters','HealOption:=',0,'Options:=','-1','FileType:=','UnRecognized',
             'MaxStitchTol:=',-1,'ImportFreeSurfaces:=',True,'GroupByAssembly:=',False,'CreateGroup:=',False,
             'MergeFacesAngle:=',-1,'PointCoincidenceTol:=',1e-6,'CreateLightweightPart:=',False,
             'ImportMaterialNames:=',False,'SeparateDisjointLumps:=',True,
             'SourceFile:=',os.path.join(cad,material+'.step'),'STLFileUnit:=','mm'])
            names=sorted(set(e.GetObjectsInGroup('Solids'))-before)
            expected=sorted(n for n,m in manifest.items() if m==material)
            # AEDT nomeia um STEP de corpo unico pelo arquivo, nao pelo label CAD.
            if len(names)==len(expected)==1 and names!=expected:
                e.ChangeProperty(['NAME:AllTabs',['NAME:Geometry3DAttributeTab',['NAME:PropServers',names[0]],
                 ['NAME:ChangedProps',['NAME:Name','Value:=',expected[0]]]]])
                names=expected
            assert set(names)==set(expected),(material,names)
            e.AssignMaterial(['NAME:Selections','Selections:=',','.join(names)],
             ['NAME:Attributes','MaterialValue:=','"'+('copper' if material=='folha_cu' else material)+'"','SolveInside:=',material in dies])
        apply(p,d,records,os.path.join(cad,'enig_hfss.json'))
        ports=read(os.path.join(cad,'portas.json'))
        for pt in ports:
            name,x,y,z,ri,ro=[pt[k] for k in ['name','x','y','z','ri','ro']]
            for suf,r in [('_ext',ro),('_int',ri)]:
                e.CreateCircle(['NAME:CircleParameters','IsCovered:=',True,'XCenter:=',mm(x),'YCenter:=',mm(y),
                 'ZCenter:=',mm(z),'Radius:=',mm(r),'WhichAxis:=','Z','NumSegments:=','0'],
                 ['NAME:Attributes','Name:=',name+suf,'MaterialValue:=','"vacuum"','SolveInside:=',True])
            e.Subtract(['NAME:Selections','Blank Parts:=',name+'_ext','Tool Parts:=',name+'_int'],['NAME:SubtractParameters','KeepOriginals:=',False])
            bd.AssignLumpedPort(['NAME:'+name,'Objects:=',[name+'_ext'],'DoDeembed:=',False,
             'RenormalizeAllTerminals:=',True,['NAME:Modes',['NAME:Mode1','ModeNum:=',1,'UseIntLine:=',True,
             ['NAME:IntLine','Start:=',[mm(x+ri),mm(y),mm(z)],'End:=',[mm(x+ro),mm(y),mm(z)]],
             'AlignmentGroup:=',0,'CharImp:=','Zpi','RenormImp:=','50ohm']],'Impedance:=','50ohm'])
        d.GetModule('ModelSetup').CreateOpenRegion(['NAME:Settings','OpFreq:=','5.09GHz','Boundary:=','Radiation','ApplyInfiniteGP:=',False])
        sol=d.GetModule('Solutions')
        if True:
            d.GetModule('RadField').InsertInfiniteSphereSetup(['NAME:HV','UseCustomRadiationSurface:=',False,
             'CSDefinition:=','Theta-Phi','Polarization:=','Linear','ThetaStart:=','-180deg','ThetaStop:=','180deg',
             'ThetaStep:=','.25deg','PhiStart:=','0deg','PhiStop:=','90deg','PhiStep:=','90deg','UseLocalCS:=',False])
            sol.EditSources([['IncludePortPostProcessing:=',False,'SpecifySystemPower:=',False]]+
             [['Name:=',pt['name']+':1','Magnitude:=','0.5W','Phase:=','0deg'] for pt in ports])
        mesh=d.GetModule('MeshSetup')
        mesh.InitialMeshSettings(['NAME:MeshSettings',
          ['NAME:GlobalSurfApproximation','CurvedSurfaceApproxChoice:=','UseSlider','SliderMeshSettings:=',5],
          ['NAME:GlobalCurvilinear','Apply:=',False],['NAME:GlobalModelRes','UseAutoLength:=',True],
          'MeshMethod:=','AnsoftClassic','UseLegacyFaceterForTauVolumeMesh:=',False,
          'DynamicSurfaceResolution:=',False,'UseFlexMeshingForTAUvolumeMesh:=',False,
          'UseAlternativeMeshMethodsAsFallBack:=',False,'AllowPhiForLayeredGeometry:=',False])
        setup=d.GetModule('AnalysisSetup')
        setup.InsertSetup('HfssDriven',['NAME:Centro','Frequency:=','5.17GHz','MaxDeltaS:=',.05,
          'MaximumPasses:=',6,'MinimumPasses:=',6,'MinimumConvergedPasses:=',2,'PercentRefinement:=',75,
          'BasisOrder:=',2,'DoLambdaRefine:=',False,'SetLambdaTarget:=',False,
          'DrivenSolverType:=','Iterative Solver','IterativeResidual:=',1e-5,
          'SaveAnyFields:=',True,'SaveRadFieldsOnly:=',True])
        assert not list(setup.GetSweeps('Centro'))
        p.SaveAs(os.path.join(dest,filename+'.aedt'),True)
        valid=d.ValidateDesign();messages=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2))
        result=dict(modelo=filename,validacao=valid,erros=messages,portas=len(ports),max_passes=6,max_delta_s=.05,
         simulado=False,modo='Quatro elementos verticais e dois divisores 1:4 impressos, dois cabos fisicos de 50mm e refletor local; portas nas extremidades dos cabos')
        with open(os.path.join(dest,'hfss_validacao.json'),'w') as f:json.dump(result,f,indent=2)
        assert valid==1 and len(sol.GetAllSources())==len(ports),result
        p.Save();oDesktop.CloseProject(p.GetName());log('CRIADO_VALIDADO_HEADLESS '+filename)
    except:
        log(traceback.format_exc());raise
