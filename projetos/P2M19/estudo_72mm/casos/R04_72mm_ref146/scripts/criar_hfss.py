# -*- coding: utf-8 -*-
"""Criar a P2M19 com oito celulas C12. Nao executa solver automaticamente."""
import os,json,sys,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')

repo='D:/dev/EMBRAER/emb_ant'
sys.path.insert(0,os.path.join(repo,'automacao','r05'))
from enig_solido import apply
root='D:/dev/EMBRAER/P2M19/R04_72mm_ref146'
cfg=json.load(open(os.path.join(root,'configuracao.json')))
def mm(v):return '%.12gmm'%v
def read(path):
    with open(path) as f:return json.load(f)
def log(s):
    with open(os.path.join(root,'hfss_criacao.log'),'a') as f:f.write(str(s)+'\n')
for folder,filename in [('', os.path.splitext(cfg['native'])[0])]:
    try:
        dest=os.path.join(root,folder);cad=os.path.join(dest,'cad')
        assert read(os.path.join(cad,'intersecoes.json'))['aprovado']
        assert not os.path.exists(os.path.join(root,cfg['native'])),'Nativo existente'
        p=oDesktop.NewProject();p.InsertDesign('HFSS',cfg['design'],'DrivenModal','')
        d=p.SetActiveDesign(cfg['design']);e=d.SetActiveEditor('3D Modeler')
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
        geometry=read(os.path.join(cad,'geometria_esperada.json'));checks={}
        for n,geo in geometry.items():
            bbox=[float(x) for x in e.GetObjectBoundingBox(n)];vol=float(e.GetObjectVolume(n))
            eb=max(abs(x-y) for x,y in zip(bbox,geo['bbox_mm']));ev=abs(vol-geo['volume_mm3'])/geo['volume_mm3']
            checks[n]=dict(erro_bbox_mm=eb,erro_volume_rel=ev,aprovado=eb<.001 and ev<.001)
        with open(os.path.join(root,'geometria_importada.json'),'w') as f:json.dump(checks,f,indent=2)
        assert all(x['aprovado'] for x in checks.values()),'Geometria importada diverge'
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
             [['Name:=',pt['name']+':1','Magnitude:=','%.12gW'%cfg['potencia_por_porta_W'],'Phase:=','0deg'] for pt in ports])
        d.GetModule('RadField').InsertInfiniteSphereSetup(['NAME:Centro_fino','UseCustomRadiationSurface:=',False,
          'CSDefinition:=','Theta-Phi','Polarization:=','Linear','ThetaStart:=','-20deg','ThetaStop:=','20deg',
          'ThetaStep:=','.05deg','PhiStart:=','0deg','PhiStop:=','90deg','PhiStep:=','90deg','UseLocalCS:=',False])
        d.GetModule('RadField').InsertInfiniteSphereSetup(['NAME:Potencia','UseCustomRadiationSurface:=',False,
          'CSDefinition:=','Theta-Phi','Polarization:=','Linear','ThetaStart:=','0deg','ThetaStop:=','180deg',
          'ThetaStep:=','2deg','PhiStart:=','0deg','PhiStop:=','360deg','PhiStep:=','2deg','UseLocalCS:=',False])
        mesh=d.GetModule('MeshSetup')
        mesh.InitialMeshSettings(['NAME:MeshSettings',
          ['NAME:GlobalSurfApproximation','CurvedSurfaceApproxChoice:=','UseSlider','SliderMeshSettings:=',5],
          ['NAME:GlobalCurvilinear','Apply:=',True],['NAME:GlobalModelRes','UseAutoLength:=',True],
          'MeshMethod:=','AnsoftClassic','UseLegacyFaceterForTauVolumeMesh:=',False,
          'DynamicSurfaceResolution:=',False,'UseFlexMeshingForTAUvolumeMesh:=',False,
          'UseAlternativeMeshMethodsAsFallBack:=',False,'AllowPhiForLayeredGeometry:=',False])
        setup=d.GetModule('AnalysisSetup')
        setup.InsertSetup('HfssDriven',['NAME:Centro','Frequency:=','5.17GHz','MaxDeltaS:=',.05,
          'MaximumPasses:=',6,'MinimumPasses:=',2,'MinimumConvergedPasses:=',2,'PercentRefinement:=',20,
          'BasisOrder:=',1,'DoLambdaRefine:=',False,'SetLambdaTarget:=',False,
          'DrivenSolverType:=','Direct Solver','IterativeResidual:=',1e-5,
          'SaveAnyFields:=',True,'SaveRadFieldsOnly:=',True])
        cache=['NAME:ExpressionCache']
        for i,(theta,phi) in enumerate([(0,90),(-10,90),(10,90),(-54,90),(54,90),(-1.75,0),(1.75,0),(-45,0),(45,0)]):
            cache.append(['NAME:CacheItem','Title:=','P2M19_Campo_%02d'%i,'Expression:=','dB(RealizedGainTotal)',
             'Intrinsics:=',"Phi='%sdeg' Theta='%sdeg'"%(phi,theta),'IsConvergence:=',False,
             'UseRelativeConvergence:=',0,'MaxConvergenceDelta:=',.1,'MaxConvergeValue:=','0.1',
             'ReportType:=','Far Fields',['NAME:ExpressionContext','Context:=','HV']])
        setup.EditSetup('Centro',['NAME:Centro','UseCacheFor:=',['Pass'],cache])
        assert len(ports)==len(cfg['portas']) and len(manifest)==41*len(cfg['celulas'])+1
        assert not list(setup.GetSweeps('Centro'))
        p.SaveAs(os.path.join(dest,filename+'.aedt'),True)
        valid=d.ValidateDesign();messages=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2))
        result=dict(modelo=filename,validacao=valid,erros=messages,portas=len(ports),max_passes=6,max_delta_s=.05,
         simulado=False,modo='%d celulas C12, %dx2 radiadores; %d portas iguais, terminais locais0.18mm e refletor comum; sem cabos ou rede externa'%(len(cfg['celulas']),cfg['niveis_radiadores'],len(ports)))
        with open(os.path.join(dest,'hfss_validacao.json'),'w') as f:json.dump(result,f,indent=2)
        assert valid==1 and len(sol.GetAllSources())==len(ports),result
        p.Save();oDesktop.CloseProject(p.GetName());log('CRIADO_VALIDADO_HEADLESS '+filename)
    except:
        log(traceback.format_exc());raise
