# -*- coding: utf-8 -*-
"""Construir o conjunto integrado R05 com ENIG nas superficies expostas."""
import os
import sys
import traceback
sys.path.insert(0,os.path.dirname(__file__))
from enig_boundary import apply
repo=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
execfile(os.path.join(repo,"automacao","r01","modelo_hfss.py"))
try:
    apply(project,d,cad,"Metais_impressos_35um")
    assert d.ValidateDesign()==1
    project.Save()
    log("MODELO_ENIG_OK")
    oDesktop.CloseProject(project.GetName())
except:
    log(traceback.format_exc())
