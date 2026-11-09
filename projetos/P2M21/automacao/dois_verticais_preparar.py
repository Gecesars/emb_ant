"""Gerar criacao e solve nativos para AEDT grafico; nenhuma sessao e fechada."""
from pathlib import Path
import json,shutil
repo=Path(__file__).resolve().parents[3];root=Path('D:/dev/EMBRAER/P2M21/R07_Dois_Verticais_GUI')
text=Path('D:/dev/EMBRAER/P2M21/R06_Integrada_1x2/criar_hfss_nativo.py').read_text()
text=text.replace("root='D:/dev/EMBRAER/P2M21/R06_Integrada_1x2'", "root='D:/dev/EMBRAER/P2M21/R07_Dois_Verticais_GUI'")
text=text.replace("for folder,filename in [('antena','P2M21_Antena_Integrada_1x2')]:", "for folder,filename in [('d52p6','Dois_Verticais_d52p6'),('d48p0','Dois_Verticais_d48p0'),('d56p0','Dois_Verticais_d56p0')]:")
text=text.replace("if folder=='antena':",'if True:')
text=text.replace("'0.03125W'","'0.5W'")
text=text.replace("p.Save();oDesktop.CloseProject(p.GetName());log('CRIADO_VALIDADO '+filename)","p.Save();e.FitAll();log('CRIADO_VALIDADO '+filename)")
text=text.replace("modo='PCB separada, restantes portas casadas em50ohms; cabos apenas no circuito'","modo='Dois elementos verticais e divisores impressos, dois cabos fisicos de 50mm e refletor local; portas nas extremidades dos cabos'")
text=text.replace("except:\n        log(traceback.format_exc());break","except:\n        log(traceback.format_exc());raise")
text += '''
# Resolver serialmente, na mesma GUI. Os projetos e a interface permanecem abertos.
oDesktop.SetRegistryFromFile(os.path.join(root,'HFSS_14nucleos.acf'))
oDesktop.SetRegistryString('Desktop/ActiveDSOConfigurations/HFSS','P2M21_14nucleos')
assert oDesktop.GetRegistryString('Desktop/ActiveDSOConfigurations/HFSS')=='P2M21_14nucleos'
for case in ['d52p6','d48p0','d56p0']:
    folder=os.path.join(root,case);p=oDesktop.SetActiveProject('Dois_Verticais_'+case)
    d=p.SetActiveDesign('PCB_separada');e=d.SetActiveEditor('3D Modeler');e.FitAll()
    marker=os.path.join(folder,'solve_iniciado.json');assert not os.path.exists(marker),'Nao duplicar solve'
    with open(marker,'w') as f:json.dump(dict(frequencia_GHz=5.17,nucleos=14,max_passes=4,gui=True),f)
    sol=d.GetModule('Solutions');reports=d.GetModule('ReportSetup');ports=list(sol.GetAllSources())
    assert len(ports)==2
    def sources(active=None):
        sol.EditSources([['IncludePortPostProcessing:=',False,'SpecifySystemPower:=',False]]+
          [['Name:=',s+':1','Magnitude:=',('0.5W' if active is None else '1W' if s==active else '0W'),'Phase:=','0deg'] for s in ports])
    sources();p.Save();log('SOLVE_INICIADO '+case);d.Analyze('Centro')
    d.ExportConvergence('Centro','',os.path.join(folder,'convergencia.txt'))
    messages=list(oDesktop.GetMessages(p.GetName(),d.GetName(),0));errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2))
    with open(os.path.join(folder,'mensagens.json'),'w') as f:json.dump(messages,f,indent=2)
    assert not errors,errors
    sol.ExportNetworkData('',['Centro : LastAdaptive'],3,os.path.join(folder,'centro.s2p'),['All'],True,50,'S',-1,1,15,False,True,False)
    for mode,active in [('AB',None),('A','A'),('B','B')]:
        sources(active)
        for axis,phi in [('H',90),('V',0)]:
            name=mode+'_'+axis
            reports.CreateReport(name,'Far Fields','Rectangular Plot','Centro : LastAdaptive',['Context:=','HV'],
              ['Theta:=',['All'],'Phi:=',[str(phi)+'deg'],'Freq:=',['5170MHz']],['X Component:=','Theta','Y Component:=',
              ['dB(RealizedGainTotal)','dB(GainTotal)','dB(DirTotal)','re(rETheta)','im(rETheta)','re(rEPhi)','im(rEPhi)']])
            reports.ExportToFile(name,os.path.join(folder,name+'.csv'),False)
    sources();p.Save();log('SOLVE_EXPORTADO '+case)
log('TRES_ESPACAMENTOS_CONCLUIDOS_GUI_ABERTA')
'''
(root/'criar_resolver_gui.py').write_text(text,encoding='utf-8')
shutil.copy2('D:/dev/EMBRAER/P2M21/R04_Centro_Classic/HFSS_14nucleos.acf',root/'HFSS_14nucleos.acf')
config=dict(estado='CAD_VALIDADO_AGUARDANDO_GUI',casos=['d52p6','d48p0','d56p0'],espacamentos_mm=[52.6,48.,56.],
  frequencia_GHz=5.17,max_passes=4,max_delta_s=.04,nucleos=14,gui=True,sweep=False,
  radiadores=2,colunas=1,divisores_1x2=2,portas=2,potencia_incidente_W=1,por_porta_W=.5,fase_graus=0,
  cabo_fisico=True,comprimento_cabo_mm=50,criterio_comparacao='Maior ganho frontal realizado AB; conferir VSWR, H/V e convergencia. Nao implica otimo global.',
  materiais='RO4350B .76mm, Cu35um/ENIG nominal, PTFE e cobre no cabo, AL5052 2mm, POM nominal',
  malha='Classic automatica, sem operacoes locais, lambda-refinement desligado; adaptacao durante solve20%.')
(root/'configuracao.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
oldroot=Path('D:/dev/EMBRAER/P2M21/R06_Integrada_1x2')
(oldroot/'interrompido_por_novo_ensaio.json').write_text(json.dumps(dict(estado='INTERROMPIDO_PARA_ENSAIO_DOIS_VERTICAIS',
  motivo='Usuario pede simular somente uma PCB de dois elementos com cabos em GUI; StopSimulations(True) aplicado ao AEDT212540 apos confirmar projeto.',
  resultados='Eventuais exports apos parada nao qualificam o painel completo; nenhuma continuacao automatica.'),indent=2)+'\n',encoding='utf-8')
print('GUI_SCRIPT_PREPARADO')
