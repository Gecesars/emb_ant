# -*- coding: utf-8 -*-
"""Refinar a representação das vias e repetir o centro com Delta S mais estrito.

Executar somente após arquivar os resultados do centro anterior. Mantém geometria,
materiais, portas e potência; muda controles numéricos para avaliar estabilidade.
"""
import os
import traceback
import ScriptEnv

ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
folder=os.path.join(os.environ['P1H_R01'],'estudo')
try:
    filename=os.path.join(folder,os.environ['P1H_NOME']+'.aedt')
    project=oDesktop.OpenProject(filename)
    design=project.SetActiveDesign('Painel_montado')
    editor=design.SetActiveEditor('3D Modeler')
    vias=[name for name in editor.GetObjectsInGroup('Solids') if name.startswith('Via')]
    assert len(vias)==20,len(vias)
    mesh=design.GetModule('MeshSetup')
    mesh.AssignTrueSurfOp(['NAME:Vias_curvatura_fina','Objects:=',vias,
        'CurvedSurfaceApproxChoice:=','ManualSettings','SurfDevChoice:=',2,
        'SurfDev:=','0.002mm','NormalDevChoice:=',2,'NormalDev:=','10deg',
        'AspectRatioChoice:=',1,'AspectRatio:=','10'])
    design.GetModule('AnalysisSetup').EditSetup('Banda',['NAME:Banda',
        'SolveType:=','Single','Frequency:=','5.17GHz','MaxDeltaS:=',.008,
        'MaximumPasses:=',18,'MinimumPasses:=',3,'MinimumConvergedPasses:=',2,
        'PercentRefinement:=',15,'BasisOrder:=',0,'DrivenSolverType:=','Iterative Solver',
        'IterativeResidual:=',.00001,'SaveAnyFields:=',True,'SaveRadFieldsOnly:=',False])
    assert design.ValidateDesign()==1
    project.Save()
    oDesktop.CloseProject(project.GetName())
    # Reutilizar a exportação e a excitação do pipeline validado.
    os.environ.pop('P1H_ITERATIVO',None)
    os.environ['P1H_SOMENTE_CENTRO']='1'
    execfile(os.path.join(os.path.dirname(__file__),'..','r01','resolver.py'))
except:
    with open(os.path.join(folder,'refino.err'),'w') as stream:
        stream.write(traceback.format_exc())
