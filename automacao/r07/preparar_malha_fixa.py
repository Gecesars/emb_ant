# -*- coding: utf-8 -*-
"""Reutilizar a malha R06 convergida em sweeps discretos, sem novos adaptativos."""
import os,json,re,hashlib,traceback,shutil
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P1H_R07'];folder=os.path.join(root,'antena')
source=os.path.join(os.path.dirname(root),'R06_sem_cabos','antena','PCB_R06.aedt')
native=os.path.join(folder,'PCB_R07_SWEEP.aedt')
def log(s):
    with open(os.path.join(folder,'preparacao_fixa.log'),'a') as f:f.write(str(s)+'\n')
def section(raw,name):
    return re.search(r"\$begin '"+name+r"'[\s\S]*?\$end '"+name+r"'",raw).group(0)
def read_bytes(path):
    with open(path,'rb') as f:return f.read()
try:
    old=read_bytes(source);source_hash=hashlib.sha256(old).hexdigest()
    if os.path.exists(native):assert read_bytes(native)==old,'Preservar projeto ja preparado'
    else:shutil.copy2(source,native)
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign('PCB_sem_cabos')
    setup=d.GetModule('AnalysisSetup');setup.DeleteSetups(list(setup.GetSetups()))
    reports=d.GetModule('ReportSetup');names=list(reports.GetAllReportNames())
    if names:reports.DeleteReports(names)
    mesh=['NAME:MeshLink','ImportMesh:=',True,'Project:=',source,'Product:=','HFSS',
      'Design:=','PCB_sem_cabos','Soln:=','Banda : LastAdaptive',['NAME:Params'],
      'ForceSourceToSolve:=',False,'PreservePartnerSoln:=',True,'PathRelativeTo:=','SourceProduct',
      'ApplyMeshOp:=',True,'AdaptPort:=',True]
    setup.InsertSetup('HfssDriven',['NAME:Banda','Frequency:=','5.17GHz','MaxDeltaS:=',.02,
      'MaximumPasses:=',0,'MinimumPasses:=',1,'MinimumConvergedPasses:=',2,
      'BasisOrder:=',0,'DrivenSolverType:=','Iterative Solver','IterativeResidual:=',.00001,
      'DoLambdaRefine:=',False,'SaveAnyFields:=',True,'SaveRadFieldsOnly:=',True,mesh])
    setup.InsertFrequencySweep('Banda',['NAME:Controle5170','IsEnabled:=',True,
      'RangeType:=','SinglePoints','RangeStart:=','5170MHz','RangeEnd:=','5170MHz',
      'Type:=','Discrete','SaveSingleField:=',True,'SaveFields:=',True,'SaveRadFields:=',True])
    assert len(d.GetModule('Solutions').GetAllSources())==20
    assert d.ValidateDesign()==1
    p.SaveAs(native,True);oDesktop.CloseProject(p.GetName())
    new=read_bytes(native)
    assert 'MaximumPasses=0' in new and 'MaxDeltaS=0.02' in new
    assert 'ForceSourceToSolve=false' in new and 'ImportMesh=true' in new
    hashes={}
    for name in ['ModelSetup','BoundarySetup','MeshSetup','RadField']:
        assert section(old,name)==section(new,name),'Mudanca em '+name
        hashes[name]=hashlib.sha256(section(new,name)).hexdigest()
    assert hashlib.sha256(read_bytes(source)).hexdigest()==source_hash
    config=dict(modo='malha_fixa_validada_R06',native='PCB_R07_SWEEP.aedt',fonte=source,sha256_fonte=source_hash,
      secoes_fisicas_sha256=hashes,maximum_passes=0,limite_usuario_novos_adaptativos=6,max_delta_s=.02,
      criterio_s_fonte=.004,source_resolve=False,save_rad_fields_only=True,
      solucao_centro='Banda : Controle5170',frequencias_MHz=list(range(5090,5251,10)),
      estado='preparado_sem_solve',nota='Nenhuma nova adaptacao. Malha R06 ja convergida e preservada; comparar controle5170 antes da banda.')
    with open(os.path.join(folder,'configuracao_hfss.json'),'w') as f:json.dump(config,f,indent=2)
    log('MALHA_FIXA_PREPARADA')
except:log(traceback.format_exc())
