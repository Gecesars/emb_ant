# -*- coding: utf-8 -*-
"""Autoriza exatamente mais dois passes, 5 e 6, preservando a malha atual."""
import os,json,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P2M21_UNIFORME'];p=None
try:
    cfg=json.load(open(os.path.join(root,'configuracao.json')))
    assert cfg['max_passes']==6 and cfg['min_passes']==6 and cfg['nucleos']==14 and cfg['apenas_centro']
    p=oDesktop.OpenProject(os.path.join(root,'antena',cfg['native']))
    d=p.SetActiveDesign('PCB_separada');m=d.GetModule('AnalysisSetup')
    assert list(m.GetSetups())==['Centro'] and not list(m.GetSweeps('Centro'))
    m.EditSetup('Centro',['NAME:Centro','MaximumPasses:=',6,'MinimumPasses:=',6])
    p.Save();oDesktop.CloseProject(p.GetName());p=None
    with open(os.path.join(root,'continuacao_preparacao.log'),'a') as f:f.write('CONTINUACAO_5_E_6_PREPARADA\n')
except:
    with open(os.path.join(root,'continuacao_preparacao.log'),'a') as f:f.write(traceback.format_exc())
finally:
    if p is not None:p.Save();oDesktop.CloseProject(p.GetName())
