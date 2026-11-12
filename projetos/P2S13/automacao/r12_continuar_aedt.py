# -*- coding: utf-8 -*-
"""Retoma somente passes7/8 em copia da solucao; preserva malha/cache e fontes."""
import os,json,re,traceback,datetime
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P2S13_ROOT'];stage=os.environ['P2S13_ETAPA'];cfg=json.load(open(os.path.join(root,'configuracao.json')));p=None
def write(n,v):
    with open(os.path.join(root,n),'w') as f:json.dump(v,f,indent=2)
def log(s):
    with open(os.path.join(root,stage+'.log'),'a') as f:f.write(datetime.datetime.now().isoformat()+' '+s+'\n')
def sources(sol,selected):
    ports=list(sol.GetAllSources());assert set(ports)==set(q['name'] for q in cfg['portas'])
    power='%.12gW'%(1./len(selected))
    sol.EditSources([['IncludePortPostProcessing:=',False,'SpecifySystemPower:=',False]]+[['Name:=',n+':1','Magnitude:=',power if n in selected else '0W','Phase:=','0deg'] for n in ports])
try:
    p=oDesktop.OpenProject(os.path.join(root,cfg['native']));d=p.SetActiveDesign(cfg['design'])
    an=d.GetModule('AnalysisSetup');sol=d.GetModule('Solutions');ports=list(sol.GetAllSources())
    assert list(an.GetSetups())==['Centro'] and not list(an.GetSweeps('Centro')) and len(ports)==len(cfg['portas']) and len(ports)==2
    if stage=='preparar':
        assert not os.path.exists(os.path.join(root,'preparacao_auditada.json'))
        d.ExportConvergence('Centro','',os.path.join(root,'antes_convergencia.txt'))
        with open(os.path.join(root,'antes_convergencia.txt')) as f:conv=f.read()
        assert int(re.search(r'Completed\s*:\s*(\d+)',conv).group(1))==6
        # Target mantido explicitamente no valor original; evita serializacao
        # diferente da propriedade inativa quando SetLambdaTarget=false.
        an.EditSetup('Centro',['NAME:Centro','MaximumPasses:=',8,'MinimumPasses:=',8,'Target:=',0.3333])
        sources(sol,ports);p.Save();oDesktop.CloseProject(p.GetName());p=None
        log('MIN8_MAX8_CONFIGURADOS_SEM_RESET')
    elif stage=='centro':
        assert json.load(open(os.path.join(root,'preparacao_auditada.json')))['aprovado']
        assert not os.path.exists(os.path.join(root,'convergencia.txt'))
        oDesktop.SetRegistryFromFile(os.path.join(root,'HFSS_14nucleos.acf'))
        oDesktop.SetRegistryString('Desktop/ActiveDSOConfigurations/HFSS','P2M21_14nucleos')
        assert oDesktop.GetRegistryString('Desktop/ActiveDSOConfigurations/HFSS')=='P2M21_14nucleos'
        sources(sol,ports);assert d.ValidateDesign()==1
        write('qualificacao.json',dict(estado='CALCULANDO_PASSES_7_E_8',nucleos=14,max_passes_total=8,sem_sweep=True))
        write('ordem_fontes.json',ports);log('RETOMADA_PASSES7_E8');d.Analyze('Centro')
        write('mensagens.json',list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)))
        errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2));assert not errors,errors
        d.ExportConvergence('Centro','',os.path.join(root,'convergencia.txt'))
        sol.ExportNetworkData('',['Centro : LastAdaptive'],3,os.path.join(root,'centro.s%dp'%len(ports)),['All'],True,50,'S',-1,1,15,False,True,False)
        reports=d.GetModule('ReportSetup')
        cases=[('ALL',ports),('POL_A',[n for n in ports if n.endswith('_A')]),('POL_B',[n for n in ports if n.endswith('_B')])]+[(n,[n]) for n in ports]
        for mode,selected in cases:
            sources(sol,selected)
            for axis,phi in [('H',90),('V',0)]:
                name=mode+'_'+axis
                if name in list(reports.GetAllReportNames()):reports.DeleteReports([name])
                reports.CreateReport(name,'Far Fields','Rectangular Plot','Centro : LastAdaptive',['Context:=','HV'],['Theta:=',['All'],'Phi:=',[str(phi)+'deg'],'Freq:=',['5170MHz']],['X Component:=','Theta','Y Component:=',['dB(RealizedGainTotal)','dB(GainTotal)','dB(DirTotal)','re(rETheta)','im(rETheta)','re(rEPhi)','im(rEPhi)']])
                reports.ExportToFile(name,os.path.join(root,name+'.csv'),False)
            log('CAMPOS_EXPORTADOS '+mode)
        sources(sol,ports)
        if 'ALL_V_fino' in list(reports.GetAllReportNames()):reports.DeleteReports(['ALL_V_fino'])
        reports.CreateReport('ALL_V_fino','Far Fields','Rectangular Plot','Centro : LastAdaptive',['Context:=','V_fino'],
          ['Theta:=',['All'],'Phi:=',['0deg'],'Freq:=',['5170MHz']],
          ['X Component:=','Theta','Y Component:=',['dB(RealizedGainTotal)','re(rETheta)','im(rETheta)','re(rEPhi)','im(rEPhi)']])
        reports.ExportToFile('ALL_V_fino',os.path.join(root,'ALL_V_fino.csv'),False)
        try:
            expressions=['RadiatedPower','AcceptedPower','IncidentPower','RadiationEfficiency','SystemEfficiency']
            data=reports.GetSolutionDataPerVariation('Antenna Parameters','Centro : LastAdaptive',['Context:=','Potencia'],['Freq:=',['All']],expressions)
            write('potencia.json',dict((q,dict(real=list(data[0].GetRealDataValues(q)),units=data[0].GetDataUnits(q))) for q in expressions))
        except:
            write('potencia_erro.json',dict(erro=traceback.format_exc()))
        sources(sol,ports);p.Save();oDesktop.CloseProject(p.GetName());p=None
        write('qualificacao.json',dict(estado='SOLVE_EXPORTADO_AGUARDA_AUDITORIA',gui=False));log('PASSES7_E8_EXPORTADOS')
    else:raise ValueError(stage)
except:
    log(traceback.format_exc());write('falha_'+stage+'.json',dict(erro=traceback.format_exc()));raise
finally:
    if p is not None:
        try:p.Save();oDesktop.CloseProject(p.GetName())
        except:log(traceback.format_exc())
