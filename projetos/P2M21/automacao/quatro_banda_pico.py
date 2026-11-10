# -*- coding: utf-8 -*-
"""Confere o pior ponto Fast por uma solucao Discrete, sem adaptar a malha."""
import os,json,traceback,datetime,hashlib
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P2M21_BANDA'];p=None
assert os.path.normpath(root).lower().startswith(os.path.normpath('D:/dev/EMBRAER/P2M21/R13_Casamento_Banda').lower()+os.sep)

def write(name,data):
    with open(os.path.join(root,name),'w') as stream:json.dump(data,stream,indent=2)

try:
    with open(os.path.join(root,'banda_auditada.json')) as stream:band=json.load(stream)
    with open(os.path.join(root,'pico_planejado.json')) as stream:plan=json.load(stream)
    with open(os.path.join(root,'banda_fast.s2p'),'rb') as stream:assert hashlib.sha256(stream.read()).hexdigest()==plan['sha256_banda_fast']
    assert band['banda_completa'] and band['sem_adaptacao_adicional']
    freq=plan['frequencia_GHz'];assert 5.09<freq<5.25 and abs(freq-5.17)>1e-7
    worst=max(band['extremos'][:2],key=lambda item:item['maximo'])
    assert abs(freq-worst['frequencia_max_GHz'])<1e-9
    assert not os.path.exists(os.path.join(root,'pico_fast.s2p'))
    p=oDesktop.OpenProject(os.path.join(root,'P2M21_4_elementos.aedt'))
    d=p.SetActiveDesign('Quatro_elementos');an=d.GetModule('AnalysisSetup');sol=d.GetModule('Solutions')
    assert set(an.GetSweeps('Centro'))==set(['Triagem3','Banda_Fast'])
    d.ExportConvergence('Centro','',os.path.join(root,'antes_pico_convergencia.txt'))
    f='%.9fGHz'%freq
    an.InsertFrequencySweep('Centro',['NAME:Pico_Fast','IsEnabled:=',True,'RangeType:=','SinglePoints','RangeStart:=',f,'RangeEnd:=',f,'Type:=','Discrete','SaveFields:=',False,'SaveRadFields:=',False,'SaveSingleField:=',False,'ExtrapToDC:=',False])
    sol.EditSources([['IncludePortPostProcessing:=',False,'SpecifySystemPower:=',False]]+[['Name:=',name+':1','Magnitude:=','0.5W','Phase:=','0deg'] for name in ['A','B']])
    oDesktop.SetRegistryFromFile(os.path.join(root,'HFSS_14nucleos.acf'))
    oDesktop.SetRegistryString('Desktop/ActiveDSOConfigurations/HFSS','P2M21_14nucleos')
    assert oDesktop.GetRegistryString('Desktop/ActiveDSOConfigurations/HFSS')=='P2M21_14nucleos'
    assert d.ValidateDesign()==1
    p.Save();write('pico_estado.json',dict(estado='DISCRETE_PICO_INICIADO',inicio=datetime.datetime.now().isoformat(),frequencia_GHz=freq,nucleos=14))
    d.Analyze('Centro')
    messages=list(oDesktop.GetMessages(p.GetName(),d.GetName(),0));write('mensagens_pico.json',messages)
    errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2));assert not errors,errors
    sol.ExportNetworkData('',['Centro : Pico_Fast'],3,os.path.join(root,'pico_fast.s2p'),['All'],True,50,'S',-1,1,15,False,True,False)
    d.ExportConvergence('Centro','',os.path.join(root,'apos_pico_convergencia.txt'))
    p.Save();oDesktop.CloseProject(p.GetName());p=None
    write('pico_estado.json',dict(estado='PICO_EXPORTADO_AGUARDA_AUDITORIA',fim=datetime.datetime.now().isoformat()))
except:
    write('falha_pico.json',dict(erro=traceback.format_exc()));raise
finally:
    if p is not None:
        try:p.Save();oDesktop.CloseProject(p.GetName())
        except:pass
