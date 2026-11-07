# -*- coding: utf-8 -*-
"""Ensaiar hipótese explícita de esmalte sem mudar o painel nominal."""
import os
import sys
import traceback
folder=os.path.dirname(os.path.abspath(__file__))
os.environ['P1H_BOBINA']=os.path.join(os.environ['P1H_R05'],'cupons')
sys.path.insert(0,os.path.join(folder,'..','r01'))
from bobina_hfss import solve,log
try:
    solve('Bobina_esmalte20',oDesktop,extra_dielectrics=[('Esmalte_hipotese',4.5,.03)])
except:
    log(traceback.format_exc())
