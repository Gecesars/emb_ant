# -*- coding: utf-8 -*-
"""Corrigir discretizacao local em copia sem resultados, sem alterar o CAD."""
import os,json,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P2M21_UNIFORME'];folder=os.path.join(root,'antena');p=None
def log(s):
    with open(os.path.join(folder,'preparacao.log'),'a') as f:f.write(str(s)+'\n')
try:
    cfg=json.load(open(os.path.join(root,'configuracao.json')))
    p=oDesktop.OpenProject(os.path.join(folder,cfg['native']))
    d=p.SetActiveDesign('PCB_separada');e=d.SetActiveEditor('3D Modeler')
    objects=list(e.GetObjectsInGroup('Solids'))
    cu0=[n for n in objects if n.endswith('_Cu0')]
    cu1=[n for n in objects if n.endswith('_Cu1')]
    solders=[n for n in objects if 'Solda_terminal_' in n]
    assert len(cu0)==64 and len(cu1)==64 and len(solders)==128
    mesh=d.GetModule('MeshSetup')
    mesh.AssignTrueSurfOp(['NAME:Cobre_solda_superficie_R02','Objects:=',cu0+cu1+solders,
      'CurvedSurfaceApproxChoice:=','ManualSettings','SurfDevChoice:=',2,'SurfDev:=','0.0005mm',
      'NormalDevChoice:=',2,'NormalDev:=','5deg','AspectRatioChoice:=',1,'AspectRatio:=','10'])
    # Cu1 ja tem Length=0.06mm no R00; acrescentar o mesmo limite aos Cu0 afetados.
    mesh.AssignLengthOp(['NAME:Cu0_60um_R02','RefineInside:=',False,'Enabled:=',True,'Objects:=',cu0,
      'RestrictElem:=',False,'NumMaxElem:=','1000','RestrictLength:=',True,'MaxLength:=','0.06mm'])
    sol=d.GetModule('Solutions');ports=list(sol.GetAllSources());assert len(ports)==64
    sol.EditSources([['IncludePortPostProcessing:=',False,'SpecifySystemPower:=',False]]+
      [['Name:=',s+':1','Magnitude:=','0.015625W','Phase:=','0deg'] for s in ports])
    # Cache somente de monitoramento: nao acrescenta criterio de convergencia ao Delta S pedido.
    cache=['NAME:ExpressionCache']
    angles=[(0,90),(-18,90),(18,90),(-20,90),(20,90),(-22,90),(22,90),(-1.75,0),(1.75,0)]
    for i,(theta,phi) in enumerate(angles):
        cache.append(['NAME:CacheItem','Title:=','U_R02_%02d'%i,'Expression:=','dB(RealizedGainTotal)',
          'Intrinsics:=',"Phi='%sdeg' Theta='%sdeg'"%(phi,theta),'IsConvergence:=',False,
          'UseRelativeConvergence:=',0,'MaxConvergenceDelta:=',.1,'MaxConvergeValue:=','0.1',
          'ReportType:=','Far Fields',['NAME:ExpressionContext','Context:=','HV']])
    setup=d.GetModule('AnalysisSetup')
    setup.EditSetup('Centro',['NAME:Centro','MaxDeltaS:=',.04,'MaximumPasses:=',6,
      'MinimumPasses:=',2,'MinimumConvergedPasses:=',2,'SaveAnyFields:=',True,
      'SaveRadFieldsOnly:=',True,'UseCacheFor:=',['Pass'],cache])
    setup.EditFrequencySweep('Centro','Banda17',['NAME:Banda17','IsEnabled:=',False,
      'RangeType:=','LinearStep','RangeStart:=','5090MHz','RangeEnd:=','5250MHz','RangeStep:=','10MHz',
      'Type:=','Discrete','SaveFields:=',True,'SaveRadFields:=',True])
    valid=d.ValidateDesign();errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2))
    info=dict(validacao=valid,erros=errors,portas=ports,potencia_por_porta_W=.015625,
      potencia_total_W=1.,fase_graus=0,cu0=cu0,cu1=cu1,soldas=solders,
      desvio_superficie_mm=.0005,desvio_normal_graus=5,comprimento_local_mm=.06,
      max_passes=6,max_delta_s=.04,cache_somente_monitoramento=angles)
    with open(os.path.join(folder,'preparacao.json'),'w') as f:json.dump(info,f,indent=2)
    assert valid==1 and not errors,info
    p.Save();oDesktop.CloseProject(p.GetName());p=None
    log('PREPARACAO_UNIFORME_OK')
except:log(traceback.format_exc())
finally:
    if p is not None:
        p.Save();oDesktop.CloseProject(p.GetName())
