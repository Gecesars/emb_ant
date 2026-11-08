# -*- coding: utf-8 -*-
"""Preparar R07 sem solve; malha fonte R06 preservada, novos limites6/.02."""
import os,json,re,hashlib,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P1H_R07'];folder=os.path.join(root,'antena')
source=os.path.join(os.path.dirname(root),'R06_sem_cabos','antena','PCB_R06.aedt')
native=os.path.join(folder,'PCB_R07.aedt')
def log(s):
    with open(os.path.join(folder,'preparacao.log'),'a') as f:f.write(str(s)+'\n')
try:
    source_hash=hashlib.sha256(open(source,'rb').read()).hexdigest()
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign('PCB_sem_cabos')
    sol=d.GetModule('Solutions');assert len(sol.GetAllSources())==20
    setup=d.GetModule('AnalysisSetup');setup.DeleteSetups(list(setup.GetSetups()))
    reports=d.GetModule('ReportSetup');names=list(reports.GetAllReportNames())
    if names:reports.DeleteReports(names)
    cache=['NAME:ExpressionCache']
    for theta,phi in [(0,90),(-60,90),(-50,90),(-40,90),(40,90),(50,90),(60,90),(-3,0),(3,0)]:
        cache.append(['NAME:CacheItem','Title:=','G_%s%d_P%d'%('M' if theta<0 else 'P',abs(theta),phi),
          'Expression:=','dB(RealizedGainTotal)','Intrinsics:=',"Phi='%sdeg' Theta='%sdeg'"%(phi,theta),
          'IsConvergence:=',True,'UseRelativeConvergence:=',0,'MaxConvergenceDelta:=',.02,
          'MaxConvergeValue:=','0.02','ReportType:=','Far Fields',['NAME:ExpressionContext','Context:=','HV']])
    setup.InsertSetup('HfssDriven',['NAME:Banda','Frequency:=','5.17GHz','MaxDeltaS:=',.02,
      'MaximumPasses:=',6,'MinimumPasses:=',2,'MinimumConvergedPasses:=',2])
    mesh=['NAME:MeshLink','ImportMesh:=',True,'Project:=',source,'Product:=','HFSS',
      'Design:=','PCB_sem_cabos','Soln:=','Banda : LastAdaptive',['NAME:Params'],
      'ForceSourceToSolve:=',False,'PreservePartnerSoln:=',True,'PathRelativeTo:=','SourceProduct',
      'ApplyMeshOp:=',True,'AdaptPort:=',True]
    setup.EditSetup('Banda',['NAME:Banda','SolveType:=','Single','Frequency:=','5.17GHz',
      'MaxDeltaS:=',.02,'MaximumPasses:=',6,'MinimumPasses:=',2,'MinimumConvergedPasses:=',2,
      'PercentRefinement:=',2,'BasisOrder:=',0,'DrivenSolverType:=','Iterative Solver',
      'IterativeResidual:=',.00001,'DoLambdaRefine:=',False,'SaveAnyFields:=',True,
      'SaveRadFieldsOnly:=',True,'UseCacheFor:=',['Pass'],mesh,cache])
    sol.EditSources([['IncludePortPostProcessing:=',False,'SpecifySystemPower:=',False]]+
      [['Name:=',port+':1','Magnitude:=','0.05W','Phase:=','0deg'] for port in sol.GetAllSources()])
    assert d.ValidateDesign()==1
    p.Save();oDesktop.CloseProject(p.GetName())
    raw=open(native,'rb').read()
    assert 'MaximumPasses=6' in raw and 'MaxDeltaS=0.02' in raw and 'MinimumPasses=2' in raw
    assert 'ImportMesh=true' in raw and 'ForceSourceToSolve=false' in raw
    assert raw.count('MaxConvergenceDelta=0.02')==9 and 'SaveRadFieldsOnly=true' in raw
    assert hashlib.sha256(open(source,'rb').read()).hexdigest()==source_hash
    with open(os.path.join(folder,'configuracao_hfss.json'),'w') as f:json.dump(dict(
      fonte=source,sha256_fonte=source_hash,maximum_passes=6,minimum_passes=2,minimum_converged_passes=2,
      max_delta_s=.02,field_delta_dB=.02,percent_refinement=2,source_resolve=False,
      save_rad_fields_only=True,frequencia_adaptativa_GHz=5.17,
      frequencias_MHz=list(range(5090,5251,10)),estado='preparado_sem_solve'),f,indent=2)
    log('PREPARADO_R07_OK')
except:log(traceback.format_exc())
