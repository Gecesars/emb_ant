# -*- coding: utf-8 -*-
"""Verificacao da discretizacao local de cobre/solda, preservando o setup e o cache."""
import os,sys,json,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
folder=os.path.join(os.environ['P1H_R06'],'antena')
def log(s):
    with open(os.path.join(folder,'refinamento.log'),'a') as f:f.write(str(s)+'\n')
try:
    assert os.path.isfile(os.path.join(folder,'padroes','E10_B_V.csv'))
    project=oDesktop.OpenProject(os.path.join(folder,'PCB_R06.aedt'))
    design=project.SetActiveDesign('PCB_sem_cabos');editor=design.SetActiveEditor('3D Modeler')
    objects=list(editor.GetObjectsInGroup('Solids'))
    fragments=[n for n in objects if n.endswith('_Cu1')]
    solders=[n for n in objects if n.startswith('Solda_terminal_')]
    assert len(fragments)==20 and len(solders)==40
    mesh=design.GetModule('MeshSetup')
    assert 'Cobre_solda_curvatura' not in list(mesh.GetOperationNames('Surface Approximation Based'))
    mesh.AssignTrueSurfOp(['NAME:Cobre_solda_curvatura','Objects:=',fragments+solders,
      'CurvedSurfaceApproxChoice:=','ManualSettings','SurfDevChoice:=',2,'SurfDev:=','0.0005mm',
      'NormalDevChoice:=',2,'NormalDev:=','5deg','AspectRatioChoice:=',1,'AspectRatio:=','10'])
    mesh.AssignLengthOp(['NAME:Fragmentos_60um','RefineInside:=',False,'Enabled:=',True,
      'Objects:=',fragments,'RestrictElem:=',False,'NumMaxElem:=','1000',
      'RestrictLength:=',True,'MaxLength:=','0.06mm'])
    project.Save();log('REFINAMENTO_LOCAL_INICIADO')
    design.Analyze('Banda')
    design.ExportConvergence('Banda','',os.path.join(folder,'convergencia.txt'))
    solutions=design.GetModule('Solutions')
    solutions.ExportNetworkData('',['Banda : LastAdaptive'],3,os.path.join(folder,'antena.s20p'),['All'],True,50,'S',-1,1,15,False,True,False)
    reports=design.GetModule('ReportSetup')
    for axis in ['H','V']:reports.ExportToFile(axis,os.path.join(folder,'Centro_'+axis+'.csv'),False)
    project.Save();oDesktop.CloseProject(project.GetName());log('REFINAMENTO_LOCAL_CONCLUIDO_VERIFICAR')
except:log(traceback.format_exc())
