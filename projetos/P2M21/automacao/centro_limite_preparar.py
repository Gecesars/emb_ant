# -*- coding: utf-8 -*-
"""Alterar somente o teto adaptativo, sem apagar setup ou malha existente."""
import os,json,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P2M21_UNIFORME'];p=None
try:
    cfg=json.load(open(os.path.join(root,'configuracao.json')))
    assert cfg['max_passes']==4 and cfg['apenas_centro'] and cfg['nucleos']==14
    p=oDesktop.OpenProject(os.path.join(root,'antena',cfg['native']))
    d=p.SetActiveDesign('PCB_separada');m=d.GetModule('AnalysisSetup')
    assert list(m.GetSetups())==['Centro'] and not list(m.GetSweeps('Centro'))
    m.EditSetup('Centro',['NAME:Centro','MaximumPasses:=',4])
    p.Save();oDesktop.CloseProject(p.GetName());p=None
    with open(os.path.join(root,'limite_preparacao.log'),'a') as f:f.write('LIMITE_QUATRO_APLICADO\n')
except:
    with open(os.path.join(root,'limite_preparacao.log'),'a') as f:f.write(traceback.format_exc())
finally:
    if p is not None:p.Save();oDesktop.CloseProject(p.GetName())
