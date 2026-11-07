# -*- coding: utf-8 -*-
"""Resolver cada PCB distribuidora completa com portas normalizadas em 50 ohms."""
import os,sys,json,traceback,re
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
repo=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0,os.path.join(repo,'automacao','r05'))
from enig_solido import apply
root=os.environ['P1H_R06']
def mm(v):return '%.12gmm'%v
for side in ['inferior','superior']:
    folder=os.path.join(root,'divisor_'+side);cad=os.path.join(folder,'cad')
    def log(s):
        with open(os.path.join(folder,'solucao.log'),'a') as f:f.write(str(s)+'\n')
    try:
        project=oDesktop.NewProject();project.InsertDesign('HFSS','Divisor_completo','DrivenModal','')
        design=project.SetActiveDesign('Divisor_completo');editor=design.SetActiveEditor('3D Modeler')
        editor.SetModelUnits(['NAME:Units Parameter','Units:=','mm','Rescale:=',False])
        definitions=project.GetDefinitionManager();boundaries=design.GetModule('BoundarySetup')
        for name,er,td in [('ZYF300',2.94,.0016),('PTFE_terminal',2.036363533774732,.00027683054882040843)]:
            definitions.AddMaterial(['NAME:'+name,'CoordinateSystemType:=','Cartesian','BulkOrSurfaceType:=',1,
              ['NAME:PhysicsTypes','set:=',['Electromagnetic']],'permittivity:=',str(er),'dielectric_loss_tangent:=',str(td)])
        definitions.AddMaterial(['NAME:SAC305','CoordinateSystemType:=','Cartesian','BulkOrSurfaceType:=',1,
          ['NAME:PhysicsTypes','set:=',['Electromagnetic']],'conductivity:=','7.575758e6'])
        manifest=json.load(open(os.path.join(cad,'manifesto.json')))
        for material in sorted(set(manifest.values())):
            before=set(editor.GetObjectsInGroup('Solids'))
            editor.Import(['NAME:NativeBodyParameters','HealOption:=',0,'Options:=','-1','FileType:=','UnRecognized',
              'MaxStitchTol:=',-1,'ImportFreeSurfaces:=',True,'GroupByAssembly:=',False,'CreateGroup:=',False,
              'MergeFacesAngle:=',-1,'PointCoincidenceTol:=',1e-6,'CreateLightweightPart:=',False,
              'ImportMaterialNames:=',False,'SeparateDisjointLumps:=',True,
              'SourceFile:=',os.path.join(cad,material+'.step'),'STLFileUnit:=','mm'])
            names=sorted(set(editor.GetObjectsInGroup('Solids'))-before);assert names,material
            if material=='folha_cu':
                assert set(names)==set(json.load(open(os.path.join(cad,'folhas_solidas.json')))), 'Cobre importado sem correspondencia ENIG'
            editor.AssignMaterial(['NAME:Selections','Selections:=',','.join(names)],
              ['NAME:Attributes','MaterialValue:=','"'+('copper' if material=='folha_cu' else material)+'"',
               'SolveInside:=',material in ('ZYF300','PTFE_terminal')])
        apply(project,design,json.load(open(os.path.join(cad,'folhas_solidas.json'))),os.path.join(cad,'enig_hfss.json'))
        ports=json.load(open(os.path.join(cad,'portas.json')))
        for p in ports:
            name,x,y,z,ri,ro=[p[k] for k in ['name','x','y','z','ri','ro']]
            for suffix,r in [('_ext',ro),('_int',ri)]:
                editor.CreateCircle(['NAME:CircleParameters','IsCovered:=',True,'XCenter:=',mm(x),'YCenter:=',mm(y),
                  'ZCenter:=',mm(z),'Radius:=',mm(r),'WhichAxis:=','Z','NumSegments:=','0'],
                  ['NAME:Attributes','Name:=',name+suffix,'MaterialValue:=','"vacuum"','SolveInside:=',True])
            editor.Subtract(['NAME:Selections','Blank Parts:=',name+'_ext','Tool Parts:=',name+'_int'],['NAME:SubtractParameters','KeepOriginals:=',False])
            boundaries.AssignLumpedPort(['NAME:'+name,'Objects:=',[name+'_ext'],'DoDeembed:=',False,
              'RenormalizeAllTerminals:=',True,['NAME:Modes',['NAME:Mode1','ModeNum:=',1,'UseIntLine:=',True,
              ['NAME:IntLine','Start:=',[mm(x+ri),mm(y),mm(z)],'End:=',[mm(x+ro),mm(y),mm(z)]],
              'AlignmentGroup:=',0,'CharImp:=','Zpi','RenormImp:=','50ohm']],'Impedance:=','50ohm'])
        design.GetModule('ModelSetup').CreateOpenRegion(['NAME:Settings','OpFreq:=','5.09GHz','Boundary:=','Radiation','ApplyInfiniteGP:=',False])
        setup=design.GetModule('AnalysisSetup')
        setup.InsertSetup('HfssDriven',['NAME:Centro','Frequency:=','5.17GHz','MaxDeltaS:=',.008,'MaximumPasses:=',16,
          'MinimumPasses:=',3,'MinimumConvergedPasses:=',2,'PercentRefinement:=',24,'BasisOrder:=',1])
        setup.InsertFrequencySweep('Centro',['NAME:Banda','IsEnabled:=',True,'RangeType:=','LinearStep',
          'RangeStart:=','5090MHz','RangeEnd:=','5250MHz','RangeStep:=','10MHz','Type:=','Discrete','SaveFields:=',False,'SaveRadFields:=',False])
        project.SaveAs(os.path.join(folder,'Divisor_'+side+'.aedt'),True)
        valid=design.ValidateDesign();log(('validacao',valid,list(oDesktop.GetMessages(project.GetName(),design.GetName(),2))))
        assert valid==1
        log('MODELO_DIVISOR_COMPLETO_OK');design.Analyze('Centro')
        design.ExportConvergence('Centro','',os.path.join(folder,'convergencia.txt'))
        project.Save()
        text=open(os.path.join(folder,'convergencia.txt')).read();assert 'Converged : Yes' in text
        design.GetModule('Solutions').ExportNetworkData('',['Centro : Banda'],3,os.path.join(folder,'divisor.s%dp'%len(ports)),['All'],True,50,'S',-1,1,15,False,True,False)
        project.Save();oDesktop.CloseProject(project.GetName());log('DIVISOR_COMPLETO_CONCLUIDO')
    except:log(traceback.format_exc());break
