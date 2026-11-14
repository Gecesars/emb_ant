# -*- coding: utf-8 -*-
"""AEDT2024R2 headless: P2M19, 16 portas coerentes e campos embutidos H/V."""
import os,json,traceback,datetime,re,hashlib,shutil
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root='D:/dev/EMBRAER/P2M19/R07_72mm_ref146_12passes'
cfg=json.load(open(os.path.join(root,'configuracao.json')))
native=os.path.join(root,cfg['native'])
def write(n,v):
    with open(os.path.join(root,n),'w') as f:json.dump(v,f,indent=2)
def log(s):
    with open(os.path.join(root,'centro.log'),'a') as f:f.write(datetime.datetime.now().isoformat()+' '+s+'\n')
def sources(sol,selected):
    ports=list(sol.GetAllSources());assert set(ports)==set(p['name'] for p in cfg['portas'])
    assert selected and set(selected).issubset(set(ports))
    power='%.12gW'%(1./len(selected))
    sol.EditSources([['IncludePortPostProcessing:=',False,'SpecifySystemPower:=',False]]+
     [['Name:=',name+':1','Magnitude:=',power if name in selected else '0W','Phase:=','0deg'] for name in ports])
def block(text,name):
    return text.split("$begin '"+name+"'",1)[1].split("$end '"+name+"'",1)[0]
try:
    assert not os.path.exists(os.path.join(root,'convergencia.txt'))
    before12=open(native).read()
    snapshot=json.load(open(os.path.join(root,'passe11/snapshot.json')))
    from System.IO import File
    from System.Security.Cryptography import SHA256
    from System import BitConverter
    digest=BitConverter.ToString(SHA256.Create().ComputeHash(File.ReadAllBytes(native))).Replace('-','').ToLower()
    assert digest==snapshot['nativo_sha256']
    analysis=block(before12,'AnalysisSetup')
    for value in ['MaximumPasses=11','MinimumPasses=11','MaxDeltaS=0.05','MinimumConvergedPasses=2','5.17GHz','BasisOrder=1']:
        assert value in analysis,value
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign(cfg['design'])
    d.GetModule('AnalysisSetup').EditSetup('Centro',['NAME:Centro','MinimumPasses:=',12,'MaximumPasses:=',12])
    p.Save();oDesktop.CloseProject(p.GetName())
    after12=open(native).read()
    expected=analysis.replace('MaximumPasses=11','MaximumPasses=12').replace('MinimumPasses=11','MinimumPasses=12')
    assert block(after12,'AnalysisSetup')==expected
    for name in ['GeometryCore','Materials','BoundarySetup','MeshSetup','RadField']:
        assert block(before12,name)==block(after12,name),name
    assert re.findall(r'TraceID=(\d+)',analysis)==re.findall(r'TraceID=(\d+)',block(after12,'AnalysisSetup'))
    write('evidencias/retomada12_confirmada.json',dict(maximum_passes=12,minimum_passes=12,somente_min_max_alterados=True,cache_preservado=True,malha_origem_passes=11,malha_origem_tetraedros=1377459))
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign(cfg['design']);sol=d.GetModule('Solutions')
    assert not list(d.GetModule('AnalysisSetup').GetSweeps('Centro'))
    oDesktop.SetRegistryFromFile(os.path.join(root,'HFSS_14nucleos.acf'))
    oDesktop.SetRegistryString('Desktop/ActiveDSOConfigurations/HFSS','P2M19_14nucleos')
    assert oDesktop.GetRegistryString('Desktop/ActiveDSOConfigurations/HFSS')=='P2M19_14nucleos'
    ports=list(sol.GetAllSources());assert len(ports)==16
    sources(sol,ports);p.Save()
    valid=d.ValidateDesign();errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2));assert valid==1 and not errors,(valid,errors)
    write('qualificacao.json',dict(estado='EM_CALCULO_PASSE12',inicio=datetime.datetime.now().isoformat(),max_passes=12,passes_preservados=11,delta_s=.05,nucleos=14))
    write('ordem_fontes.json',ports)
    log('RETOMADA_SOMENTE_PASSE12_14NUCLEOS')
    d.Analyze('Centro')
    d.ExportConvergence('Centro','',os.path.join(root,'convergencia.txt'))
    write('mensagens.json',list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)))
    errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2));assert not errors,errors
    sol.ExportNetworkData('',['Centro : LastAdaptive'],3,os.path.join(root,'centro.s%dp'%len(ports)),['All'],True,50,'S',-1,1,15,False,True,False)
    reports=d.GetModule('ReportSetup')
    cases=[('ALL',ports),('POL_A',[n for n in ports if n.endswith('_A')]),('POL_B',[n for n in ports if n.endswith('_B')])]
    cases.extend((n,[n]) for n in ports)
    for mode,selected in cases:
        sources(sol,selected)
        for axis,phi in [('H',90),('V',0)]:
            name=mode+'_'+axis
            if name in list(reports.GetAllReportNames()): reports.DeleteReports([name])
            reports.CreateReport(name,'Far Fields','Rectangular Plot','Centro : LastAdaptive',['Context:=','HV'],
              ['Theta:=',['All'],'Phi:=',[str(phi)+'deg'],'Freq:=',['5170MHz']],
              ['X Component:=','Theta','Y Component:=',['dB(RealizedGainTotal)','dB(GainTotal)','dB(DirTotal)',
               're(rETheta)','im(rETheta)','re(rEPhi)','im(rEPhi)']])
            reports.ExportToFile(name,os.path.join(root,name+'.csv'),False)
        log('CAMPOS_EXPORTADOS '+mode)
    sources(sol,ports)
    for axis,phi in [('H',90),('V',0)]:
        name='ALL_'+axis+'_fino'
        if name in list(reports.GetAllReportNames()): reports.DeleteReports([name])
        reports.CreateReport(name,'Far Fields','Rectangular Plot','Centro : LastAdaptive',['Context:=','Centro_fino'],
          ['Theta:=',['All'],'Phi:=',[str(phi)+'deg'],'Freq:=',['5170MHz']],
          ['X Component:=','Theta','Y Component:=',['dB(RealizedGainTotal)','re(rETheta)','im(rETheta)','re(rEPhi)','im(rEPhi)']])
        reports.ExportToFile(name,os.path.join(root,name+'.csv'),False)
    if 'ALL_Potencia' in list(reports.GetAllReportNames()): reports.DeleteReports(['ALL_Potencia'])
    reports.CreateReport('ALL_Potencia','Far Fields','Rectangular Plot','Centro : LastAdaptive',['Context:=','Potencia'],
      ['Theta:=',['All'],'Phi:=',['All'],'Freq:=',['5170MHz']],
      ['X Component:=','Theta','Y Component:=',['dB(RealizedGainTotal)']])
    reports.ExportToFile('ALL_Potencia',os.path.join(root,'ALL_Potencia.csv'),False)
    try:
        expressions=['RadiatedPower','AcceptedPower','IncidentPower','RadiationEfficiency','SystemEfficiency']
        data=reports.GetSolutionDataPerVariation('Antenna Parameters','Centro : LastAdaptive',['Context:=','Potencia'],['Freq:=',['All']],expressions)
        write('potencia.json',dict((q,dict(real=list(data[0].GetRealDataValues(q)),units=data[0].GetDataUnits(q))) for q in expressions))
    except:
        write('potencia_erro.json',dict(erro=traceback.format_exc()))
    p.Save();oDesktop.CloseProject(p.GetName())
    write('qualificacao.json',dict(estado='SOLVE_EXPORTADO_AGUARDA_AUDITORIA',fim=datetime.datetime.now().isoformat(),gui=False))
    log('SOLVE_EXPORTADO_HEADLESS '+cfg['revisao'])
except:
    write('falha.json',dict(erro=traceback.format_exc()));log(traceback.format_exc());raise
