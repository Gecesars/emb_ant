# -*- coding: utf-8 -*-
"""Dois passes adicionais apos convergir, preservando os criterios e a geometria."""
import os,sys,json,traceback,re
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P1H_R06'];folder=os.path.join(root,'antena')
repo=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0,os.path.join(repo,'automacao','r05'))
from criterios_campo import configure
def log(message):
    with open(os.path.join(folder,'estabilidade_final.log'),'a') as f:f.write(str(message)+'\n')
try:
    reference=json.load(open(os.path.join(root,'antena_estrita21','auditoria_convergencia.json')))
    assert reference['convergencia_aprovada'] and reference['historico'][-1]['passe']==21
    project=oDesktop.OpenProject(os.path.join(folder,'PCB_R06.aedt'))
    design=project.SetActiveDesign('PCB_sem_cabos')
    # A serializacao PyAEDT do cache antigo usa ReportType numerico e um
    # SimValueContext nao aceito por EditSetup nesta release. Reconstruir
    # exatamente as mesmas nove expressoes pela API nativa ja validada.
    configure(design,reset=False,max_delta_s=.004,field_delta=.02,maximum_passes=25,minimum_passes=23)
    project.Save()
    raw=open(os.path.join(folder,'PCB_R06.aedt'),'rb').read()
    assert 'MinimumPasses=23' in raw and 'MaximumPasses=25' in raw and 'MaxDeltaS=0.004' in raw
    assert raw.count('MaxConvergenceDelta=0.02')==9
    assert len(re.findall(r"Title='G_[MP][0-9]+_P[0-9]+'",raw))==9
    with open(os.path.join(folder,'estabilidade_setup.json'),'w') as f:
        json.dump(dict(referencia='antena_estrita21',minimum_passes=23,maximum_passes=25,
            max_delta_s=.004,field_delta=.02,percent_refinement=15,reset=False,
            nota='Mesma geometria, malha e criterios; min23 exige pelo menos dois passes adicionais.'),f,indent=2)
    log('ESTABILIDADE_FINAL_INICIADA');design.Analyze('Banda')
    design.ExportConvergence('Banda','',os.path.join(folder,'convergencia.txt'))
    design.GetModule('Solutions').ExportNetworkData('',['Banda : LastAdaptive'],3,
      os.path.join(folder,'antena.s20p'),['All'],True,50,'S',-1,1,15,False,True,False)
    reports=design.GetModule('ReportSetup')
    for axis in ['H','V']:reports.ExportToFile(axis,os.path.join(folder,'Centro_'+axis+'.csv'),False)
    project.Save();oDesktop.CloseProject(project.GetName());log('ESTABILIDADE_FINAL_CONCLUIDA')
except:log(traceback.format_exc())
