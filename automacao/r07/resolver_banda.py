# -*- coding: utf-8 -*-
"""Dezessete solucoes discretas com campos radiados, usando a malha adaptada."""
import os,json,traceback,hashlib
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P1H_R07'];folder=os.path.join(root,'antena');p=None
def log(s):
    with open(os.path.join(folder,'banda.log'),'a') as f:f.write(str(s)+'\n')
def read_bytes(path):
    with open(path,'rb') as f:return f.read()
try:
    config=json.load(open(os.path.join(folder,'configuracao_hfss.json')))
    if config.get('modo')=='malha_fixa_validada_R06':
        assert json.load(open(os.path.join(folder,'fonte_malha.json')))['fonte_convergida']
        assert 'MaximumPasses=0' in read_bytes(os.path.join(folder,config['native']))
    else:assert json.load(open(os.path.join(folder,'auditoria_convergencia.json')))['convergencia_aprovada']
    assert json.load(open(os.path.join(root,'comparacao_centro.json')))['estavel']
    assert hashlib.sha256(read_bytes(config['fonte'])).hexdigest()==config['sha256_fonte']
    p=oDesktop.OpenProject(os.path.join(folder,config.get('native','PCB_R07.aedt')));d=p.SetActiveDesign('PCB_sem_cabos')
    setup=d.GetModule('AnalysisSetup');sweep='Discreta_10MHz'
    if sweep not in setup.GetSweeps('Banda'):
        setup.InsertFrequencySweep('Banda',['NAME:'+sweep,'IsEnabled:=',True,
          'RangeType:=','LinearStep','RangeStart:=','5090MHz','RangeEnd:=','5250MHz',
          'RangeStep:=','10MHz','Type:=','Discrete','SaveFields:=',True,'SaveRadFields:=',True])
    p.Save();log('BANDA17_INICIADA');d.Analyze('Banda')
    errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2));log(errors)
    with open(os.path.join(folder,'mensagens_banda.json'),'w') as f:
        json.dump(list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)),f,indent=2)
    assert not errors,'Erros nativos durante a banda'
    d.GetModule('Solutions').ExportNetworkData('',['Banda : '+sweep],3,
      os.path.join(folder,'antena_banda.s20p'),['All'],True,50,'S',-1,1,15,False,True,False)
    p.Save();oDesktop.CloseProject(p.GetName());p=None
    assert hashlib.sha256(read_bytes(config['fonte'])).hexdigest()==config['sha256_fonte']
    log('BANDA17_RESOLVIDA_EXPORTAR_CAMPOS')
except:
    log(traceback.format_exc())
    if p is not None:
        try:p.Save();oDesktop.CloseProject(p.GetName())
        except:log(traceback.format_exc())
