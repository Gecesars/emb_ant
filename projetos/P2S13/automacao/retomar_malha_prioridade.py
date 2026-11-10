# -*- coding: utf-8 -*-
"""Retoma somente GenerateMesh de nativo cuja prioridade ja foi persistida."""
import os,json,time,datetime,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P2S13_ROOT'];cfg=json.load(open(os.path.join(root,'configuracao.json')));native=os.path.join(root,cfg['native'])
def write(n,x):
    with open(os.path.join(root,n),'w') as f:json.dump(x,f,indent=2)
try:
    checks=json.load(open(os.path.join(root,'mudanca_setup.json')))
    assert all(checks[k]['identico_fisicamente'] for k in ['Materials','GeometryCore','Boundaries','AnalysisSetup','MeshSettings'])
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign(cfg['design']);e=d.SetActiveEditor('3D Modeler')
    assert 'Prioridade_Interfaces' in list(d.GetChildObject('Mesh').GetChildNames())
    faces=sorted(set(int(f) for n in cfg['prioridade_superficies'] for f in e.GetFaceIDs(n)))
    assigned=sorted(int(f) for f in d.GetModule('MeshSetup').GetMeshOpAssignment('Prioridade_Interfaces'))
    assert assigned==faces,(len(assigned),len(faces))
    valid=d.ValidateDesign();errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2))
    write('hfss_validacao.json',dict(validacao=valid,erros=errors,portas=len(d.GetModule('Solutions').GetAllSources()),max_passes=6,max_delta_s=.05,simulado=False,faces_preservadas=len(faces)))
    assert valid==1 and not errors and not list(d.GetModule('AnalysisSetup').GetSweeps('Centro'))
    oDesktop.SetRegistryFromFile(os.path.join(root,'HFSS_14nucleos.acf'));oDesktop.SetRegistryString('Desktop/ActiveDSOConfigurations/HFSS','P2M21_14nucleos')
    start=time.time();write('qualificacao.json',dict(estado='GERANDO_MALHA_RF_PRESERVADA',inicio=datetime.datetime.now().isoformat(),aedt_pid=oDesktop.GetProcessID(),solve_RF=False))
    rc=d.GenerateMesh('Centro');elapsed=time.time()-start
    write('geracao_malha.json',dict(retorno=rc,tempo_s=elapsed,solve_RF=False,fim=datetime.datetime.now().isoformat()))
    write('mensagens_malha.json',list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)))
    assert rc==0 and not list(oDesktop.GetMessages(p.GetName(),d.GetName(),2))
    p.Save();oDesktop.CloseProject(p.GetName());write('qualificacao.json',dict(estado='MALHA_GERADA_AGUARDA_AUDITORIA',tempo_s=elapsed,solve_RF=False))
except:
    try:write('mensagens_falha.json',list(oDesktop.GetMessages('','',0)))
    except:pass
    write('falha_malha.json',dict(erro=traceback.format_exc(),solve_RF=False));raise
