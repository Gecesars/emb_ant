# -*- coding: utf-8 -*-
"""Cria e resolve divisor duplo1:3 fisico; seis passes/14cores/sem sweep."""
import os,sys,json,datetime,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
repo='D:/dev/EMBRAER/emb_ant';root=os.environ.get('P2S13_DIV3_ROOT','D:/dev/EMBRAER/P2S13/R08_Divisor_HFSS')
sys.path.insert(0,os.path.join(repo,'projetos','P2S13','automacao'));from r11_enig import apply
cfg=json.load(open(os.path.join(root,'configuracao.json')));cad=os.path.join(root,'cad')
def mm(v):return '%.12gmm'%v
def save(n,v):
    with open(os.path.join(root,n),'w') as f:json.dump(v,f,indent=2)
def log(s):
    with open(os.path.join(root,'hfss.log'),'a') as f:f.write(datetime.datetime.now().isoformat()+' '+s+'\n')
try:
    native=os.path.join(root,cfg['native']);assert not os.path.exists(native),'Nao sobrescrever nativo'
    assert json.load(open(os.path.join(cad,'intersecoes.json')))['aprovado']
    p=oDesktop.NewProject();p.InsertDesign('HFSS',cfg['design'],'DrivenModal','')
    d=p.SetActiveDesign(cfg['design']);e=d.SetActiveEditor('3D Modeler');defs=p.GetDefinitionManager();bd=d.GetModule('BoundarySetup')
    e.SetModelUnits(['NAME:Units Parameter','Units:=','mm','Rescale:=',False])
    dies={'ZYF300':(2.94,.0016),'PTFE_terminal':(2.036363533774732,.00027683054882040843),'Alumina_nominal':(9.8,.0001)}
    if cfg.get('mask_windows'):dies['Soldermask_nominal']=(cfg['mask_windows']['er'],cfg['mask_windows']['tand'])
    for name,(er,td) in dies.items():
        defs.AddMaterial(['NAME:'+name,'CoordinateSystemType:=','Cartesian','BulkOrSurfaceType:=',1,
         ['NAME:PhysicsTypes','set:=',['Electromagnetic']],'permittivity:=',str(er),'dielectric_loss_tangent:=',str(td)])
    defs.AddMaterial(['NAME:SAC305','CoordinateSystemType:=','Cartesian','BulkOrSurfaceType:=',1,
        ['NAME:PhysicsTypes','set:=',['Electromagnetic']],'conductivity:=','7.575758e6'])
    if cfg.get('shield'):
        defs.AddMaterial(['NAME:AL5052','CoordinateSystemType:=','Cartesian','BulkOrSurfaceType:=',1,
            ['NAME:PhysicsTypes','set:=',['Electromagnetic']],'conductivity:=',str(cfg['shield']['conductivity_S_m'])])
    man=json.load(open(os.path.join(cad,'manifesto.json')))
    for mat in sorted(set(man.values())):
        old=set(e.GetObjectsInGroup('Solids'))
        e.Import(['NAME:NativeBodyParameters','HealOption:=',0,'Options:=','-1','FileType:=','UnRecognized',
         'MaxStitchTol:=',-1,'ImportFreeSurfaces:=',True,'GroupByAssembly:=',False,'CreateGroup:=',False,
         'MergeFacesAngle:=',-1,'PointCoincidenceTol:=',1e-6,'CreateLightweightPart:=',False,
         'ImportMaterialNames:=',False,'SeparateDisjointLumps:=',True,'SourceFile:=',os.path.join(cad,mat+'.step'),'STLFileUnit:=','mm'])
        names=sorted(set(e.GetObjectsInGroup('Solids'))-old);expected=sorted(n for n,m in man.items() if m==mat)
        if len(names)==len(expected)==1 and names!=expected:
            e.ChangeProperty(['NAME:AllTabs',['NAME:Geometry3DAttributeTab',['NAME:PropServers',names[0]],['NAME:ChangedProps',['NAME:Name','Value:=',expected[0]]]]]);names=expected
        assert names==expected,(mat,names,expected)
        e.AssignMaterial(['NAME:Selections','Selections:=',','.join(names)],['NAME:Attributes','MaterialValue:=','"'+('copper' if mat=='folha_cu' else mat)+'"','SolveInside:=',mat in dies])
    apply(p,d,json.load(open(os.path.join(cad,'folhas_solidas.json'))),os.path.join(cad,'enig_hfss.json'))
    for r in cfg['resistores']:
        name=r['name']+'_RLC';x=r['x'];y=r['y'];z=cfg['h']+cfg['cu']
        e.CreateRectangle(['NAME:RectangleParameters','IsCovered:=',True,'XStart:=',mm(x-.3),'YStart:=',mm(y-.2),'ZStart:=',mm(z),
            'Width:=','.6mm','Height:=','.4mm','WhichAxis:=','Z'],['NAME:Attributes','Name:=',name,'MaterialValue:=','"vacuum"','SolveInside:=',True])
        bd.AssignLumpedRLC(['NAME:'+name,'Objects:=',[name],['NAME:CurrentLine','Start:=',[mm(x),mm(y-.2),mm(z)],'End:=',[mm(x),mm(y+.2),mm(z)]],
            'RLC Type:=','Parallel','UseResist:=',True,'Resistance:=',str(r['R'])+'ohm','UseInduct:=',False,'UseCap:=',False])
    for pt in cfg['portas']:
        name,x,y,z,ri,ro=[pt[k] for k in ['name','x','y','z','ri','ro']]
        for suf,r in [('_ext',ro),('_int',ri)]:
            e.CreateCircle(['NAME:CircleParameters','IsCovered:=',True,'XCenter:=',mm(x),'YCenter:=',mm(y),'ZCenter:=',mm(z),
                'Radius:=',mm(r),'WhichAxis:=','Z','NumSegments:=','0'],['NAME:Attributes','Name:=',name+suf,'MaterialValue:=','"vacuum"','SolveInside:=',True])
        e.Subtract(['NAME:Selections','Blank Parts:=',name+'_ext','Tool Parts:=',name+'_int'],['NAME:SubtractParameters','KeepOriginals:=',False])
        bd.AssignLumpedPort(['NAME:'+name,'Objects:=',[name+'_ext'],'DoDeembed:=',False,'RenormalizeAllTerminals:=',True,
          ['NAME:Modes',['NAME:Mode1','ModeNum:=',1,'UseIntLine:=',True,['NAME:IntLine','Start:=',[mm(x+ri),mm(y),mm(z)],'End:=',[mm(x+ro),mm(y),mm(z)]],
            'AlignmentGroup:=',0,'CharImp:=','Zpi','RenormImp:=','50ohm']],'Impedance:=','50ohm'])
    d.GetModule('ModelSetup').CreateOpenRegion(['NAME:Settings','OpFreq:=','5.17GHz','Boundary:=','Radiation','ApplyInfiniteGP:=',False])
    d.GetModule('MeshSetup').InitialMeshSettings(['NAME:MeshSettings',
        ['NAME:GlobalSurfApproximation','CurvedSurfaceApproxChoice:=','UseSlider','SliderMeshSettings:=',5],
        ['NAME:GlobalCurvilinear','Apply:=',True],['NAME:GlobalModelRes','UseAutoLength:=',True],
        'MeshMethod:=','AnsoftClassic','UseLegacyFaceterForTauVolumeMesh:=',False,'DynamicSurfaceResolution:=',False,
        'UseFlexMeshingForTAUvolumeMesh:=',False,'UseAlternativeMeshMethodsAsFallBack:=',False,'AllowPhiForLayeredGeometry:=',False])
    an=d.GetModule('AnalysisSetup');an.InsertSetup('HfssDriven',['NAME:Centro','Frequency:=','5.17GHz','MaxDeltaS:=',.05,
        'MaximumPasses:=',6,'MinimumPasses:=',2,'MinimumConvergedPasses:=',2,'PercentRefinement:=',cfg.get('percent_refinement',30),
        'BasisOrder:=',cfg.get('basis_order',1),'DoLambdaRefine:=',False,'SetLambdaTarget:=',False,'DrivenSolverType:=','Direct Solver',
        'SaveAnyFields:=',True,'SaveRadFieldsOnly:=',True])
    sol=d.GetModule('Solutions');ports=list(sol.GetAllSources());assert len(ports)==8
    sol.EditSources([['IncludePortPostProcessing:=',False,'SpecifySystemPower:=',False]]+
        [['Name:=',n+':1','Magnitude:=','.5W' if n.startswith('IN_') else '0W','Phase:=','0deg'] for n in ports])
    p.SaveAs(native,True);valid=d.ValidateDesign();errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2))
    save('hfss_validacao.json',dict(validacao=valid,erros=errors,portas=ports,solidos=len(man),sweeps=list(an.GetSweeps('Centro'))));assert valid==1 and not errors
    assert not list(an.GetSweeps('Centro'))
    oDesktop.SetRegistryFromFile(os.path.join(root,'HFSS_14nucleos.acf'))
    oDesktop.SetRegistryString('Desktop/ActiveDSOConfigurations/HFSS','P2M21_14nucleos')
    assert oDesktop.GetRegistryString('Desktop/ActiveDSOConfigurations/HFSS')=='P2M21_14nucleos'
    save('estado.json',dict(estado='EM_CALCULO',inicio=datetime.datetime.now().isoformat(),nucleos=14,max_passes=6,delta_s=.05))
    log('SOLVE_INICIADO_14NUCLEOS_MAX6');d.Analyze('Centro')
    d.ExportConvergence('Centro','',os.path.join(root,'convergencia.txt'))
    save('mensagens.json',list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)))
    errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2));assert not errors,errors
    sol.ExportNetworkData('',['Centro : LastAdaptive'],3,os.path.join(root,'divisor.s8p'),['All'],True,50,'S',-1,1,15,False,True,False)
    p.SaveAs(native,True);oDesktop.CloseProject(p.GetName())
    save('estado.json',dict(estado='CONCLUIDO_AGUARDA_ANALISE',fim=datetime.datetime.now().isoformat()))
    log('SOLVE_EXPORTADO')
except:
    save('falha.json',dict(erro=traceback.format_exc()));log(traceback.format_exc());raise
