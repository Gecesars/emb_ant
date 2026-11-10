# -*- coding: utf-8 -*-
"""Isola componentes numa COPIA para localizar falha do mesher; nenhum solve RF."""
import os,json,time,datetime,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P2S13_ROOT'];cfg=json.load(open(os.path.join(root,'configuracao.json')))
def write(n,x):
    with open(os.path.join(root,n),'w') as f:json.dump(x,f,indent=2)
try:
    assert cfg['somente_diagnostico_malha'] is True
    p=oDesktop.OpenProject(os.path.join(root,cfg['native']));d=p.SetActiveDesign(cfg['design']);e=d.SetActiveEditor('3D Modeler')
    solids=list(e.GetObjectsInGroup('Solids'));sheets=list(e.GetObjectsInGroup('Sheets'))
    assert len(solids)==84 and 'Refletor_Al2mm' in solids
    keep=['Refletor_Al2mm','RadiatingSurface']
    for cell in cfg['celulas']:
        for pol in ['A','B']:
            keep.extend([cell['nome']+'_'+part+'_'+pol for part in ['PTFE','Vivo','Blindagem']])
    assert set(keep).issubset(set(solids)),(keep,solids)
    bd=d.GetModule('BoundarySetup');bd.DeleteBoundaries(['ENIG_faces_expostas'])
    removed=[n for n in solids if n not in keep]
    e.Delete(['NAME:Selections','Selections:=',','.join(removed)])
    assert set(e.GetObjectsInGroup('Solids'))==set(keep)
    assert list(e.GetObjectsInGroup('Sheets'))==sheets
    assert len(d.GetModule('Solutions').GetAllSources())==4
    write('isolamento.json',dict(mantidos=keep,removidos=removed,folhas=sheets,solve_RF=False,nota='Geometria isolada para diagnostico, nunca usar como resultado da antena.'))
    p.Save();assert d.ValidateDesign()==1
    start=time.time();write('qualificacao.json',dict(estado='GERANDO_MALHA_ISOLADA',inicio=datetime.datetime.now().isoformat(),aedt_pid=oDesktop.GetProcessID(),solve_RF=False))
    rc=d.GenerateMesh('Centro');elapsed=time.time()-start
    write('geracao_malha.json',dict(retorno=rc,tempo_s=elapsed,solve_RF=False,fim=datetime.datetime.now().isoformat()))
    write('mensagens_malha.json',list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)))
    assert rc==0 and not list(oDesktop.GetMessages(p.GetName(),d.GetName(),2))
    p.Save();oDesktop.CloseProject(p.GetName());write('qualificacao.json',dict(estado='MALHA_ISOLADA_CONCLUIDA',tempo_s=elapsed,solve_RF=False))
except:
    write('falha_malha.json',dict(erro=traceback.format_exc(),solve_RF=False));raise
