# -*- coding: utf-8 -*-
"""Continuar a malha refinada, sem reset de setup, com S/campo mais estritos."""
import os,sys,json,traceback,re
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
repo=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0,os.path.join(repo,'automacao','r05'))
from criterios_campo import configure
folder=os.path.join(os.environ['P1H_R06'],'antena')
def log(message):
    with open(os.path.join(folder,'convergencia_estrita.log'),'a') as f:f.write(str(message)+'\n')
try:
    previous=json.load(open(os.path.join(os.environ['P1H_R06'],'antena_refinada1','auditoria_convergencia.json')))
    assert previous['convergencia_aprovada']
    passes=previous['historico'][-1]['passe'];assert passes==11
    project=oDesktop.OpenProject(os.path.join(folder,'PCB_R06.aedt'))
    design=project.SetActiveDesign('PCB_sem_cabos')
    assert 'Banda' in list(design.GetModule('AnalysisSetup').GetSetups())
    configure(design,reset=False,max_delta_s=.004,field_delta=.02,maximum_passes=24,minimum_passes=passes+2)
    project.Save()
    raw=open(os.path.join(folder,'PCB_R06.aedt'),'rb').read()
    assert len(re.findall(r"Title='G_[MP][0-9]+_P[0-9]+'",raw))==9
    assert raw.count('MaxConvergenceDelta=0.02')==9
    log('CONTINUACAO_ESTRITA_INICIADA');design.Analyze('Banda')
    design.ExportConvergence('Banda','',os.path.join(folder,'convergencia.txt'))
    design.GetModule('Solutions').ExportNetworkData('',['Banda : LastAdaptive'],3,
      os.path.join(folder,'antena.s20p'),['All'],True,50,'S',-1,1,15,False,True,False)
    reports=design.GetModule('ReportSetup')
    for axis in ['H','V']:reports.ExportToFile(axis,os.path.join(folder,'Centro_'+axis+'.csv'),False)
    project.Save();oDesktop.CloseProject(project.GetName());log('CONTINUACAO_ESTRITA_CONCLUIDA')
except:log(traceback.format_exc())
