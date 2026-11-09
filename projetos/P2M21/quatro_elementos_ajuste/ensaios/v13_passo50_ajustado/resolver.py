# -*- coding: utf-8 -*-
"""AEDT 2024 R2 -ng: somente 5.17GHz; duas entradas iguais, ate seis passes."""
import os,json,traceback,datetime
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root='D:/dev/EMBRAER/P2M21/R11_Divisor_Ajustes/v13_passo50_ajustado'
native=os.path.join(root,'P2M21_4_elementos.aedt')

def write(name,data):
    with open(os.path.join(root,name),'w') as f:json.dump(data,f,indent=2)

def log(text):
    with open(os.path.join(root,'centro.log'),'a') as f:f.write(datetime.datetime.now().isoformat()+' '+text+'\n')

def sources(sol,active=None):
    ports=list(sol.GetAllSources());assert sorted(ports)==['A','B'],ports
    sol.EditSources([['IncludePortPostProcessing:=',False,'SpecifySystemPower:=',False]]+
        [['Name:=',name+':1','Magnitude:=',('0.5W' if active is None else '1W' if name==active else '0W'),'Phase:=','0deg'] for name in ports])

try:
    assert not os.path.exists(os.path.join(root,'convergencia.txt')),'Resultado ja existe; nao duplicar solve.'
    raw=open(native).read()
    analysis=raw.split("$begin 'AnalysisSetup'",1)[1].split("$end 'AnalysisSetup'",1)[0]
    for expr in ['MaximumPasses=6','MaxDeltaS=0.05','DoLambdaRefine=false','MinimumConvergedPasses=2','5.17GHz']:assert expr in analysis,expr
    assert 'AnsoftClassic' in raw and "Name='Apoio_POM" not in raw
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign('Quatro_elementos')
    assert not list(d.GetModule('AnalysisSetup').GetSweeps('Centro'))
    oDesktop.SetRegistryFromFile(os.path.join(root,'HFSS_14nucleos.acf'))
    oDesktop.SetRegistryString('Desktop/ActiveDSOConfigurations/HFSS','P2M21_14nucleos')
    assert oDesktop.GetRegistryString('Desktop/ActiveDSOConfigurations/HFSS')=='P2M21_14nucleos'
    sol=d.GetModule('Solutions');sources(sol);p.Save()
    valid=d.ValidateDesign();errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2));assert valid==1 and not errors,(valid,errors)
    write('qualificacao.json',dict(estado='EM_CALCULO_HEADLESS',inicio=datetime.datetime.now().isoformat(),max_passes=6,delta_s=.05,nucleos=14))
    log('SOLVE_INICIADO_4_ELEMENTOS_5170MHz_14NUCLEOS_MAX6')
    d.Analyze('Centro')
    d.ExportConvergence('Centro','',os.path.join(root,'convergencia.txt'))
    write('mensagens.json',list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)))
    errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2));assert not errors,errors
    sol.ExportNetworkData('',['Centro : LastAdaptive'],3,os.path.join(root,'centro.s2p'),['All'],True,50,'S',-1,1,15,False,True,False)
    reports=d.GetModule('ReportSetup')
    for mode,active in [('AB',None),('A','A'),('B','B')]:
        sources(sol,active)
        for axis,phi in [('H',90),('V',0)]:
            name=mode+'_'+axis
            reports.CreateReport(name,'Far Fields','Rectangular Plot','Centro : LastAdaptive',['Context:=','HV'],
                ['Theta:=',['All'],'Phi:=',[str(phi)+'deg'],'Freq:=',['5170MHz']],
                ['X Component:=','Theta','Y Component:=',['dB(RealizedGainTotal)','dB(GainTotal)','dB(DirTotal)',
                 're(rETheta)','im(rETheta)','re(rEPhi)','im(rEPhi)']])
            reports.ExportToFile(name,os.path.join(root,name+'.csv'),False)
    sources(sol)
    exec(compile(open(os.path.join(root,'sondas.py')).read(),'sondas.py','exec'))
    p.Save();oDesktop.CloseProject(p.GetName())
    write('qualificacao.json',dict(estado='SOLVE_EXPORTADO_AGUARDA_AUDITORIA',fim=datetime.datetime.now().isoformat(),gui=False))
    log('SOLVE_EXPORTADO_HEADLESS')
except:
    write('falha.json',dict(erro=traceback.format_exc()))
    log(traceback.format_exc())
    raise
