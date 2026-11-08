# -*- coding: utf-8 -*-
"""Primeiro ensaio dos divisores: seis passes maximos; banda somente apos convergencia."""
import os,json,re,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root='D:/dev/EMBRAER/P2M21/R00_Concepcao'
def state(status,**kwargs):
    kwargs['estado']=status
    with open(os.path.join(root,'qualificacao.json'),'w') as f:json.dump(kwargs,f,indent=2)
try:
    for n in (4,8):
        folder=os.path.join(root,'divisor_1x%d'%n);path=os.path.join(folder,'P2M21_Duplo_1x%d.aedt'%n)
        with open(path) as f:native=f.read()
        assert 'MaximumPasses=6' in native and 'MaxDeltaS=0.02' in native
        p=oDesktop.OpenProject(path);d=p.SetActiveDesign('PCB_separada');s=d.GetModule('AnalysisSetup')
        # Densidade inicial nas linhas de quarto de onda, mantida no ciclo de seis passes.
        d.GetModule('MeshSetup').AssignLengthOp(['NAME:Linhas_RF_inicial','RefineInside:=',False,'Enabled:=',True,
          'Objects:=',['Estrela_A','Estrela_B'],'RestrictElem:=',False,'NumMaxElem:=','10000',
          'RestrictLength:=',True,'MaxLength:=','0.8mm'])
        def sweep(enabled):
            s.EditFrequencySweep('Centro','Banda17',['NAME:Banda17','IsEnabled:=',enabled,
             'RangeType:=','LinearStep','RangeStart:=','5090MHz','RangeEnd:=','5250MHz','RangeStep:=','10MHz',
             'Type:=','Discrete','SaveFields:=',False,'SaveRadFields:=',False])
        sweep(False);p.Save();state('SIMULANDO_CENTRO_DIVISOR',divisor=n,max_passes=6,max_delta_s=.02)
        d.Analyze('Centro');d.ExportConvergence('Centro','',os.path.join(folder,'convergencia.txt'));p.Save()
        with open(os.path.join(folder,'convergencia.txt')) as f:text=f.read()
        passes=int(re.search(r'Completed\s*:\s*(\d+)',text).group(1))
        consecutive=int(re.search(r'Current Consecutive Passes\s*:\s*(\d+)',text).group(1))
        target=float(re.search(r'Target\s*:\s*([\d.eE+-]+)',text).group(1))
        current=float(re.search(r'Current\s*:\s*([\d.eE+-]+)',text).group(1))
        assert 2<=passes<=6 and target<=.02 and current<=.02 and consecutive>=2 and 'Converged : Yes' in text, text
        ports=2*(n+1);sol=d.GetModule('Solutions')
        sol.ExportNetworkData('',['Centro : LastAdaptive'],3,os.path.join(folder,'centro.s%dp'%ports),['All'],True,50,'S',-1,1,15,False,True,False)
        sweep(True);p.Save();state('SIMULANDO_BANDA_DIVISOR',divisor=n,passes=passes,delta_s=current)
        d.Analyze('Centro')
        sol.ExportNetworkData('',['Centro : Banda17'],3,os.path.join(folder,'divisor.s%dp'%ports),['All'],True,50,'S',-1,1,15,False,True,False)
        p.Save();oDesktop.CloseProject(p.GetName())
    state('DIVISORES_CONCLUIDOS_AGUARDANDO_AUDITORIA',antena_simulada=False)
except:
    state('REQUER_VERIFICACAO',divisor=n,erro=traceback.format_exc())
