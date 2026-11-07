# -*- coding: utf-8 -*-
"""Retomar somente a varredura existente apos falha de contexto de licenca."""
import os,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
folder=os.path.join(os.environ['P1H_R06'],'divisor_superior')
def log(s):
    with open(os.path.join(folder,'retomada.log'),'a') as f:f.write(str(s)+'\n')
try:
    project=oDesktop.OpenProject(os.path.join(folder,'Divisor_superior.aedt'))
    design=project.SetActiveDesign('Divisor_completo')
    assert list(design.GetModule('AnalysisSetup').GetSetups())==['Centro']
    solutions=design.GetModule('Solutions')
    assert len(solutions.GetAllSources())==12
    design.ExportConvergence('Centro','',os.path.join(folder,'convergencia_antes_retomada.txt'))
    solutions.ExportNetworkData('',['Centro : LastAdaptive'],3,os.path.join(folder,'divisor_centro.s12p'),['All'],True,50,'S',-1,1,15,False,True,False)
    log('CENTRO_PRESERVADO_RETOMANDO_VARREDURA')
    design.Analyze('Centro')
    design.ExportConvergence('Centro','',os.path.join(folder,'convergencia.txt'))
    text=open(os.path.join(folder,'convergencia.txt')).read();assert 'Converged : Yes' in text
    solutions.ExportNetworkData('',['Centro : Banda'],3,os.path.join(folder,'divisor.s12p'),['All'],True,50,'S',-1,1,15,False,True,False)
    project.Save();oDesktop.CloseProject(project.GetName());log('DIVISOR_SUPERIOR_RETOMADO_CONCLUIDO')
except:log(traceback.format_exc())
