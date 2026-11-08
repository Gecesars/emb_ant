# -*- coding: utf-8 -*-
"""Campos complexos reais por porta/frequencia. Nao congela o elemento em banda."""
import os,json,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P1H_R07'];stage=os.environ['P1H_R07_ETAPA'];assert stage in ['centro','banda']
folder=os.path.join(root,'antena')
def log(s):
    with open(os.path.join(folder,'campos_'+stage+'.log'),'a') as f:f.write(str(s)+'\n')
try:
    assert json.load(open(os.path.join(folder,'auditoria_convergencia.json')))['convergencia_aprovada']
    p=oDesktop.OpenProject(os.path.join(folder,'PCB_R07.aedt'));d=p.SetActiveDesign('PCB_sem_cabos')
    sol=d.GetModule('Solutions');reports=d.GetModule('ReportSetup')
    ports=list(sol.GetAllSources());assert len(ports)==20
    solution='Banda : LastAdaptive' if stage=='centro' else 'Banda : Discreta_10MHz'
    def excite(active=None):
        sol.EditSources([['IncludePortPostProcessing:=',False,'SpecifySystemPower:=',False]]+
          [['Name:=',s+':1','Magnitude:=',('0.05W' if active is None else ('1W' if s==active else '0W')),
            'Phase:=','0deg'] for s in ports])
    def report(freq,axis,phi,path,complex_fields):
        name='R07_TEMP_'+axis
        if name in reports.GetAllReportNames():reports.DeleteReports([name])
        expressions=(['re(rETheta)','im(rETheta)','re(rEPhi)','im(rEPhi)'] if complex_fields else [])+['dB(RealizedGainTotal)']
        reports.CreateReport(name,'Far Fields','Rectangular Plot',solution,['Context:=','HV'],
          ['Theta:=',['All'],'Phi:=',[str(phi)+'deg'],'Freq:=',[str(freq)+'MHz']],
          ['X Component:=','Theta','Y Component:=',expressions])
        reports.ExportToFile(name,path,False);reports.DeleteReports([name])
        assert os.path.getsize(path)>20000,path
    for freq in ([5170] if stage=='centro' else range(5090,5251,10)):
        dest=os.path.join(root,'centro' if stage=='centro' else 'pontos',str(freq))
        if not os.path.isdir(os.path.join(dest,'padroes')):os.makedirs(os.path.join(dest,'padroes'))
        if stage=='centro':
            sol.ExportNetworkData('',[solution],3,os.path.join(dest,'antena.s20p'),['All'],True,50,'S',-1,1,15,False,True,False)
        for active in ports:
            excite(active)
            for axis,phi in [('H',90),('V',0)]:
                report(freq,axis,phi,os.path.join(dest,'padroes',active+'_'+axis+'.csv'),True)
        excite()
        for axis,phi in [('H',90),('V',0)]:report(freq,axis,phi,os.path.join(dest,'Centro_'+axis+'.csv'),False)
        with open(os.path.join(dest,'campos.json'),'w') as f:json.dump(dict(frequencia_MHz=freq,solucao=solution,portas=ports,campos=40),f,indent=2)
        log('CAMPOS_%d_OK'%freq)
    p.Save();oDesktop.CloseProject(p.GetName());log('CAMPOS_'+stage.upper()+'_OK')
except:log(traceback.format_exc())
