# -*- coding: utf-8 -*-
"""TAU Flex com preservacao estrita das interfaces criticas; nenhuma analise RF."""
import os,json,time,datetime,traceback,hashlib
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P2S13_ROOT'];cfg=json.load(open(os.path.join(root,'configuracao.json')));native=os.path.join(root,cfg['native'])
def write(n,x):
    with open(os.path.join(root,n),'w') as f:json.dump(x,f,indent=2)
def block(raw,key):return raw.split("$begin '"+key+"'",1)[1].split("$end '"+key+"'",1)[0]
try:
    original=open(native).read();assert 'Prioridade_Interfaces' not in original
    assert "MeshMethod='AnsoftTAU'" in original and 'UseFlexMeshingForTAUvolumeMesh=true' in original
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign(cfg['design']);m=d.GetModule('MeshSetup')
    e=d.SetActiveEditor('3D Modeler')
    faces=sorted(set(int(f) for n in cfg['prioridade_superficies'] for f in e.GetFaceIDs(n)))
    m.AssignSurfPriorityForTauOp(['NAME:Prioridade_Interfaces','Type:=','SurfaceRepPriority',
      'Faces:=',faces,'SurfaceRepPriority:=',1])
    ops=list(d.GetChildObject('Mesh').GetChildNames())
    write('operacoes_prioridade.json',dict(operacoes=ops,mensagens=list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)),caminho=p.GetPath()))
    assert 'Prioridade_Interfaces' in ops,ops
    if cfg.get('salvar_prioridade_em_novo_nativo'):
        native=os.path.join(root,cfg['salvar_prioridade_em_novo_nativo'])
        assert not os.path.exists(native),native
    result=p.SaveAs(native,True)
    write('salvamento_prioridade.json',dict(retorno=str(result),faces=len(faces),mensagens=list(oDesktop.GetMessages(p.GetName(),d.GetName(),0))))
    oDesktop.CloseProject(p.GetName());updated=open(native).read();checks={}
    for key in ['Materials','GeometryCore','Boundaries','AnalysisSetup','MeshSettings']:
        a,b=block(original,key),block(updated,key);checks[key]=dict(identico=a==b,sha_antes=hashlib.sha256(a.encode('utf-8')).hexdigest(),sha_depois=hashlib.sha256(b.encode('utf-8')).hexdigest());assert a==b,key
    assert 'SurfaceRepPriority=1' in block(updated,'Prioridade_Interfaces')
    if cfg.get('salvar_prioridade_em_novo_nativo'):
        cfg['native']=os.path.basename(native)
        write('configuracao.json',cfg)
    checks['prioridade']=dict(objetos=cfg['prioridade_superficies'],nivel=1,refinamento_Length=False)
    write('mudanca_setup.json',checks)
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign(cfg['design']);valid=d.ValidateDesign();errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2))
    write('hfss_validacao.json',dict(validacao=valid,erros=errors,portas=len(d.GetModule('Solutions').GetAllSources()),max_passes=6,max_delta_s=.05,simulado=False))
    assert valid==1 and not errors
    oDesktop.SetRegistryFromFile(os.path.join(root,'HFSS_14nucleos.acf'));oDesktop.SetRegistryString('Desktop/ActiveDSOConfigurations/HFSS','P2M21_14nucleos')
    start=time.time();write('qualificacao.json',dict(estado='GERANDO_MALHA_PRIORIDADE',inicio=datetime.datetime.now().isoformat(),aedt_pid=oDesktop.GetProcessID(),solve_RF=False))
    rc=d.GenerateMesh('Centro');elapsed=time.time()-start
    write('geracao_malha.json',dict(retorno=rc,tempo_s=elapsed,solve_RF=False,fim=datetime.datetime.now().isoformat()))
    write('mensagens_malha.json',list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)))
    assert rc==0 and not list(oDesktop.GetMessages(p.GetName(),d.GetName(),2))
    p.SaveAs(native,True);oDesktop.CloseProject(p.GetName());write('qualificacao.json',dict(estado='MALHA_GERADA_AGUARDA_AUDITORIA',tempo_s=elapsed,solve_RF=False))
except:
    try:write('mensagens_falha.json',list(oDesktop.GetMessages('','',0)))
    except:pass
    write('falha_malha.json',dict(erro=traceback.format_exc(),solve_RF=False));raise
