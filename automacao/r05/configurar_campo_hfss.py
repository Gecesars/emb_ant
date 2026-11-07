# -*- coding: utf-8 -*-
import os
import sys
import traceback
import re
import ScriptEnv
sys.path.insert(0,os.path.dirname(__file__))
from criterios_campo import configure
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
folder=os.path.join(os.environ['P1H_R01'],'estudo')
try:
    project=oDesktop.OpenProject(os.path.join(folder,os.environ['P1H_NOME']+'.aedt'))
    design=project.SetActiveDesign('Painel_montado')
    # Somente antes do primeiro cálculo válido: remover caches antigos cujos
    # títulos com sinais negativos foram normalizados pelo AEDT.
    assert not os.path.isfile(os.path.join(folder,'convergencia.txt'))
    configure(design,reset=True)
    assert design.ValidateDesign()==1
    project.Save()
    data=open(os.path.join(folder,os.environ['P1H_NOME']+'.aedt'),'rb').read()
    assert len(re.findall(r"Title='G_[MP][0-9]+_P[0-9]+'",data))==9
    oDesktop.CloseProject(project.GetName())
    with open(os.path.join(folder,'criterios.log'),'w') as stream:stream.write('CRITERIOS_CAMPO_OK')
except:
    with open(os.path.join(folder,'criterios.log'),'w') as stream:stream.write(traceback.format_exc())
