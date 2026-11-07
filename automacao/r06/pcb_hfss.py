# -*- coding: utf-8 -*-
"""PCB de dez elementos sem chicote; Cu35um/ENIG e vinte portas diretamente na PCB."""
import json,os,sys,traceback,re
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
repo=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0,os.path.join(repo,'automacao','r05'))
from enig_solido import apply
from criterios_campo import configure
folder=os.path.join(os.environ['P1H_R06'],'antena');cad=os.path.join(folder,'cad')
def log(s):
    with open(os.path.join(folder,'solucao.log'),'a') as f:f.write(str(s)+'\n')
def mm(v):return '%.12gmm'%v
try:
    project=oDesktop.NewProject();project.InsertDesign('HFSS','PCB_sem_cabos','DrivenModal','')
    design=project.SetActiveDesign('PCB_sem_cabos');editor=design.SetActiveEditor('3D Modeler')
    editor.SetModelUnits(['NAME:Units Parameter','Units:=','mm','Rescale:=',False])
    definitions=project.GetDefinitionManager();boundaries=design.GetModule('BoundarySetup')
    dielectrics={'RO4350B_R01':(3.66,.0037),'POM_nom':(3.4,.01)}
    for name,values in dielectrics.items():
        definitions.AddMaterial(['NAME:'+name,'CoordinateSystemType:=','Cartesian','BulkOrSurfaceType:=',1,
          ['NAME:PhysicsTypes','set:=',['Electromagnetic']],'permittivity:=',str(values[0]),'dielectric_loss_tangent:=',str(values[1])])
    for name,sigma in [('AL5052',2e7),('aco_nom',1.4e6),('SAC305',7.575758e6)]:
        definitions.AddMaterial(['NAME:'+name,'CoordinateSystemType:=','Cartesian','BulkOrSurfaceType:=',1,
          ['NAME:PhysicsTypes','set:=',['Electromagnetic']],'conductivity:=',str(sigma)])
    manifest=json.load(open(os.path.join(cad,'manifesto.json')))
    for material in sorted(set(manifest.values())):
        before=set(editor.GetObjectsInGroup('Solids'))
        editor.Import(['NAME:NativeBodyParameters','HealOption:=',0,'Options:=','-1','FileType:=','UnRecognized',
          'MaxStitchTol:=',-1,'ImportFreeSurfaces:=',True,'GroupByAssembly:=',False,'CreateGroup:=',False,
          'MergeFacesAngle:=',-1,'PointCoincidenceTol:=',1e-6,'CreateLightweightPart:=',False,
          'ImportMaterialNames:=',False,'SeparateDisjointLumps:=',True,
          'SourceFile:=',os.path.join(cad,material+'.step'),'STLFileUnit:=','mm'])
        names=sorted(set(editor.GetObjectsInGroup('Solids'))-before)
        assert names,material
        if material=='folha_cu':assert set(names)==set(json.load(open(os.path.join(cad,'folhas_solidas.json'))))
        editor.AssignMaterial(['NAME:Selections','Selections:=',','.join(names)],
          ['NAME:Attributes','MaterialValue:=','"'+('copper' if material=='folha_cu' else material)+'"','SolveInside:=',material in dielectrics])
    apply(project,design,json.load(open(os.path.join(cad,'folhas_solidas.json'))),os.path.join(cad,'enig_hfss.json'))
    ports=json.load(open(os.path.join(cad,'portas.json')))
    for p in ports:
        name,x,y,z,ri,ro=[p[k] for k in ['name','x','y','z','ri','ro']]
        for suffix,r in [('_externo',ro),('_interno',ri)]:
            editor.CreateCircle(['NAME:CircleParameters','IsCovered:=',True,'XCenter:=',mm(x),'YCenter:=',mm(y),
              'ZCenter:=',mm(z),'Radius:=',mm(r),'WhichAxis:=','Z','NumSegments:=','0'],
              ['NAME:Attributes','Name:=',name+suffix,'MaterialValue:=','"vacuum"','SolveInside:=',True])
        editor.Subtract(['NAME:Selections','Blank Parts:=',name+'_externo','Tool Parts:=',name+'_interno'],['NAME:SubtractParameters','KeepOriginals:=',False])
        boundaries.AssignLumpedPort(['NAME:'+name,'Objects:=',[name+'_externo'],'DoDeembed:=',False,
          'RenormalizeAllTerminals:=',True,['NAME:Modes',['NAME:Mode1','ModeNum:=',1,'UseIntLine:=',True,
          ['NAME:IntLine','Start:=',[mm(x+ri),mm(y),mm(z)],'End:=',[mm(x+ro),mm(y),mm(z)]],
          'AlignmentGroup:=',0,'CharImp:=','Zpi','RenormImp:=','50ohm']],'Impedance:=','50ohm'])
    design.GetModule('ModelSetup').CreateOpenRegion(['NAME:Settings','OpFreq:=','5.09GHz','Boundary:=','Radiation','ApplyInfiniteGP:=',False])
    design.GetModule('RadField').InsertInfiniteSphereSetup(['NAME:HV','UseCustomRadiationSurface:=',False,
      'CSDefinition:=','Theta-Phi','Polarization:=','Linear','ThetaStart:=','-180deg','ThetaStop:=','180deg',
      'ThetaStep:=','.25deg','PhiStart:=','0deg','PhiStop:=','90deg','PhiStep:=','90deg','UseLocalCS:=',False])
    sources=design.GetModule('Solutions')
    sources.EditSources([['IncludePortPostProcessing:=',False,'SpecifySystemPower:=',False]]+
      [['Name:=',p['name']+':1','Magnitude:=','0.05W','Phase:=','0deg'] for p in ports])
    configure(design)
    vias=[n for n in editor.GetObjectsInGroup('Solids') if n.startswith('Via')]
    design.GetModule('MeshSetup').AssignTrueSurfOp(['NAME:Vias_curvatura','Objects:=',vias,
      'CurvedSurfaceApproxChoice:=','ManualSettings','SurfDevChoice:=',2,'SurfDev:=','0.002mm',
      'NormalDevChoice:=',2,'NormalDev:=','10deg','AspectRatioChoice:=',1,'AspectRatio:=','10'])
    project.SaveAs(os.path.join(folder,'PCB_R06.aedt'),True)
    valid=design.ValidateDesign();log(('validacao',valid,list(oDesktop.GetMessages(project.GetName(),design.GetName(),2))))
    assert valid==1 and len(sources.GetAllSources())==20
    log('MODELO_PCB_SEM_CABOS_OK');design.Analyze('Banda')
    design.ExportConvergence('Banda','',os.path.join(folder,'convergencia.txt'))
    project.Save()
    sources.ExportNetworkData('',['Banda : LastAdaptive'],3,os.path.join(folder,'antena.s20p'),['All'],True,50,'S',-1,1,15,False,True,False)
    reports=design.GetModule('ReportSetup')
    for axis,phi in [('H',90),('V',0)]:
        reports.CreateReport(axis,'Far Fields','Rectangular Plot','Banda : LastAdaptive',['Context:=','HV'],
          ['Theta:=',['All'],'Phi:=',[str(phi)+'deg'],'Freq:=',['5.17GHz']],
          ['X Component:=','Theta','Y Component:=',['dB(RealizedGainTotal)','dB(GainTotal)','dB(DirTotal)']])
        reports.ExportToFile(axis,os.path.join(folder,'Centro_'+axis+'.csv'),False)
    project.Save();oDesktop.CloseProject(project.GetName());log('CENTRO_PCB_CONCLUIDO_CONFERIR_CONVERGENCIA')
except:log(traceback.format_exc())
