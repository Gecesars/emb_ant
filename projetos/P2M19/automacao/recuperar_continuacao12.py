"""Retoma somente o passe 12 apos erro de JSON no checkpoint ja resolvido 11."""
from pathlib import Path
import ast, hashlib, json, shutil, re, sys

ROOT=Path('D:/dev/EMBRAER/P2M19/R07_72mm_ref146_12passes')
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def block(s,n):return s.split("$begin '"+n+"'",1)[1].split("$end '"+n+"'",1)[0]
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')

def main():
    assert not (ROOT/'processo_passe12.json').exists(),'Recuperacao ja iniciada'
    assert not (ROOT/'convergencia.txt').exists(),'Resultado final existente'
    cfg=json.loads((ROOT/'configuracao.json').read_text(encoding='utf-8'))
    native=ROOT/cfg['native'];cp=ROOT/'passe11'
    assert not Path(str(native)+'.lock').exists()
    assert sha(native)==sha(cp/cfg['native'])
    before=native.read_text(encoding='latin1')
    setup=block(before,'AnalysisSetup')
    assert 'MaximumPasses=11' in setup and 'MinimumPasses=11' in setup
    conv=(cp/'convergencia.txt').read_text()
    assert int(re.search(r'Completed\s*:\s*(\d+)',conv).group(1))==11
    ev=ROOT/'evidencias/recuperacao_codificacao';ev.mkdir(exist_ok=False)
    for name in ['falha.json','pipeline.json','analise_erro.log']:
        if (ROOT/name).exists():shutil.copy2(ROOT/name,ev/name)
    shutil.copy2(ROOT/'scripts/resolver.py',ev/'resolver_interrompido.py')
    cp_cfg=dict(cfg);cp_cfg.update(max_passes=11,min_passes=11,revisao=cfg['revisao']+'_checkpoint11')
    dump(cp/'configuracao.json',cp_cfg)
    dump(cp/'snapshot.json',dict(passe=11,nativo_sha256=sha(native),fontes_iguais_em_fase=True))
    sys.path.insert(0,'D:/dev/EMBRAER/emb_ant/projetos/P2M21/automacao')
    from oito_celulas_monitorar import progress
    h=progress(cp);assert h['historico'][-1]['passe']==11,h
    dump(cp/'historico_passes.json',h)
    original=(ROOT/'scripts/resolver.py').read_text(encoding='utf-8')
    prefix=original.split('try:\n    assert not os.path.exists',1)[0]
    tail=original.split("    d.ExportConvergence('Centro','',os.path.join(root,'convergencia.txt'))",1)[1]
    middle='''def block(text,name):
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
    assert re.findall(r'TraceID=(\\d+)',analysis)==re.findall(r'TraceID=(\\d+)',block(after12,'AnalysisSetup'))
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
    d.ExportConvergence('Centro','',os.path.join(root,'convergencia.txt'))'''
    script=prefix+middle+tail
    ast.parse(script)
    (ROOT/'scripts/resolver_passe12.py').write_text(script,encoding='utf-8')
    shutil.copy2(ROOT/'scripts/resolver_passe12.py',HERE/'continuacao12_resolver_passe12.py')
    runner=(ROOT/'scripts/continuar.ps1').read_text(encoding='utf-8-sig')
    runner=runner.replace("'processo_centro.json'","'processo_passe12.json'").replace('CONTINUANDO_PASSES_11_E_12','CONTINUANDO_SOMENTE_PASSE12').replace("Native 'resolver.py' 'centro'","Native 'resolver_passe12.py' 'passe12'")
    # Capturar o handle antes de esperar tambem no pos-processamento.
    runner=runner.replace('-WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput','-WindowStyle Hidden -PassThru -RedirectStandardOutput')
    runner=runner.replace('    [pscustomobject]@{pid=$a.Id;exit_code=', '    $analysisHandle=$a.Handle\n    $a.WaitForExit()\n    [pscustomobject]@{pid=$a.Id;exit_code=')
    (ROOT/'scripts/continuar_passe12.ps1').write_text(runner,encoding='utf-8-sig')
    shutil.copy2(ROOT/'scripts/continuar_passe12.ps1',HERE/'continuacao12_continuar_passe12.ps1')
    evidence=dict(causa='Erro de codificacao ao serializar configuracao no IronPython apos exportar passe 11; nenhum erro RF',passe11_preservado=True,passe12_ainda_nao_executado=True,nativo_passe11_sha256=sha(native),script_interrompido_sha256=sha(ev/'resolver_interrompido.py'),historico_final=h['historico'][-1])
    dump(ROOT/'evidencias/recuperacao_codificacao.json',evidence)
    # O marcador antigo fica preservado junto ao log; nao representa a retomada.
    (ROOT/'falha.json').rename(ev/'falha_original.json')
    print(json.dumps(evidence,ensure_ascii=True,indent=2))
if __name__=='__main__':main()
