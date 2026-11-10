# -*- coding: utf-8 -*-
import os,re,json
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root='D:/dev/EMBRAER/P2M21/R13_Casamento_Banda/c08_raiz_ajuste_fino'
p=oDesktop.OpenProject(os.path.join(root,'P2M21_4_elementos.aedt'));d=p.SetActiveDesign('Quatro_elementos');an=d.GetModule('AnalysisSetup')
assert not list(an.GetSweeps('Centro'))
d.ExportConvergence('Centro','',os.path.join(root,'antes_sexto_convergencia.txt'))
with open(os.path.join(root,'P2M21_4_elementos.aedt')) as stream:raw=stream.read()
assert 'MaximumPasses=6' in raw and 'MinimumPasses=2' in raw
an.EditSetup('Centro',['NAME:Centro','MinimumPasses:=',6,'Target:=',0.3333])
p.SaveAs(os.path.join(root,'P2M21_4_elementos.aedt'),True);oDesktop.CloseProject(p.GetName())
