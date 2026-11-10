# -*- coding: utf-8 -*-
"""AEDT2024R2 headless: R14, 16 portas coerentes e 32 campos embutidos H/V."""
import os,json,traceback,datetime
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ.get('P2M21_OITO_ROOT','D:/dev/EMBRAER/P2M21/R14_Oito_Celulas')
cfg=json.load(open(os.path.join(root,'configuracao.json')))
native=os.path.join(root,cfg['native'])
def write(n,v):
    with open(os.path.join(root,n),'w') as f:json.dump(v,f,indent=2)
def log(s):
    with open(os.path.join(root,'centro.log'),'a') as f:f.write(datetime.datetime.now().isoformat()+' '+s+'\n')
def sources(sol,selected):
    ports=list(sol.GetAllSources());assert set(ports)==set(p['name'] for p in cfg['portas'])
    assert selected and set(selected).issubset(set(ports))
    power='%.12gW'%(1./len(selected))
    sol.EditSources([['IncludePortPostProcessing:=',False,'SpecifySystemPower:=',False]]+
     [['Name:=',name+':1','Magnitude:=',power if name in selected else '0W','Phase:=','0deg'] for name in ports])
try:
    assert not os.path.exists(os.path.join(root,'convergencia.txt')),'Resultado existente'
    raw=open(native).read();analysis=raw.split("$begin 'AnalysisSetup'",1)[1].split("$end 'AnalysisSetup'",1)[0]
    for expr in ['MaximumPasses=6','MaxDeltaS=0.05','MinimumPasses=2','DoLambdaRefine=false','MinimumConvergedPasses=2','5.17GHz','BasisOrder=1']:
        assert expr in analysis,expr
    assert 'AnsoftClassic' in raw
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign(cfg['design'])
    assert not list(d.GetModule('AnalysisSetup').GetSweeps('Centro'))
    oDesktop.SetRegistryFromFile(os.path.join(root,'HFSS_14nucleos.acf'))
    oDesktop.SetRegistryString('Desktop/ActiveDSOConfigurations/HFSS','P2M21_14nucleos')
    assert oDesktop.GetRegistryString('Desktop/ActiveDSOConfigurations/HFSS')=='P2M21_14nucleos'
    sol=d.GetModule('Solutions');ports=list(sol.GetAllSources());assert len(ports)==len(cfg['portas'])
    sources(sol,ports);p.Save()
    valid=d.ValidateDesign();errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2));assert valid==1 and not errors,(valid,errors)
    write('qualificacao.json',dict(estado='EM_CALCULO_HEADLESS',inicio=datetime.datetime.now().isoformat(),max_passes=6,delta_s=.05,nucleos=14))
    write('ordem_fontes.json',ports)
    log('SOLVE_INICIADO '+cfg['revisao']+' 5170MHz_14NUCLEOS_MAX6')
    d.Analyze('Centro')
    d.ExportConvergence('Centro','',os.path.join(root,'convergencia.txt'))
    write('mensagens.json',list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)))
    errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2));assert not errors,errors
    sol.ExportNetworkData('',['Centro : LastAdaptive'],3,os.path.join(root,'centro.s%dp'%len(ports)),['All'],True,50,'S',-1,1,15,False,True,False)
    reports=d.GetModule('ReportSetup')
    cases=[('ALL',ports),('POL_A',[n for n in ports if n.endswith('_A')]),('POL_B',[n for n in ports if n.endswith('_B')])]
    cases.extend((n,[n]) for n in ports)
    for mode,selected in cases:
        sources(sol,selected)
        for axis,phi in [('H',90),('V',0)]:
            name=mode+'_'+axis
            reports.CreateReport(name,'Far Fields','Rectangular Plot','Centro : LastAdaptive',['Context:=','HV'],
              ['Theta:=',['All'],'Phi:=',[str(phi)+'deg'],'Freq:=',['5170MHz']],
              ['X Component:=','Theta','Y Component:=',['dB(RealizedGainTotal)','dB(GainTotal)','dB(DirTotal)',
               're(rETheta)','im(rETheta)','re(rEPhi)','im(rEPhi)']])
            reports.ExportToFile(name,os.path.join(root,name+'.csv'),False)
        log('CAMPOS_EXPORTADOS '+mode)
    sources(sol,ports);p.Save();oDesktop.CloseProject(p.GetName())
    write('qualificacao.json',dict(estado='SOLVE_EXPORTADO_AGUARDA_AUDITORIA',fim=datetime.datetime.now().isoformat(),gui=False))
    log('SOLVE_EXPORTADO_HEADLESS '+cfg['revisao'])
except:
    write('falha.json',dict(erro=traceback.format_exc()));log(traceback.format_exc());raise
