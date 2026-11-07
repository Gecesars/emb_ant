# -*- coding: utf-8 -*-
"""Exportar campos embutidos da PCB R06; nao altera nem recalcula o setup."""
import json, os, traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
folder=os.path.join(os.environ['P1H_R06'],'antena')
output=os.path.join(folder,'padroes')
if not os.path.isdir(output):os.makedirs(output)
def log(message):
    with open(os.path.join(folder,'padroes.log'),'a') as stream:stream.write(str(message)+'\n')
try:
    assert json.load(open(os.path.join(folder,'auditoria_convergencia.json')))['convergencia_aprovada']
    project=oDesktop.OpenProject(os.path.join(folder,'PCB_R06.aedt'))
    design=project.SetActiveDesign('PCB_sem_cabos')
    solutions=design.GetModule('Solutions');reports=design.GetModule('ReportSetup')
    ports=list(solutions.GetAllSources());assert len(ports)==20
    for active in ports:
        solutions.EditSources([['IncludePortPostProcessing:=',False,'SpecifySystemPower:=',False]]+
          [['Name:=',p+':1','Magnitude:=','1W' if p==active else '0W','Phase:=','0deg'] for p in ports])
        for axis,phi in [('H',90),('V',0)]:
            name='R06_'+active+'_'+axis
            reports.CreateReport(name,'Far Fields','Rectangular Plot','Banda : LastAdaptive',
              ['Context:=','HV'],['Theta:=',['All'],'Phi:=',[str(phi)+'deg'],'Freq:=',['5.17GHz']],
              ['X Component:=','Theta','Y Component:=',[
              're(rETheta)','im(rETheta)','re(rEPhi)','im(rEPhi)','dB(RealizedGainTotal)']])
            reports.ExportToFile(name,os.path.join(output,active+'_'+axis+'.csv'),False)
            reports.DeleteReports([name])
        log(active)
    solutions.EditSources([['IncludePortPostProcessing:=',False,'SpecifySystemPower:=',False]]+
      [['Name:=',p+':1','Magnitude:=','0.05W','Phase:=','0deg'] for p in ports])
    project.Save();oDesktop.CloseProject(project.GetName());log('PADROES_R06_OK')
except:log(traceback.format_exc())
