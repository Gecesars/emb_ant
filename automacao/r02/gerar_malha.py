# -*- coding: utf-8 -*-
"""Preparar a malha TAU Flex do projeto R02 antes de iniciar os passes adaptativos."""
import os
import traceback
import ScriptEnv

ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
directory=os.path.join(os.environ["P1H_R01"],"estudo")
def log(message):
    with open(os.path.join(directory,"malha.log"),"a") as stream:stream.write(str(message)+"\n")
try:
    p=oDesktop.OpenProject(os.path.join(directory,os.environ["P1H_NOME"]+".aedt"))
    design=p.SetActiveDesign("Painel_montado")
    assert design.ValidateDesign()==1
    log("MALHA_INICIADA")
    code=design.GenerateMesh("Banda")
    log(list(oDesktop.GetMessages(p.GetName(),design.GetName(),2)))
    assert code==0,code
    p.Save()
    log("MALHA_OK")
except:log(traceback.format_exc())
