# -*- coding: utf-8 -*-
"""Reconstroi apenas refletor em primitivas HFSS exatas e testa a malha Classic."""
import os,json,math,time,datetime,traceback,hashlib,sys
sys.path.insert(0,os.path.dirname(__file__))
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P2S13_ROOT'];cfg=json.load(open(os.path.join(root,'configuracao.json')))
def write(n,x):
    with open(os.path.join(root,n),'w') as f:json.dump(x,f,indent=2)
def mm(x):return '%.15gmm'%x
def block(raw,key):return raw.split("$begin '"+key+"'",1)[1].split("$end '"+key+"'",1)[0]
try:
    source=os.path.join(root,'P2S13.aedt');dest=os.path.join(root,cfg['native']);assert not os.path.exists(dest)
    original=open(source).read();p=oDesktop.OpenProject(source);d=p.SetActiveDesign(cfg['design']);e=d.SetActiveEditor('3D Modeler')
    names=list(e.GetObjectsInGroup('Solids'));assert len(names)==84
    def snapshot(n):return dict(volume=e.GetObjectVolume(n),faces=list(e.GetFaceIDs(n)),bbox=list(e.GetObjectBoundingBox(n)))
    before=dict((n,snapshot(n)) for n in names);e.Delete(['NAME:Selections','Selections:=','Refletor_Al2mm'])
    from desenhar_refletor_hfss import criar
    yz=criar(e,cfg)
    after=dict((n,snapshot(n)) for n in names)
    assert all(before[n]==after[n] for n in names if n!='Refletor_Al2mm'),'Alteracao fora do refletor'
    ref0,ref1=before['Refletor_Al2mm'],after['Refletor_Al2mm']
    assert abs(float(ref0['volume'])-float(ref1['volume']))/float(ref0['volume'])<1e-4
    assert max(abs(float(x)-float(y)) for x,y in zip(ref0['bbox'],ref1['bbox']))<1e-5
    e.Export(['NAME:ExportParameters','AllowRegionDependentPartSelectionForPMLCreation:=',True,'AllowRegionSelectionForPMLCreation:=',True,'Selections:=','Refletor_Al2mm','File Name:=',os.path.join(root,'Refletor_nativo.step'),'Major Version:=',-1,'Minor Version:=',-1])
    p.SaveAs(dest,True);oDesktop.CloseProject(p.GetName());updated=open(dest).read();checks={}
    for k in ['Materials','Boundaries','AnalysisSetup','MeshSettings']:
        x,y=block(original,k),block(updated,k);assert x==y,k;checks[k]=dict(identico=True,sha256=hashlib.sha256(x.encode('utf-8')).hexdigest())
    write('reconstrucao_refletor.json',dict(antes=ref0,depois=ref1,outros_83_solidos_identicos=True,controles=checks,perfil_yz_mm=yz))
    p=oDesktop.OpenProject(dest);d=p.SetActiveDesign(cfg['design']);valid=d.ValidateDesign();errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2));write('hfss_validacao.json',dict(validacao=valid,erros=errors,portas=len(d.GetModule('Solutions').GetAllSources()),max_passes=6,max_delta_s=.05,simulado=False));assert valid==1 and not errors
    start=time.time();write('qualificacao.json',dict(estado='GERANDO_MALHA_REFLETOR_NATIVO',inicio=datetime.datetime.now().isoformat(),aedt_pid=oDesktop.GetProcessID(),solve_RF=False))
    rc=d.GenerateMesh('Centro');elapsed=time.time()-start;write('geracao_malha.json',dict(retorno=rc,tempo_s=elapsed,solve_RF=False,fim=datetime.datetime.now().isoformat()));write('mensagens_malha.json',list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)))
    assert rc==0 and not list(oDesktop.GetMessages(p.GetName(),d.GetName(),2))
    p.Save();oDesktop.CloseProject(p.GetName());write('qualificacao.json',dict(estado='MALHA_GERADA_AGUARDA_AUDITORIA',tempo_s=elapsed,solve_RF=False))
except:
    try:write('mensagens_falha.json',list(oDesktop.GetMessages('','',0)))
    except:pass
    write('falha_malha.json',dict(erro=traceback.format_exc(),solve_RF=False));raise
