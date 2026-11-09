# -*- coding: utf-8 -*-
"""Somente centro, sem operacoes locais nem refinamento lambda inicial."""
import os,json,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P2M21_UNIFORME'];folder=os.path.join(root,'antena');p=None
def log(s):
    with open(os.path.join(folder,'preparacao.log'),'a') as f:f.write(str(s)+'\n')
try:
    cfg=json.load(open(os.path.join(root,'configuracao.json')));assert cfg['apenas_centro']
    p=oDesktop.OpenProject(os.path.join(folder,cfg['native']));d=p.SetActiveDesign('PCB_separada')
    mesh=d.GetModule('MeshSetup');removed=[]
    for kind in ['Length Based','Surface Approximation Based']:
        names=list(mesh.GetOperationNames(kind))
        if names:mesh.DeleteOp(names);removed.extend(names)
        assert not list(mesh.GetOperationNames(kind))
    # Classic avoids the TAU repair seen without local controls. Keep the
    # standard global slider/resolution; no local sizing or lambda refinement.
    mesh.InitialMeshSettings(['NAME:MeshSettings',
      ['NAME:GlobalSurfApproximation','CurvedSurfaceApproxChoice:=','UseSlider','SliderMeshSettings:=',5],
      ['NAME:GlobalCurvilinear','Apply:=',False],['NAME:GlobalModelRes','UseAutoLength:=',True],
      'MeshMethod:=','AnsoftClassic','UseLegacyFaceterForTauVolumeMesh:=',False,
      'DynamicSurfaceResolution:=',False,'UseFlexMeshingForTAUvolumeMesh:=',False,
      'UseAlternativeMeshMethodsAsFallBack:=',False,'AllowPhiForLayeredGeometry:=',False])
    setup=d.GetModule('AnalysisSetup')
    old=list(setup.GetSetups())
    if old:setup.DeleteSetups(old)
    setup.InsertSetup('HfssDriven',['NAME:Centro','Frequency:=','5.17GHz','MaxDeltaS:=',.04,
      'MaximumPasses:=',6,'MinimumPasses:=',2,'MinimumConvergedPasses:=',2,'PercentRefinement:=',20,
      'BasisOrder:=',-1,'DoLambdaRefine:=',False,'SetLambdaTarget:=',False,
      'DrivenSolverType:=','Iterative Solver','IterativeResidual:=',1e-5,
      'SaveAnyFields:=',True,'SaveRadFieldsOnly:=',True])
    sol=d.GetModule('Solutions');ports=list(sol.GetAllSources());assert len(ports)==64
    sol.EditSources([['IncludePortPostProcessing:=',False,'SpecifySystemPower:=',False]]+
      [['Name:=',s+':1','Magnitude:=','0.015625W','Phase:=','0deg'] for s in ports])
    cache=['NAME:ExpressionCache']
    for i,(theta,phi) in enumerate([(0,90),(-18,90),(18,90),(-20,90),(20,90),(-22,90),(22,90),(-1.75,0),(1.75,0)]):
        cache.append(['NAME:CacheItem','Title:=','U_R03_%02d'%i,'Expression:=','dB(RealizedGainTotal)',
          'Intrinsics:=',"Phi='%sdeg' Theta='%sdeg'"%(phi,theta),'IsConvergence:=',False,
          'UseRelativeConvergence:=',0,'MaxConvergenceDelta:=',.1,'MaxConvergeValue:=','0.1',
          'ReportType:=','Far Fields',['NAME:ExpressionContext','Context:=','HV']])
    setup.EditSetup('Centro',['NAME:Centro','BasisOrder:=',-1,'DoLambdaRefine:=',False,
      'MaxDeltaS:=',.04,'MaximumPasses:=',6,'MinimumPasses:=',2,'MinimumConvergedPasses:=',2,
      'DrivenSolverType:=','Iterative Solver','IterativeResidual:=',1e-5,
      'SaveAnyFields:=',True,'SaveRadFieldsOnly:=',True,'UseCacheFor:=',['Pass'],cache])
    sweeps=list(setup.GetSweeps('Centro'));assert not sweeps,sweeps
    valid=d.ValidateDesign();errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2))
    with open(os.path.join(folder,'preparacao.json'),'w') as f:
        json.dump(dict(validacao=valid,erros=errors,operacoes_removidas=removed,sweeps=sweeps,
          frequencia_GHz=5.17,basis_order=-1,basis='Mixed Order',lambda_refine=False,mesher='AnsoftClassic',
          max_passes=6,delta_s=.04,portas=ports,potencia_por_porta_W=.015625,fase_graus=0,
          campos_por_passe='Monitoramento apenas'),f,indent=2)
    assert valid==1 and not errors
    p.Save();oDesktop.CloseProject(p.GetName());p=None;log('PREPARACAO_CENTRO_AUTOMATICO_OK')
except:log(traceback.format_exc())
finally:
    if p is not None:p.Save();oDesktop.CloseProject(p.GetName())
