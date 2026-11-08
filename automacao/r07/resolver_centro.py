# -*- coding: utf-8 -*-
"""Novo adaptativo R07: no maximo seis passes, DeltaS0.02, fonteR06 intacta."""
import os,json,hashlib,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P1H_R07'];folder=os.path.join(root,'antena')
def log(s):
    with open(os.path.join(folder,'centro.log'),'a') as f:f.write(str(s)+'\n')
try:
    config=json.load(open(os.path.join(folder,'configuracao_hfss.json')))
    native=os.path.join(folder,'PCB_R07.aedt');raw=open(native,'rb').read()
    assert 'MaximumPasses=6' in raw and 'MaxDeltaS=0.02' in raw
    assert 'ForceSourceToSolve=false' in raw
    assert hashlib.sha256(open(config['fonte'],'rb').read()).hexdigest()==config['sha256_fonte']
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign('PCB_sem_cabos')
    assert d.ValidateDesign()==1
    log('CENTRO_R07_INICIADO');d.Analyze('Banda')
    errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2));log(errors)
    with open(os.path.join(folder,'mensagens_centro.json'),'w') as f:
        json.dump(list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)),f,indent=2)
    d.ExportConvergence('Banda','',os.path.join(folder,'convergencia.txt'))
    p.Save();oDesktop.CloseProject(p.GetName())
    assert not errors,'Erros nativos durante o adaptativo'
    assert hashlib.sha256(open(config['fonte'],'rb').read()).hexdigest()==config['sha256_fonte']
    log('CENTRO_R07_RESOLVIDO_AUDITAR')
except:log(traceback.format_exc())
