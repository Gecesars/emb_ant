# -*- coding: utf-8 -*-
import os,json,traceback,datetime,re,shutil
from System.IO import File
from System.Text import Encoding
from System.Security.Cryptography import SHA256
from System import BitConverter
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root='D:/dev/EMBRAER/P2M19/R08_72mm_ref146_14passes'
cfg=json.load(open(os.path.join(root,'configuracao.json')))
native=os.path.join(root,cfg['native'])
def read_native():return File.ReadAllText(native,Encoding.GetEncoding(28591))
def native_sha():return BitConverter.ToString(SHA256.Create().ComputeHash(File.ReadAllBytes(native))).Replace('-','').ToLower()
def block(text,name):return text.split("$begin '"+name+"'",1)[1].split("$end '"+name+"'",1)[0]
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
def configure(old,total,expected_sha):
    assert native_sha()==expected_sha,'Nativo diferente do checkpoint'
    before=read_native();analysis=block(before,'AnalysisSetup')
    for value in ['MaximumPasses='+str(old),'MinimumPasses='+str(old),'MaxDeltaS=0.05','MinimumConvergedPasses=2','DoLambdaRefine=false','BasisOrder=1','5.17GHz']:
        assert value in analysis,value
    assert 'AnsoftClassic' in before
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign(cfg['design'])
    d.GetModule('AnalysisSetup').EditSetup('Centro',['NAME:Centro','MinimumPasses:=',total,'MaximumPasses:=',total])
    p.Save();oDesktop.CloseProject(p.GetName())
    after=read_native()
    expected=analysis.replace('MaximumPasses='+str(old),'MaximumPasses='+str(total)).replace('MinimumPasses='+str(old),'MinimumPasses='+str(total))
    assert block(after,'AnalysisSetup')==expected,'Setup alterado alem de min/max'
    names=['GeometryCore','Materials','BoundarySetup','MeshSetup','RadField']
    for n in names:assert block(before,n)==block(after,n),n
    traces=re.findall(r'TraceID=(\d+)',analysis)
    assert len(traces)==9 and traces==re.findall(r'TraceID=(\d+)',block(after,'AnalysisSetup'))
    write('evidencias/retomada%d_confirmada.json'%total,dict(maximum_passes=total,minimum_passes=total,
      somente_min_max_alterados=True,blocos_preservados=names,trace_ids_preservados=traces,
      nativo_anterior_sha256=expected_sha,nativo_configurado_sha256=native_sha(),passes_preservados=old))
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign(cfg['design']);sol=d.GetModule('Solutions')
    assert not list(d.GetModule('AnalysisSetup').GetSweeps('Centro'))
    oDesktop.SetRegistryFromFile(os.path.join(root,'HFSS_14nucleos.acf'))
    oDesktop.SetRegistryString('Desktop/ActiveDSOConfigurations/HFSS','P2M19_14nucleos')
    assert oDesktop.GetRegistryString('Desktop/ActiveDSOConfigurations/HFSS')=='P2M19_14nucleos'
    ports=list(sol.GetAllSources());assert len(ports)==16
    sources(sol,ports);p.Save()
    valid=d.ValidateDesign();errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2));assert valid==1 and not errors,(valid,errors)
    write('ordem_fontes.json',ports)
    write('qualificacao.json',dict(estado='EM_CALCULO_HEADLESS',passe_em_execucao=total,passes_preservados=old,
      max_passes=14,delta_s=.05,nucleos=14,inicio=datetime.datetime.now().isoformat()))
    return p,d,sol,ports
try:
    assert not os.path.exists(os.path.join(root,'convergencia.txt')),'Resultado final existente'
    p,d,sol,ports=configure(12,13,cfg['continuacao']['nativo_referencia_sha256'])
    log('SOLVE_PASSE13_INICIADO_14NUCLEOS');d.Analyze('Centro')
    checkpoint=os.path.join(root,'passe13')
    d.ExportConvergence('Centro','',os.path.join(checkpoint,'convergencia.txt'))
    conv=open(os.path.join(checkpoint,'convergencia.txt')).read()
    assert int(re.search(r'Completed\s*:\s*(\d+)',conv).group(1))==13
    errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2));assert not errors,errors
    write('passe13/mensagens.json',list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)))
    sol.ExportNetworkData('',['Centro : LastAdaptive'],3,os.path.join(checkpoint,'centro.s16p'),['All'],True,50,'S',-1,1,15,False,True,False)
    reports=d.GetModule('ReportSetup')
    for n in ['ALL_H','ALL_V','ALL_H_fino','ALL_V_fino','ALL_Potencia']:
        assert n in list(reports.GetAllReportNames()),n
        reports.ExportToFile(n,os.path.join(checkpoint,n+'.csv'),False)
    expressions=['RadiatedPower','AcceptedPower','IncidentPower','RadiationEfficiency','SystemEfficiency']
    data=reports.GetSolutionDataPerVariation('Antenna Parameters','Centro : LastAdaptive',['Context:=','Potencia'],['Freq:=',['All']],expressions)
    write('passe13/potencia.json',dict((q,dict(real=list(data[0].GetRealDataValues(q)),units=data[0].GetDataUnits(q))) for q in expressions))
    p.Save();oDesktop.CloseProject(p.GetName())
    digest=native_sha();shutil.copy2(native,os.path.join(checkpoint,cfg['native']))
    results=os.path.splitext(native)[0]+'.aedtresults'
    for folder,dirs,files in os.walk(results):
        for n in files:
            if n.endswith(('.EMConvData','.ExprCache','.profile')):
                src=os.path.join(folder,n);dst=os.path.join(checkpoint,os.path.relpath(src,root))
                parent=os.path.dirname(dst)
                if not os.path.exists(parent):os.makedirs(parent)
                shutil.copy2(src,dst)
    assert os.path.isfile(os.path.join(checkpoint,'configuracao.json'))
    write('passe13/snapshot.json',dict(passe=13,nativo_sha256=digest,fontes_iguais_em_fase=True))
    log('PASSE13_EXPORTADO_RETORNO_PASSE14')
    p,d,sol,ports=configure(13,14,digest)
    log('SOLVE_PASSE14_INICIADO_14NUCLEOS');d.Analyze('Centro')
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
