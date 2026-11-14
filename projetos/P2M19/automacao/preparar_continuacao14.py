"""Continua somente passes 13/14; preserva R07, malha e checkpoint RF do 13."""
from pathlib import Path
import json,shutil,hashlib,ast
SOURCE=Path('D:/dev/EMBRAER/P2M19/R07_72mm_ref146_12passes')
DEST=Path('D:/dev/EMBRAER/P2M19/R08_72mm_ref146_14passes')
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')

def main():
    assert not DEST.exists(),'Continuacao existente; nao duplicar'
    cfg=json.loads((SOURCE/'configuracao.json').read_text(encoding='utf-8'))
    h=json.loads((SOURCE/'historico_passes.json').read_text(encoding='utf-8'))
    assert len(h['historico'])==12 and h['historico'][-1]['tetraedros']==1632517
    assert sha(SOURCE/cfg['native'])=='478b418fc9bb5b21ac9952e17fdb152448d0b40d5d7abe71374914ef979c817f'
    assert not (SOURCE/(cfg['native']+'.lock')).exists()
    DEST.mkdir()
    for n in ['scripts','evidencias','passe13']:(DEST/n).mkdir()
    for n in [cfg['native'],cfg['cad_native'],'HFSS_14nucleos.acf','geometria_importada.json','hfss_validacao.json']:
        shutil.copy2(SOURCE/n,DEST/n)
    results=Path(cfg['native']).with_suffix('.aedtresults')
    for n in ['cad',results.name]:shutil.copytree(SOURCE/n,DEST/n)
    records=[]
    for p in (SOURCE/results).rglob('*'):
        if p.is_file():
            rel=p.relative_to(SOURCE);digest=sha(p);assert sha(DEST/rel)==digest
            records.append(dict(arquivo=rel.as_posix(),bytes=p.stat().st_size,sha256=digest))
    dump(DEST/'evidencias/copia_resultados_local.json',records)
    for n in ['historico_passes.json','resultado.json','convergencia.txt']:
        shutil.copy2(SOURCE/n,DEST/'evidencias'/('referencia12_'+n))
    cfg.update(revisao='P2M19_R08_72mm_ref146_14passes',max_passes=14,min_passes=14,
      referencia_comparacao=SOURCE.as_posix(),continuacao=dict(passes_preservados=12,passes_adicionais=2,
      nativo_referencia_sha256=sha(SOURCE/cfg['native']),geometria_inalterada=True,checkpoint_cortes_passe13=True),
      controle_comparacao='Mesma geometria de 72/146 mm; somente passes 13 e 14, preservando malha e cache.')
    dump(DEST/'configuracao.json',cfg)
    cp=dict(cfg);cp.update(max_passes=13,min_passes=13,revisao=cfg['revisao']+'_checkpoint13')
    dump(DEST/'passe13/configuracao.json',cp)
    # Trecho de exportacao completo ja usado nos passes 10 e 12.
    previous=(SOURCE/'scripts/resolver_passe12.py').read_text(encoding='utf-8')
    final_export="    d.ExportConvergence('Centro','',os.path.join(root,'convergencia.txt'))"+previous.split("    d.ExportConvergence('Centro','',os.path.join(root,'convergencia.txt'))",1)[1]
    native_script=r'''# -*- coding: utf-8 -*-
import os,json,traceback,datetime,re,shutil
from System.IO import File
from System.Text import Encoding
from System.Security.Cryptography import SHA256
from System import BitConverter
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root='__ROOT__'
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
'''.replace('__ROOT__',DEST.as_posix())+final_export
    ast.parse(native_script);(DEST/'scripts/resolver.py').write_text(native_script,encoding='utf-8')
    analyzer=(SOURCE/'scripts/analisar.py').read_text(encoding='utf-8').replace(SOURCE.as_posix(),DEST.as_posix())
    analyzer=analyzer.replace('R06: mesma geometria, dez passes; DeltaS atendido','R07: mesma geometria, doze passes; DeltaS atendido').replace('comparacao de dez versus doze passes','comparacao de doze versus quatorze passes').replace('R06_dez_passes_deltaS_atendido','R07_doze_passes_deltaS_atendido')
    ast.parse(analyzer);(DEST/'scripts/analisar.py').write_text(analyzer,encoding='utf-8')
    runner=(SOURCE/'scripts/continuar.ps1').read_text(encoding='utf-8-sig').replace('CONTINUANDO_PASSES_11_E_12','CONTINUANDO_PASSES_13_E_14')
    (DEST/'scripts/continuar.ps1').write_text(runner,encoding='utf-8-sig')
    for n in ['resolver.py','analisar.py','continuar.ps1']:shutil.copy2(DEST/'scripts'/n,HERE/('continuacao14_'+n))
    print(json.dumps(dict(destino=DEST.as_posix(),arquivos_resultados=len(records),bytes_resultados=sum(x['bytes'] for x in records),nativo_origem_sha256=sha(SOURCE/cfg['native'])),indent=2))
if __name__=='__main__':main()
