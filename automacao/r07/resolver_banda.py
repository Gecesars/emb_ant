# -*- coding: utf-8 -*-
"""Dezessete solucoes discretas com campos radiados, usando a malha adaptada."""
import os,json,traceback,hashlib
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P1H_R07'];folder=os.path.join(root,'antena')
def log(s):
    with open(os.path.join(folder,'banda.log'),'a') as f:f.write(str(s)+'\n')
try:
    assert json.load(open(os.path.join(folder,'auditoria_convergencia.json')))['convergencia_aprovada']
    assert json.load(open(os.path.join(root,'comparacao_centro.json')))['estavel']
    config=json.load(open(os.path.join(folder,'configuracao_hfss.json')))
    assert hashlib.sha256(open(config['fonte'],'rb').read()).hexdigest()==config['sha256_fonte']
    p=oDesktop.OpenProject(os.path.join(folder,'PCB_R07.aedt'));d=p.SetActiveDesign('PCB_sem_cabos')
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
    p.Save();oDesktop.CloseProject(p.GetName())
    assert hashlib.sha256(open(config['fonte'],'rb').read()).hexdigest()==config['sha256_fonte']
    log('BANDA17_RESOLVIDA_EXPORTAR_CAMPOS')
except:log(traceback.format_exc())
