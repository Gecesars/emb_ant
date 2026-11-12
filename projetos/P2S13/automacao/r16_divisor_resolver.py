# -*- coding: utf-8 -*-
"""Resolver so o novo divisor com tubo, sem recriar malha/configuracao."""
import os,json,datetime,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P2S13_ROOT'];cfg=json.load(open(os.path.join(root,'configuracao.json')));native=os.path.join(root,cfg['native'])
def save(n,v):
    with open(os.path.join(root,n),'w') as f:json.dump(v,f,indent=2)
try:
    assert os.path.exists(os.path.join(root,'tubo_criado.json')) and not os.path.exists(os.path.join(root,'convergencia.txt'))
    raw=open(native).read();analysis=raw.split("$begin 'AnalysisSetup'",1)[1].split("$end 'AnalysisSetup'",1)[0]
    for x in ['MaximumPasses=6','MaxDeltaS=0.05','MinimumPasses=2','MinimumConvergedPasses=2','DoLambdaRefine=false',"DrivenSolverType='Direct Solver'"]:assert x in analysis,x
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign(cfg['design']);sol=d.GetModule('Solutions')
    ports=list(sol.GetAllSources());assert len(ports)==8
    sol.EditSources([['IncludePortPostProcessing:=',False,'SpecifySystemPower:=',False]]+
        [['Name:=',n+':1','Magnitude:=','.5W' if n.startswith('IN_') else '0W','Phase:=','0deg'] for n in ports])
    assert not list(d.GetModule('AnalysisSetup').GetSweeps('Centro'))
    oDesktop.SetRegistryFromFile(os.path.join(root,'HFSS_14nucleos.acf'));oDesktop.SetRegistryString('Desktop/ActiveDSOConfigurations/HFSS','P2M21_14nucleos')
    assert oDesktop.GetRegistryString('Desktop/ActiveDSOConfigurations/HFSS')=='P2M21_14nucleos'
    save('estado.json',dict(estado='EM_CALCULO',inicio=datetime.datetime.now().isoformat(),nucleos=14,max_passes=6,delta_s=.05))
    p.Save();d.Analyze('Centro');d.ExportConvergence('Centro','',os.path.join(root,'convergencia.txt'))
    save('mensagens.json',list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)))
    errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2));assert not errors,errors
    sol.ExportNetworkData('',['Centro : LastAdaptive'],3,os.path.join(root,'divisor.s8p'),['All'],True,50,'S',-1,1,15,False,True,False)
    p.SaveAs(native,True);oDesktop.CloseProject(p.GetName());save('estado.json',dict(estado='CONCLUIDO_AGUARDA_ANALISE'))
except:save('falha.json',dict(erro=traceback.format_exc()));raise
