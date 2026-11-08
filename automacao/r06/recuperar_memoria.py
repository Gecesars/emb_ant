# -*- coding: utf-8 -*-
"""Continua a malha21 com crescimento5%, sem relaxar erros ou recriar cache."""
import os,json,traceback,re,hashlib
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P1H_R06'];folder=os.path.join(root,'antena')
native=os.path.join(folder,'PCB_R06.aedt')
reference_path=os.path.join(root,'antena_estrita21','PCB_R06.aedt')

def log(message):
    with open(os.path.join(folder,'estabilidade_memoria.log'),'a') as f:f.write(str(message)+'\n')

def setup(raw):
    return re.search(r"\$begin 'AnalysisSetup'[\s\S]*?\$end 'AnalysisSetup'",raw).group(0)

try:
    reference=json.load(open(os.path.join(root,'antena_estrita21','auditoria_convergencia.json')))
    assert reference['convergencia_aprovada'] and reference['historico'][-1]['passe']==21
    old=open(reference_path,'rb').read()
    assert hashlib.sha256(old).hexdigest()=='19b6540a62e240713ff7a888fc4f1410e76c0f6e2e34a7deb8b0ac569dc18f24'
    assert open(native,'rb').read()==old, 'Restaurar checkpoint21 antes da abertura; preservar tentativa OOM.'
    project=oDesktop.OpenProject(native)
    design=project.SetActiveDesign('PCB_sem_cabos')
    # EditSetup parcial foi verificado em copia SEM SOLVER: somente tres
    # propriedades mudam, e os nove TraceID672-680 permanecem identicos.
    design.GetModule('AnalysisSetup').EditSetup('Banda',[
        'NAME:Banda','MinimumPasses:=',23,'MaximumPasses:=',25,'PercentRefinement:=',5])
    project.Save()
    oDesktop.CloseProject(project.GetName())
    new=open(native,'rb').read()
    expected=setup(old).replace('MaximumPasses=24','MaximumPasses=25').replace(
        'MinimumPasses=13','MinimumPasses=23').replace('PercentRefinement=15','PercentRefinement=5')
    assert setup(new)==expected, 'O setup mudou alem dos tres parametros autorizados.'
    assert new.count('MaxConvergenceDelta=0.02')==9
    assert re.findall(r"Title='(G_[^']+)'[\s\S]*?TraceID=(\d+)",new)==re.findall(
        r"Title='(G_[^']+)'[\s\S]*?TraceID=(\d+)",old)
    with open(os.path.join(folder,'estabilidade_setup.json'),'w') as f:
        json.dump(dict(referencia='antena_estrita21',minimum_passes=23,maximum_passes=25,
            max_delta_s=.004,field_delta=.02,percent_refinement=5,reset=False,
            sha256_native_referencia=hashlib.sha256(old).hexdigest(),
            cache_ids_preservados=True,edicao_parcial_verificada=True,
            nota='Tentativa15% falhou por SOLVER_OUT_OF_MEMORY. Crescimento reduzido5%; criterios e tolerancias preservados.'),f,indent=2)
    project=oDesktop.OpenProject(native)
    design=project.SetActiveDesign('PCB_sem_cabos')
    log('ESTABILIDADE_MEMORIA_INICIADA');design.Analyze('Banda')
    design.ExportConvergence('Banda','',os.path.join(folder,'convergencia.txt'))
    design.GetModule('Solutions').ExportNetworkData('',['Banda : LastAdaptive'],3,
      os.path.join(folder,'antena.s20p'),['All'],True,50,'S',-1,1,15,False,True,False)
    reports=design.GetModule('ReportSetup')
    for axis in ['H','V']:reports.ExportToFile(axis,os.path.join(folder,'Centro_'+axis+'.csv'),False)
    project.Save();oDesktop.CloseProject(project.GetName());log('ESTABILIDADE_MEMORIA_CONCLUIDA')
except:log(traceback.format_exc())
