# -*- coding: utf-8 -*-
"""GenerateMesh isolado para auditar representacao antes dos passes RF."""
import os,json,time,datetime,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P2S13_ROOT'];cfg=json.load(open(os.path.join(root,'configuracao.json')))
def write(n,x):
    with open(os.path.join(root,n),'w') as f:json.dump(x,f,indent=2)
try:
    assert not os.path.exists(os.path.join(root,'convergencia.txt'))
    p=oDesktop.OpenProject(os.path.join(root,cfg['native']));d=p.SetActiveDesign(cfg['design'])
    oDesktop.SetRegistryFromFile(os.path.join(root,'HFSS_14nucleos.acf'))
    oDesktop.SetRegistryString('Desktop/ActiveDSOConfigurations/HFSS','P2M21_14nucleos')
    valid=d.ValidateDesign();assert valid==1 and not list(oDesktop.GetMessages(p.GetName(),d.GetName(),2))
    start=time.time();write('qualificacao.json',dict(estado='GERANDO_MALHA_INICIAL',inicio=datetime.datetime.now().isoformat(),aedt_pid=oDesktop.GetProcessID(),solve_RF=False))
    rc=d.GenerateMesh('Centro');elapsed=time.time()-start
    write('geracao_malha.json',dict(retorno=rc,tempo_s=elapsed,solve_RF=False,fim=datetime.datetime.now().isoformat()))
    write('mensagens_malha.json',list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)))
    assert rc==0 and not list(oDesktop.GetMessages(p.GetName(),d.GetName(),2))
    p.Save();oDesktop.CloseProject(p.GetName());write('qualificacao.json',dict(estado='MALHA_GERADA_AGUARDA_AUDITORIA',tempo_s=elapsed,solve_RF=False))
except:
    try:write('mensagens_falha.json',list(oDesktop.GetMessages('','',0)))
    except:pass
    write('falha_malha.json',dict(erro=traceback.format_exc(),solve_RF=False));raise
