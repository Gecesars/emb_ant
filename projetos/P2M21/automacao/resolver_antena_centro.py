# -*- coding: utf-8 -*-
"""Centro do painel de64portas; somente apos os divisores liberarem a fila."""
import os,json,re,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root='D:/dev/EMBRAER/P2M21/R00_Concepcao';folder=os.path.join(root,'antena')
def state(status,**kwargs):
    kwargs['estado']=status
    with open(os.path.join(root,'qualificacao.json'),'w') as f:json.dump(kwargs,f,indent=2)
p=None
try:
    with open(os.path.join(root,'qualificacao.json')) as f:previous=json.load(f)
    assert previous['estado']=='DIVISORES_CONCLUIDOS_AGUARDANDO_AUDITORIA'
    path=os.path.join(folder,'P2M21_Antena.aedt')
    with open(path) as f:native=f.read()
    assert 'MaximumPasses=6' in native and 'MaxDeltaS=0.02' in native
    p=oDesktop.OpenProject(path);d=p.SetActiveDesign('PCB_separada');setup=d.GetModule('AnalysisSetup')
    setup.EditFrequencySweep('Centro','Banda17',['NAME:Banda17','IsEnabled:=',False,'RangeType:=','LinearStep',
     'RangeStart:=','5090MHz','RangeEnd:=','5250MHz','RangeStep:=','10MHz','Type:=','Discrete',
     'SaveFields:=',True,'SaveRadFields:=',True])
    p.Save();state('SIMULANDO_CENTRO_ANTENA',max_passes=6,max_delta_s=.02,portas=64)
    d.Analyze('Centro');d.ExportConvergence('Centro','',os.path.join(folder,'convergencia.txt'));p.Save()
    with open(os.path.join(folder,'convergencia.txt')) as f:conv=f.read()
    passes=int(re.search(r'Completed\s*:\s*(\d+)',conv).group(1))
    consecutive=int(re.search(r'Current Consecutive Passes\s*:\s*(\d+)',conv).group(1))
    delta=float(re.search(r'Current\s*:\s*([\d.eE+-]+)',conv).group(1))
    assert 2<=passes<=6 and consecutive>=2 and delta<=.02 and 'Converged : Yes' in conv,conv
    sol=d.GetModule('Solutions');reports=d.GetModule('ReportSetup');ports=list(sol.GetAllSources());assert len(ports)==64
    sol.ExportNetworkData('',['Centro : LastAdaptive'],3,os.path.join(folder,'centro.s64p'),['All'],True,50,'S',-1,1,15,False,True,False)
    state('EXTRAINDO_CAMPOS_CENTRO',passes=passes,delta_s=delta)
    out=os.path.join(folder,'padroes')
    if not os.path.isdir(out):os.makedirs(out)
    def sources(active=None,pol=None):
        sol.EditSources([['IncludePortPostProcessing:=',False,'SpecifySystemPower:=',False]]+
         [['Name:=',port+':1','Magnitude:=',('1W' if port==active else '0W') if active else ('0.03125W' if port.endswith('_'+pol) else '0W'),'Phase:=','0deg'] for port in ports])
    def report(name,path,axis,components):
        reports.CreateReport(name,'Far Fields','Rectangular Plot','Centro : LastAdaptive',['Context:=','HV'],
         ['Theta:=',['All'],'Phi:=',['90deg' if axis=='H' else '0deg'],'Freq:=',['5.17GHz']],
         ['X Component:=','Theta','Y Component:=',components]);reports.ExportToFile(name,path,False);reports.DeleteReports([name])
    for port in ports:
        sources(active=port)
        for axis in 'HV':report('E_'+port+'_'+axis,os.path.join(out,port+'_'+axis+'.csv'),axis,
          ['re(rETheta)','im(rETheta)','re(rEPhi)','im(rEPhi)','dB(RealizedGainTotal)'])
    for pol in 'AB':
        sources(pol=pol)
        for axis in 'HV':report('Uniforme_'+pol+'_'+axis,os.path.join(folder,'Uniforme_'+pol+'_'+axis+'.csv'),axis,['dB(RealizedGainTotal)'])
    sources(pol='A');p.Save()
    state('CENTROS_CONCLUIDOS_AGUARDANDO_CIRCUITO_E_AUDITORIA',passes_antena=passes,delta_s_antena=delta,
      banda_painel_qualificada=False,campos_embutidos=128)
except:state('REQUER_VERIFICACAO',etapa='antena_centro',erro=traceback.format_exc())
finally:
    if p is not None:
        p.Save();oDesktop.CloseProject(p.GetName())
