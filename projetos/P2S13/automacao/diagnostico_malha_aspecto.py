# -*- coding: utf-8 -*-
"""Controle de qualidade das facetas do refletor; somente geracao da malha."""
import os,json,datetime,traceback,hashlib,time,re
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P2S13_ROOT'];cfg=json.load(open(os.path.join(root,'configuracao.json')))
native=os.path.join(root,cfg['native'])
def write(n,x):
    with open(os.path.join(root,n),'w') as f:json.dump(x,f,indent=2)
def block(raw,key):return raw.split("$begin '"+key+"'",1)[1].split("$end '"+key+"'",1)[0]
try:
    reference=os.path.join(os.path.dirname(root),cfg['referencia_geometria_identica'],cfg['native'])
    original=open(reference).read()
    assert "MeshMethod='AnsoftClassic'" in original and 'DynamicSurfaceResolution=false' in original
    assert 'Qualidade_Refletor' not in original
    current=open(native).read()
    if 'Qualidade_Refletor' not in current:
        p=oDesktop.OpenProject(native);d=p.SetActiveDesign(cfg['design']);m=d.GetModule('MeshSetup')
        m.AssignTrueSurfOp(['NAME:Qualidade_Refletor','Type:=','SurfApproxBased','Objects:=',['Refletor_Al2mm'],
          'CurvedSurfaceApproxChoice:=','ManualSettings','SurfDevChoice:=',2,'SurfDev:=','0.02mm',
          'NormalDevChoice:=',1,'NormalDev:=','1','AspectRatioChoice:=',2,'AspectRatio:=',20])
        p.Save();oDesktop.CloseProject(p.GetName())
    updated=open(native).read();checks={}
    for key in ['Materials','GeometryCore','Boundaries','AnalysisSetup','MeshSettings']:
        a,b=block(original,key),block(updated,key);checks[key]=dict(identico=a==b,sha_antes=hashlib.sha256(a.encode('utf-8')).hexdigest(),sha_depois=hashlib.sha256(b.encode('utf-8')).hexdigest());assert a==b,key
    operation=block(updated,'Qualidade_Refletor')
    assert re.search(r"AspectRatio='?20'?\s",operation)
    assert "SurfDev='0.02mm'" in operation and 'AspectRatioChoice=2' in operation
    assert 'SurfDevChoice=2' in operation and 'NormalDevChoice=1' in operation
    assert updated.count("$begin 'Qualidade_Refletor'")==1
    checks['operacao_adicionada']=dict(nome='Qualidade_Refletor',objeto='Refletor_Al2mm',desvio_superficial_mm=.02,aspecto_maximo=20,normal='padrao',tipo='SurfApproxBased',comprimento_de_elemento_imposto=False)
    write('mudanca_setup.json',checks)
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign(cfg['design']);assert d.ValidateDesign()==1
    assert len(d.GetModule('Solutions').GetAllSources())==4 and not list(d.GetModule('AnalysisSetup').GetSweeps('Centro'))
    oDesktop.SetRegistryFromFile(os.path.join(root,'HFSS_14nucleos.acf'));oDesktop.SetRegistryString('Desktop/ActiveDSOConfigurations/HFSS','P2M21_14nucleos')
    start=time.time();write('qualificacao.json',dict(estado='GERANDO_MALHA_APENAS',inicio=datetime.datetime.now().isoformat(),aedt_pid=oDesktop.GetProcessID(),solve_RF=False))
    rc=d.GenerateMesh('Centro');elapsed=time.time()-start
    write('mensagens_malha.json',list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)))
    write('geracao_malha.json',dict(retorno=rc,tempo_s=elapsed,solve_RF=False,metodo='Classic; qualidade de facetas no refletor',fim=datetime.datetime.now().isoformat()))
    assert rc==0,rc
    assert not list(oDesktop.GetMessages(p.GetName(),d.GetName(),2))
    p.Save();oDesktop.CloseProject(p.GetName());write('qualificacao.json',dict(estado='MALHA_GERADA_AGUARDA_AUDITORIA',tempo_s=elapsed,solve_RF=False))
except:
    err=traceback.format_exc()
    try:write('mensagens_falha.json',list(oDesktop.GetMessages('','',0)))
    except:pass
    write('falha_malha.json',dict(erro=err,solve_RF=False));raise
