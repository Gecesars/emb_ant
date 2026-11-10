# -*- coding: utf-8 -*-
"""Testa TAU Flex na geometria integral, sem solve RF; reparos exigem auditoria."""
import os,json,time,datetime,traceback,hashlib,difflib
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P2S13_ROOT'];cfg=json.load(open(os.path.join(root,'configuracao.json')))
native=os.path.join(root,cfg['native'])
def write(n,x):
    with open(os.path.join(root,n),'w') as f:json.dump(x,f,indent=2)
def block(raw,key):return raw.split("$begin '"+key+"'",1)[1].split("$end '"+key+"'",1)[0]
try:
    original=open(native).read()
    assert "MeshMethod='AnsoftClassic'" in original and 'UseFlexMeshingForTAUvolumeMesh=false' in original
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign(cfg['design']);m=d.GetModule('MeshSetup')
    m.InitialMeshSettings(['NAME:MeshSettings',
      ['NAME:GlobalSurfApproximation','CurvedSurfaceApproxChoice:=','UseSlider','SliderMeshSettings:=',5],
      ['NAME:GlobalCurvilinear','Apply:=',False],['NAME:GlobalModelRes','UseAutoLength:=',True],
      'MeshMethod:=','AnsoftTAU','UseLegacyFaceterForTauVolumeMesh:=',False,
      'DynamicSurfaceResolution:=',False,'UseFlexMeshingForTAUvolumeMesh:=',True,
      'UseAlternativeMeshMethodsAsFallBack:=',False,'AllowPhiForLayeredGeometry:=',False])
    p.Save();oDesktop.CloseProject(p.GetName());updated=open(native).read();checks={}
    for key in ['Materials','GeometryCore','Boundaries','AnalysisSetup']:
        a,b=block(original,key),block(updated,key)
        checks[key]=dict(identico=a==b,sha_antes=hashlib.sha256(a.encode('utf-8')).hexdigest(),sha_depois=hashlib.sha256(b.encode('utf-8')).hexdigest());assert a==b,key
    a,b=block(original,'MeshSetup'),block(updated,'MeshSetup')
    assert a.replace("MeshMethod='AnsoftClassic'","MeshMethod='AnsoftTAU'").replace('UseFlexMeshingForTAUvolumeMesh=false','UseFlexMeshingForTAUvolumeMesh=true')==b
    checks['MeshSetup']=dict(diff=list(difflib.unified_diff(a.splitlines(),b.splitlines())))
    write('mudanca_setup.json',checks)
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign(cfg['design']);assert d.ValidateDesign()==1
    oDesktop.SetRegistryFromFile(os.path.join(root,'HFSS_14nucleos.acf'));oDesktop.SetRegistryString('Desktop/ActiveDSOConfigurations/HFSS','P2M21_14nucleos')
    start=time.time();write('qualificacao.json',dict(estado='GERANDO_MALHA_FLEX_APENAS',inicio=datetime.datetime.now().isoformat(),aedt_pid=oDesktop.GetProcessID(),solve_RF=False))
    rc=d.GenerateMesh('Centro');elapsed=time.time()-start
    write('geracao_malha.json',dict(retorno=rc,tempo_s=elapsed,solve_RF=False,fim=datetime.datetime.now().isoformat()))
    write('mensagens_malha.json',list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)))
    assert rc==0 and not list(oDesktop.GetMessages(p.GetName(),d.GetName(),2))
    p.Save();oDesktop.CloseProject(p.GetName());write('qualificacao.json',dict(estado='MALHA_GERADA_AGUARDA_AUDITORIA',tempo_s=elapsed,solve_RF=False))
except:
    try:write('mensagens_falha.json',list(oDesktop.GetMessages('','',0)))
    except:pass
    write('falha_malha.json',dict(erro=traceback.format_exc(),solve_RF=False));raise
