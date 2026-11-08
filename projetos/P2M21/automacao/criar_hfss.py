# -*- coding: utf-8 -*-
"""Criar tres projetos HFSS separados. Nao executa solver automaticamente."""
import os,json,sys,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
repo=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0,os.path.join(repo,'automacao','r05'))
from enig_solido import apply
root='D:/dev/EMBRAER/P2M21/R00_Concepcao'
def mm(v):return '%.12gmm'%v
def read(path):
    with open(path) as f:return json.load(f)
def log(s):
    with open(os.path.join(root,'hfss_criacao.log'),'a') as f:f.write(str(s)+'\n')
for folder,filename in [('divisor_1x4','P2M21_Duplo_1x4'),('divisor_1x8','P2M21_Duplo_1x8'),('antena','P2M21_Antena')]:
    try:
        dest=os.path.join(root,folder);cad=os.path.join(dest,'cad')
        assert read(os.path.join(cad,'intersecoes.json'))['aprovado']
        p=oDesktop.NewProject();p.InsertDesign('HFSS','PCB_separada','DrivenModal','')
        d=p.SetActiveDesign('PCB_separada');e=d.SetActiveEditor('3D Modeler')
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
        if folder=='antena':
            d.GetModule('RadField').InsertInfiniteSphereSetup(['NAME:HV','UseCustomRadiationSurface:=',False,
             'CSDefinition:=','Theta-Phi','Polarization:=','Linear','ThetaStart:=','-180deg','ThetaStop:=','180deg',
             'ThetaStep:=','.25deg','PhiStart:=','0deg','PhiStop:=','90deg','PhiStep:=','90deg','UseLocalCS:=',False])
            sol.EditSources([['IncludePortPostProcessing:=',False,'SpecifySystemPower:=',False]]+
             [['Name:=',pt['name']+':1','Magnitude:=','0.03125W' if pt['name'].endswith('_A') else '0W','Phase:=','0deg'] for pt in ports])
            mesh=d.GetModule('MeshSetup');vias=[n for n in manifest if '_Via' in n]
            mesh.AssignTrueSurfOp(['NAME:Vias_curvatura','Objects:=',vias,'CurvedSurfaceApproxChoice:=','ManualSettings',
             'SurfDevChoice:=',2,'SurfDev:=','0.002mm','NormalDevChoice:=',2,'NormalDev:=','10deg','AspectRatioChoice:=',1,'AspectRatio:=','10'])
            small=[n for n in records if n.endswith('Cu1')]
            mesh.AssignLengthOp(['NAME:Fragmentos_locais','RefineInside:=',False,'Enabled:=',True,'Objects:=',small,
             'RestrictElem:=',False,'NumMaxElem:=','1000','RestrictLength:=',True,'MaxLength:=','0.06mm'])
        setup=d.GetModule('AnalysisSetup')
        setup.InsertSetup('HfssDriven',['NAME:Centro','Frequency:=','5.17GHz','MaxDeltaS:=',.02,
         'MaximumPasses:=',6,'MinimumPasses:=',2,'MinimumConvergedPasses:=',2,'PercentRefinement:=',20,
         'BasisOrder:=',0,'UseIterativeSolver:=',True,'IterativeResidual:=',1e-5,
         'SaveRadFieldsOnly:=',True])
        setup.InsertFrequencySweep('Centro',['NAME:Banda17','IsEnabled:=',True,'RangeType:=','LinearStep',
         'RangeStart:=','5090MHz','RangeEnd:=','5250MHz','RangeStep:=','10MHz','Type:=','Discrete',
         'SaveFields:=',folder=='antena','SaveRadFields:=',folder=='antena'])
        p.SaveAs(os.path.join(dest,filename+'.aedt'),True)
        valid=d.ValidateDesign();messages=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2))
        result=dict(modelo=filename,validacao=valid,erros=messages,portas=len(ports),max_passes=6,max_delta_s=.02,
         simulado=False,modo='PCB separada, restantes portas casadas em50ohms; cabos apenas no circuito')
        with open(os.path.join(dest,'hfss_validacao.json'),'w') as f:json.dump(result,f,indent=2)
        assert valid==1 and len(sol.GetAllSources())==len(ports),result
        p.Save();oDesktop.CloseProject(p.GetName());log('CRIADO_VALIDADO '+filename)
    except:
        log(traceback.format_exc());break
