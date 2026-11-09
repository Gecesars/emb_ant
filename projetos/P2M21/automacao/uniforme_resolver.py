# -*- coding: utf-8 -*-
"""Centro ou 17 pontos discretos da antena com todas as 64 portas iguais/em fase."""
import os,json,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P2M21_UNIFORME'];stage=os.environ['P2M21_ETAPA'];assert stage in ('centro','banda')
folder=os.path.join(root,'antena');p=None
def log(s):
    with open(os.path.join(folder,stage+'.log'),'a') as f:f.write(str(s)+'\n')
try:
    cfg=json.load(open(os.path.join(root,'configuracao.json')))
    if stage=='banda':assert json.load(open(os.path.join(folder,'auditoria_centro.json')))['aprovado']
    p=oDesktop.OpenProject(os.path.join(folder,cfg['native']));d=p.SetActiveDesign('PCB_separada')
    sol=d.GetModule('Solutions');reports=d.GetModule('ReportSetup');ports=list(sol.GetAllSources())
    assert len(ports)==64
    sol.EditSources([['IncludePortPostProcessing:=',False,'SpecifySystemPower:=',False]]+
      [['Name:=',s+':1','Magnitude:=','0.015625W','Phase:=','0deg'] for s in ports])
    if stage=='banda':
        d.GetModule('AnalysisSetup').EditFrequencySweep('Centro','Banda17',['NAME:Banda17','IsEnabled:=',True,
          'RangeType:=','LinearStep','RangeStart:=','5090MHz','RangeEnd:=','5250MHz','RangeStep:=','10MHz',
          'Type:=','Discrete','SaveFields:=',True,'SaveRadFields:=',True])
    p.Save();log(stage.upper()+'_INICIADO');d.Analyze('Centro')
    with open(os.path.join(folder,'mensagens_'+stage+'.json'),'w') as f:
        json.dump(list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)),f,indent=2)
    d.ExportConvergence('Centro','',os.path.join(folder,'convergencia_'+stage+'.txt'))
    errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2));assert not errors,errors
    solution='Centro : '+('LastAdaptive' if stage=='centro' else 'Banda17')
    sol.ExportNetworkData('',[solution],3,os.path.join(folder,stage+'.s64p'),['All'],True,50,'S',-1,1,15,False,True,False)
    for freq in ([5170] if stage=='centro' else range(5090,5251,10)):
        dest=os.path.join(folder,stage,str(freq))
        if not os.path.isdir(dest):os.makedirs(dest)
        for axis,phi in [('H',90),('V',0)]:
            name='Uniforme_'+stage+'_'+str(freq)+'_'+axis
            if name in list(reports.GetAllReportNames()):reports.DeleteReports([name])
            expressions=['re(rETheta)','im(rETheta)','re(rEPhi)','im(rEPhi)',
              'dB(RealizedGainTotal)','dB(GainTotal)','dB(DirTotal)']
            reports.CreateReport(name,'Far Fields','Rectangular Plot',solution,['Context:=','HV'],
              ['Theta:=',['All'],'Phi:=',[str(phi)+'deg'],'Freq:=',[str(freq)+'MHz']],
              ['X Component:=','Theta','Y Component:=',expressions])
            path=os.path.join(dest,'Uniforme_'+axis+'.csv');reports.ExportToFile(name,path,False)
            assert os.path.getsize(path)>20000,path
            reports.DeleteReports([name])
        log('CAMPOS_%d_OK'%freq)
    p.Save();oDesktop.CloseProject(p.GetName());p=None
    log(stage.upper()+'_UNIFORME_OK')
except:log(traceback.format_exc())
finally:
    if p is not None:
        p.Save();oDesktop.CloseProject(p.GetName())
