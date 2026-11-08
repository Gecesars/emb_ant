# -*- coding: utf-8 -*-
"""Teste sem solver: editar somente limites de passes e taxa de refinamento."""
import os,json,traceback,re
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P1H_R06'];folder=os.path.join(root,'teste_edit_setup')
try:
    project=oDesktop.OpenProject(os.path.join(folder,'PCB_TesteEdit.aedt'))
    design=project.SetActiveDesign('PCB_sem_cabos')
    design.GetModule('AnalysisSetup').EditSetup('Banda',[
        'NAME:Banda','MinimumPasses:=',23,'MaximumPasses:=',25,'PercentRefinement:=',5])
    project.Save();oDesktop.CloseProject(project.GetName())
    raw=open(os.path.join(folder,'PCB_TesteEdit.aedt'),'rb').read()
    wanted=['Frequency','MaxDeltaS','MaximumPasses','MinimumPasses','MinimumConvergedPasses',
            'PercentRefinement','BasisOrder','DrivenSolverType','IterativeResidual']
    values={name:re.findall(name+'=([^\\r\\n]+)',raw) for name in wanted}
    values['cache']=re.findall("Title='(G_[^']+)'[\\s\\S]*?TraceID=(\\d+)",raw)
    values['field_delta']=re.findall('MaxConvergenceDelta=([^\\r\\n]+)',raw)
    with open(os.path.join(folder,'resultado.json'),'w') as f:json.dump(values,f,indent=2)
except:
    with open(os.path.join(folder,'erro.txt'),'w') as f:f.write(traceback.format_exc())
