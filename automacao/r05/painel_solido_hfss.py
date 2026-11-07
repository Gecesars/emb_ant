# -*- coding: utf-8 -*-
"""Construir painel R05 com cobre de 35um e acabamento por faces exteriores."""
import os
import sys
import json
import traceback
sys.path.insert(0,os.path.dirname(__file__))
from enig_solido import apply
from criterios_campo import configure
repo=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
execfile(os.path.join(repo,'automacao','r01','modelo_hfss.py'))
try:
    records=json.load(open(os.path.join(cad,'folhas_solidas.json')))
    apply(project,d,records,os.path.join(cad,'enig_solido_hfss.json'))
    vias=[name for name in ed.GetObjectsInGroup('Solids') if name.startswith('Via')]
    assert len(vias)==20
    d.GetModule('MeshSetup').AssignTrueSurfOp(['NAME:Vias_curvatura_fina','Objects:=',vias,
        'CurvedSurfaceApproxChoice:=','ManualSettings','SurfDevChoice:=',2,'SurfDev:=','0.002mm',
        'NormalDevChoice:=',2,'NormalDev:=','10deg','AspectRatioChoice:=',1,'AspectRatio:=','10'])
    configure(d)
    assert d.ValidateDesign()==1
    project.Save()
    log('MODELO_SOLIDO_OK')
    oDesktop.CloseProject(project.GetName())
except:
    log(traceback.format_exc())
