"""Clone fechado da R04, incluindo resultados, para somente os passes 7 e 8."""
from pathlib import Path
import json, shutil, hashlib, ast

SOURCE=Path('D:/dev/EMBRAER/P2M19/R04_72mm_ref146')
DEST=Path('D:/dev/EMBRAER/P2M19/R05_72mm_ref146_8passes')
HERE=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not DEST.exists(), 'Inspecionar continuacao existente; nao duplicar.'
    cfg=json.loads((SOURCE/'configuracao.json').read_text(encoding='utf-8'))
    assert not (SOURCE/(cfg['native']+'.lock')).exists()
    h=json.loads((SOURCE/'historico_passes.json').read_text(encoding='utf-8'))
    assert len(h['historico'])==6 and h['historico'][-1]['tetraedros']==602282
    DEST.mkdir(); (DEST/'scripts').mkdir(); (DEST/'evidencias').mkdir()
    files=[cfg['native'],cfg['cad_native'],'HFSS_14nucleos.acf','geometria_importada.json','hfss_validacao.json']
    for name in files: shutil.copy2(SOURCE/name,DEST/name)
    for name in ['cad',Path(cfg['native']).with_suffix('.aedtresults').name]: shutil.copytree(SOURCE/name,DEST/name)
    copied=[]
    for p in (SOURCE/Path(cfg['native']).with_suffix('.aedtresults')).rglob('*'):
        if p.is_file():
            rel=p.relative_to(SOURCE); digest=sha(p)
            assert sha(DEST/rel)==digest
            copied.append(dict(arquivo=str(rel),bytes=p.stat().st_size,sha256=digest))
    (DEST/'evidencias/copia_resultados_local.json').write_text(json.dumps(copied,indent=2))
    for name in ['historico_passes.json','resultado.json','convergencia.txt']:
        shutil.copy2(SOURCE/name,DEST/'evidencias'/('referencia6_'+name))
    cfg.update(revisao='P2M19_R05_72mm_ref146_8passes',max_passes=8,min_passes=8,
        referencia_comparacao=str(SOURCE),continuacao=dict(passes_preservados=6,passes_adicionais=2,
        nativo_referencia_sha256=sha(SOURCE/cfg['native']),geometria_inalterada=True),
        controle_comparacao='Mesma geometria R04; somente dois passes adicionais, preservando malha e cache.')
    (DEST/'configuracao.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    resolver=(SOURCE/'scripts/resolver.py').read_text(encoding='utf-8').replace(str(SOURCE).replace('\\','/'),str(DEST).replace('\\','/'))
    resolver=resolver.replace('import os,json,traceback,datetime','import os,json,traceback,datetime,re,hashlib')
    needle="    assert 'AnsoftClassic' in raw\n    p=oDesktop.OpenProject(native);d=p.SetActiveDesign(cfg['design'])"
    replacement="""    assert 'AnsoftClassic' in raw
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign(cfg['design'])
    d.GetModule('AnalysisSetup').EditSetup('Centro',['NAME:Centro','MinimumPasses:=',8,'MaximumPasses:=',8])
    p.Save();oDesktop.CloseProject(p.GetName())
    after=open(native).read()
    def block(text,name):
        return text.split(\"$begin '\"+name+\"'\",1)[1].split(\"$end '\"+name+\"'\",1)[0]
    expected=analysis.replace('MaximumPasses=6','MaximumPasses=8').replace('MinimumPasses=2','MinimumPasses=8')
    assert block(after,'AnalysisSetup')==expected,'Setup alterado alem de min/max passes'
    preserved={}
    for name in ['GeometryCore','Materials','BoundarySetup','MeshSetup','RadField']:
        assert block(raw,name)==block(after,name),name
        preserved[name]=hashlib.sha256(block(after,name)).hexdigest()
    assert re.findall(r'TraceID=(\\d+)',analysis)==re.findall(r'TraceID=(\\d+)',block(after,'AnalysisSetup'))
    write('evidencias/retomada_confirmada.json',dict(maximum_passes=8,minimum_passes=8,
        somente_min_max_alterados=True,cache_preservado=True,blocos_fisicos_sha256=preserved,
        malha_origem_passes=6,malha_origem_tetraedros=602282))
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign(cfg['design'])"""
    assert needle in resolver; resolver=resolver.replace(needle,replacement)
    resolver=resolver.replace('max_passes=6,delta_s=.05','max_passes=8,passes_adicionais=2,delta_s=.05').replace('5170MHz_14NUCLEOS_MAX6','5170MHz_14NUCLEOS_CONTINUAR7_8')
    # Exportar os relatorios existentes com a excitacao atual, sem duplicar definicoes.
    resolver=resolver.replace("            reports.CreateReport(name,", "            if name in list(reports.GetAllReportNames()): reports.DeleteReports([name])\n            reports.CreateReport(name,")
    needle="        name='ALL_'+axis+'_fino'\n        reports.CreateReport(name,"
    resolver=resolver.replace(needle,"        name='ALL_'+axis+'_fino'\n        if name in list(reports.GetAllReportNames()): reports.DeleteReports([name])\n        reports.CreateReport(name,")
    resolver=resolver.replace("    reports.CreateReport('ALL_Potencia',","    if 'ALL_Potencia' in list(reports.GetAllReportNames()): reports.DeleteReports(['ALL_Potencia'])\n    reports.CreateReport('ALL_Potencia',")
    ast.parse(resolver); (DEST/'scripts/resolver.py').write_text(resolver,encoding='utf-8')
    analysis=(SOURCE/'scripts/analisar.py').read_text(encoding='utf-8').replace(str(SOURCE).replace('\\','/'),str(DEST).replace('\\','/'))
    analysis=analysis.replace("old=Path('D:\\\\dev\\\\EMBRAER\\\\P2M19\\\\R01_16x2_88mm')","old=Path(cfg['referencia_comparacao'])")
    analysis=analysis.replace('R01: 16x2, 48 x 88 mm; nao convergido','R04: mesma geometria, seis passes; nao convergido').replace('R01 e candidato: conferir convergencia antes de atribuir diferencas pequenas a geometria.','Mesma geometria: comparacao de seis versus oito passes, preservando a malha.').replace('R01_88mm_nao_convergido','R04_seis_passes_nao_convergido')
    ast.parse(analysis); (DEST/'scripts/analisar.py').write_text(analysis,encoding='utf-8')
    runner=(HERE/'executar_estudo.ps1').read_text(encoding='utf-8')
    start=runner.index("    if(Test-Path -LiteralPath (Join-Path $casePath 'processo_criacao.json'))")
    end=runner.index("    Native 'resolver.py' 'centro'",start)
    runner=runner[:start]+"    if(Test-Path -LiteralPath (Join-Path $casePath 'processo_centro.json')){throw 'Continuacao ja iniciada; verificar antes de retomar'}\n    State 'CONTINUANDO_PASSES_7_E_8'\n"+runner[end:]
    (DEST/'scripts/continuar.ps1').write_text(runner,encoding='utf-8-sig')
    for name in ['resolver.py','analisar.py','continuar.ps1']: shutil.copy2(DEST/'scripts'/name,HERE/('continuacao8_'+name))
    print(json.dumps(dict(destino=str(DEST),arquivos_resultados_preservados=len(copied),bytes_resultados=sum(x['bytes'] for x in copied)),indent=2))
if __name__=='__main__': main()
