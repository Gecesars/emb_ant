# -*- coding: utf-8 -*-
"""Fast ou triagem discreta3 apos centro exportado; sem novo ciclo adaptativo."""
import os,json,re,traceback,datetime
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P2M21_BANDA'];p=None
kind=os.environ.get('P2M21_BANDA_TIPO','Fast');assert kind in ['Fast','Discrete']
diagnostic=os.environ.get('P2M21_BANDA_DIAGNOSTICO','0')=='1'
calibration=os.environ.get('P2M21_BANDA_CALIBRACAO_REJEITADA','0')=='1'
tag='fast' if kind=='Fast' else 'triagem3';name='Banda_Fast' if kind=='Fast' else 'Triagem3'
output='banda_fast.s2p' if kind=='Fast' else 'triagem3.s2p'
def write(name,data):
    with open(os.path.join(root,name),'w') as f:json.dump(data,f,indent=2)
try:
    gate=json.load(open(os.path.join(root,'diagrama_comparado.json')))
    if calibration:
        assert kind=='Discrete','Calibracao de candidato rejeitado limitada a tres frequencias reais'
        assert gate['verificacoes']['fisica'] and gate['verificacoes']['convergencia']
        failed=[k for k,v in gate['verificacoes'].items() if not v]
        assert failed,'Candidato aprovado deve usar fluxo normal'
        write('triagem_diagnostica.json',dict(tipo=kind,qualifica_geometria=False,finalidade='CALIBRACAO_DE_CANDIDATO_REJEITADO',motivo='Extrair tres S2 reais para corrigir o modelo de casamento. Todos os criterios de rejeicao dos diagramas continuam ativos; nao libera Fast nem aprova o candidato.',criterios_reprovados=failed))
    elif diagnostic:
        # Medicao de impedancia separada da aprovacao do apontamento.
        # Os limites de forma, ganho, SLL, fisica e convergencia permanecem exigidos.
        failed=[k for k,v in gate['verificacoes'].items() if not v]
        assert gate['verificacoes']['fisica'] and gate['verificacoes']['convergencia']
        assert failed and all(k.startswith('apontamento_') for k in failed),failed
        write('fast_diagnostico.json' if kind=='Fast' else 'triagem_diagnostica.json',dict(tipo=kind,qualifica_geometria=False,motivo='Medir casamento na faixa solicitada sem declarar os maximos em zero; reprovacao de apontamento continua registrada.',criterios_reprovados=failed))
    else:assert gate['permitir_fast']
    assert not os.path.exists(os.path.join(root,output))
    native=os.path.join(root,'P2M21_4_elementos.aedt')
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign('Quatro_elementos');an=d.GetModule('AnalysisSetup');sol=d.GetModule('Solutions')
    assert list(an.GetSweeps('Centro')) in ([[],['Triagem3']] if kind=='Fast' else [[]])
    d.ExportConvergence('Centro','',os.path.join(root,'antes_'+tag+'_convergencia.txt'))
    sweep=['NAME:'+name,'IsEnabled:=',True,'RangeType:=','LinearStep','RangeStart:=','5090MHz','RangeEnd:=','5250MHz','RangeStep:=',('1MHz' if kind=='Fast' else '80MHz'),'Type:=',kind,'SaveFields:=',False,'SaveRadFields:=',False,'ExtrapToDC:=',False]
    if kind=='Fast':sweep+=['GenerateFieldsForAllFreqs:=',False]
    an.InsertFrequencySweep('Centro',sweep)
    sol.EditSources([['IncludePortPostProcessing:=',False,'SpecifySystemPower:=',False]]+[['Name:=',n+':1','Magnitude:=','0.5W','Phase:=','0deg'] for n in ['A','B']])
    oDesktop.SetRegistryFromFile(os.path.join(root,'HFSS_14nucleos.acf'));oDesktop.SetRegistryString('Desktop/ActiveDSOConfigurations/HFSS','P2M21_14nucleos')
    assert oDesktop.GetRegistryString('Desktop/ActiveDSOConfigurations/HFSS')=='P2M21_14nucleos'
    assert d.ValidateDesign()==1
    write(tag+'_estado.json',dict(estado=kind+'_EM_EXECUCAO',inicio=datetime.datetime.now().isoformat(),nucleos=14,faixa_GHz=[5.09,5.25]))
    p.Save();d.Analyze('Centro')
    errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2));write('mensagens_'+tag+'.json',list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)));assert not errors,errors
    sol.ExportNetworkData('',['Centro : '+name],3,os.path.join(root,output),['All'],True,50,'S',-1,1,15,False,True,False)
    d.ExportConvergence('Centro','',os.path.join(root,'apos_'+tag+'_convergencia.txt'))
    p.Save();oDesktop.CloseProject(p.GetName());p=None
    write(tag+'_estado.json',dict(estado=kind+'_EXPORTADO_AGUARDA_AUDITORIA',fim=datetime.datetime.now().isoformat()))
except:
    write('falha_'+tag+'.json',dict(erro=traceback.format_exc()));raise
finally:
    if p is not None:
        try:p.Save();oDesktop.CloseProject(p.GetName())
        except:pass
