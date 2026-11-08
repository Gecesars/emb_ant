# -*- coding: utf-8 -*-
"""Resolver5170MHz na malha importada fixa antes da varredura; nenhum adaptativo."""
import os,json,hashlib,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P1H_R07'];folder=os.path.join(root,'antena');p=None
def log(s):
    with open(os.path.join(folder,'controle_fixo.log'),'a') as f:f.write(str(s)+'\n')
def read_bytes(path):
    with open(path,'rb') as f:return f.read()
try:
    config=json.load(open(os.path.join(folder,'configuracao_hfss.json')))
    assert config['modo']=='malha_fixa_validada_R06'
    assert json.load(open(os.path.join(folder,'fonte_malha.json')))['fonte_convergida']
    native=os.path.join(folder,config['native']);raw=read_bytes(native)
    assert 'MaximumPasses=0' in raw and 'ForceSourceToSolve=false' in raw
    assert hashlib.sha256(read_bytes(config['fonte'])).hexdigest()==config['sha256_fonte']
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign('PCB_sem_cabos')
    assert d.ValidateDesign()==1
    log('CONTROLE_FIXO_INICIADO');d.Analyze('Banda')
    errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2))
    with open(os.path.join(folder,'mensagens_controle_fixo.json'),'w') as f:
        json.dump(list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)),f,indent=2)
    assert not errors,str(errors)
    d.ExportProfile('Banda','',os.path.join(folder,'perfil_controle_fixo.txt'))
    p.Save();oDesktop.CloseProject(p.GetName());p=None
    assert hashlib.sha256(read_bytes(config['fonte'])).hexdigest()==config['sha256_fonte']
    log('CONTROLE_FIXO_RESOLVIDO')
except:
    log(traceback.format_exc())
    if p is not None:
        try:p.Save();oDesktop.CloseProject(p.GetName())
        except:log(traceback.format_exc())
