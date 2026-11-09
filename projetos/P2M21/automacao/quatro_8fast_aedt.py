# -*- coding: utf-8 -*-
"""Etapas nativas AEDT2024R2. Nunca cria geometria nem reinicia adaptacao."""
import os,json,traceback,datetime,re
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P2M21_8FAST'];folder=os.path.join(root,'antena');stage=os.environ['P2M21_8FAST_ETAPA'];p=None
def write(name,data):
    with open(os.path.join(root,name),'w') as f:json.dump(data,f,indent=2)
def log(s):
    with open(os.path.join(root,stage+'.log'),'a') as f:f.write(datetime.datetime.now().isoformat()+' '+str(s)+'\n')
def sources(sol,active=None):
    ports=list(sol.GetAllSources());assert sorted(ports)==['A','B'],ports
    sol.EditSources([['IncludePortPostProcessing:=',False,'SpecifySystemPower:=',False]]+[['Name:=',n+':1','Magnitude:=',('0.5W' if active is None else '1W' if n==active else '0W'),'Phase:=','0deg'] for n in ports])
def profile14():
    oDesktop.SetRegistryFromFile(os.path.join(folder,'HFSS_14nucleos.acf'))
    oDesktop.SetRegistryString('Desktop/ActiveDSOConfigurations/HFSS','P2M21_14nucleos')
    assert oDesktop.GetRegistryString('Desktop/ActiveDSOConfigurations/HFSS')=='P2M21_14nucleos'
try:
    p=oDesktop.OpenProject(os.path.join(folder,'P2M21_4_elementos.aedt'));d=p.SetActiveDesign('Quatro_elementos')
    an=d.GetModule('AnalysisSetup');sol=d.GetModule('Solutions')
    assert list(an.GetSetups())==['Centro']
    if stage=='preparar':
        assert not list(an.GetSweeps('Centro'))
        d.ExportConvergence('Centro','',os.path.join(root,'antes_convergencia.txt'))
        old=open(os.path.join(root,'antes_convergencia.txt')).read();assert int(re.search(r'Completed\s*:\s*(\d+)',old).group(1))==6
        # O AEDT242 pode aplicar Target=0.6667 por default em EditSetup parcial.
        # Informar o valor original. A auditoria externa verifica a normalizacao
        # inativa para 0.6667 e a preservacao da malha antes de autorizar o solve.
        an.EditSetup('Centro',['NAME:Centro','MaximumPasses:=',8,'MinimumPasses:=',8,'Target:=',0.3333])
        sources(sol);p.Save();oDesktop.CloseProject(p.GetName());p=None
        log('MIN8_MAX8_CONFIGURADOS_SEM_RESET')
    elif stage=='centro':
        assert json.load(open(os.path.join(root,'preparacao_auditada.json')))['aprovado']
        assert not os.path.exists(os.path.join(folder,'convergencia.txt'))
        assert not list(an.GetSweeps('Centro'))
        profile14();sources(sol);assert d.ValidateDesign()==1
        write('qualificacao.json',dict(estado='CALCULANDO_PASSES_7_E_8',nucleos=14,max_passes_total=8))
        log('RETOMADA_APENAS_PASSES7_E8');d.Analyze('Centro')
        errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2))
        write('mensagens_centro.json',list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)));assert not errors,errors
        d.ExportConvergence('Centro','',os.path.join(folder,'convergencia.txt'))
        sol.ExportNetworkData('',['Centro : LastAdaptive'],3,os.path.join(folder,'centro.s2p'),['All'],True,50,'S',-1,1,15,False,True,False)
        reports=d.GetModule('ReportSetup')
        for mode,active in [('AB',None),('A','A'),('B','B')]:
            sources(sol,active)
            for axis,phi in [('H',90),('V',0)]:
                name=mode+'_'+axis
                if name in list(reports.GetAllReportNames()):reports.DeleteReports([name])
                reports.CreateReport(name,'Far Fields','Rectangular Plot','Centro : LastAdaptive',['Context:=','HV'],['Theta:=',['All'],'Phi:=',[str(phi)+'deg'],'Freq:=',['5170MHz']],['X Component:=','Theta','Y Component:=',['dB(RealizedGainTotal)','dB(GainTotal)','dB(DirTotal)','re(rETheta)','im(rETheta)','re(rEPhi)','im(rEPhi)']])
                reports.ExportToFile(name,os.path.join(folder,name+'.csv'),False)
        sources(sol);p.Save();oDesktop.CloseProject(p.GetName());p=None
        write('antena/qualificacao.json',dict(estado='CENTRO8_EXPORTADO_AGUARDA_AUDITORIA'))
        log('CENTRO8_EXPORTADO')
    elif stage=='fast':
        assert json.load(open(os.path.join(root,'continuidade_auditada.json')))['aprovado']
        assert not os.path.exists(os.path.join(folder,'banda_fast.s2p'))
        sweep='Banda_Fast';assert not list(an.GetSweeps('Centro'))
        an.InsertFrequencySweep('Centro',['NAME:'+sweep,'IsEnabled:=',True,'RangeType:=','LinearStep','RangeStart:=','5090MHz','RangeEnd:=','5250MHz','RangeStep:=','1MHz','Type:=','Fast','SaveFields:=',False,'SaveRadFields:=',False,'GenerateFieldsForAllFreqs:=',False])
        assert list(an.GetSweeps('Centro'))==[sweep]
        profile14();sources(sol);assert d.ValidateDesign()==1
        p.Save();oDesktop.CloseProject(p.GetName());p=None
        raw=open(os.path.join(folder,'P2M21_4_elementos.aedt')).read()
        sw=raw.split("$begin '"+sweep+"'",1)[1].split("$end '"+sweep+"'",1)[0]
        assert "Type='Fast'" in sw and 'SaveFields=false' in sw and 'SaveRadFields=false' in sw
        write('sweep_configurado.json',dict(nome=sweep,tipo='Fast',inicio_GHz=5.09,fim_GHz=5.25,passo_MHz=1,campos=False))
        p=oDesktop.OpenProject(os.path.join(folder,'P2M21_4_elementos.aedt'));d=p.SetActiveDesign('Quatro_elementos');sol=d.GetModule('Solutions')
        profile14();sources(sol);log('FAST_INICIADO');d.Analyze('Centro')
        write('mensagens_fast.json',list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)))
        errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2));assert not errors,errors
        sol.ExportNetworkData('',['Centro : '+sweep],3,os.path.join(folder,'banda_fast.s2p'),['All'],True,50,'S',-1,1,15,False,True,False)
        d.ExportConvergence('Centro','',os.path.join(root,'apos_fast_convergencia.txt'))
        p.Save();oDesktop.CloseProject(p.GetName());p=None;log('FAST_EXPORTADO')
    else:raise ValueError(stage)
except:
    log(traceback.format_exc());write('falha_'+stage+'.json',dict(erro=traceback.format_exc()))
    raise
finally:
    if p is not None:
        try:p.Save();oDesktop.CloseProject(p.GetName())
        except:log(traceback.format_exc())
