"""Continua a R06 por dois passes e guarda cortes completos no passe 11."""
from pathlib import Path
import json,shutil,hashlib,ast
SOURCE=Path('D:/dev/EMBRAER/P2M19/R06_72mm_ref146_10passes')
DEST=Path('D:/dev/EMBRAER/P2M19/R07_72mm_ref146_12passes')
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sub(text,old,new):
    assert old in text,old
    return text.replace(old,new)
def main():
    assert not DEST.exists(),'Continuacao existente: verificar antes de repetir.'
    cfg=json.loads((SOURCE/'configuracao.json').read_text(encoding='utf-8'))
    h=json.loads((SOURCE/'historico_passes.json').read_text(encoding='utf-8'))
    assert len(h['historico'])==10 and h['historico'][-1]['tetraedros']==1163077
    assert sha(SOURCE/cfg['native'])=='d946068b6f4e0e7530f74cb7ada1961e1b00c50e98bd7952003f15060031c888'
    assert not (SOURCE/(cfg['native']+'.lock')).exists()
    DEST.mkdir();(DEST/'scripts').mkdir();(DEST/'evidencias').mkdir();(DEST/'passe11').mkdir()
    for name in [cfg['native'],cfg['cad_native'],'HFSS_14nucleos.acf','geometria_importada.json','hfss_validacao.json']:
        shutil.copy2(SOURCE/name,DEST/name)
    for name in ['cad',Path(cfg['native']).with_suffix('.aedtresults').name]:shutil.copytree(SOURCE/name,DEST/name)
    records=[]
    for p in (SOURCE/Path(cfg['native']).with_suffix('.aedtresults')).rglob('*'):
        if p.is_file():
            rel=p.relative_to(SOURCE);digest=sha(p);assert sha(DEST/rel)==digest
            records.append(dict(arquivo=str(rel),bytes=p.stat().st_size,sha256=digest))
    (DEST/'evidencias/copia_resultados_local.json').write_text(json.dumps(records,indent=2))
    for name in ['historico_passes.json','resultado.json','convergencia.txt']:
        shutil.copy2(SOURCE/name,DEST/'evidencias'/('referencia10_'+name))
    cfg.update(revisao='P2M19_R07_72mm_ref146_12passes',max_passes=12,min_passes=12,
      referencia_comparacao=str(SOURCE),continuacao=dict(passes_preservados=10,passes_adicionais=2,
      nativo_referencia_sha256=sha(SOURCE/cfg['native']),geometria_inalterada=True,checkpoint_cortes_passe11=True),
      controle_comparacao='Mesma geometria de 72/146 mm; somente passes 11 e 12, preservando malha e cache.')
    cfg['observacao']='Somente 5,17 GHz, 16 portas diretas iguais/em fase, 1 W total; sem rede externa, cabos, conectores N, radome ou suportes plasticos. Ganho total; nao e qualificacao MIMO por entrada.'
    (DEST/'configuracao.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    cp_cfg=dict(cfg);cp_cfg.update(max_passes=11,min_passes=11,revisao=cfg['revisao']+'_checkpoint11')
    (DEST/'passe11/configuracao.json').write_text(json.dumps(cp_cfg,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
    resolver=(SOURCE/'scripts/resolver.py').read_text(encoding='utf-8')
    edits=[(SOURCE.as_posix(),DEST.as_posix()),('datetime,re,hashlib','datetime,re,hashlib,shutil'),
      ("['MaximumPasses=8','MaxDeltaS=0.05','MinimumPasses=8'","['MaximumPasses=10','MaxDeltaS=0.05','MinimumPasses=10'"),
      ("'MinimumPasses:=',10,'MaximumPasses:=',10","'MinimumPasses:=',11,'MaximumPasses:=',11"),
      ("analysis.replace('MaximumPasses=8','MaximumPasses=10').replace('MinimumPasses=8','MinimumPasses=10')","analysis.replace('MaximumPasses=10','MaximumPasses=11').replace('MinimumPasses=10','MinimumPasses=11')"),
      ('maximum_passes=10,minimum_passes=10','maximum_passes=11,minimum_passes=11'),
      ('malha_origem_passes=8,malha_origem_tetraedros=834197','malha_origem_passes=10,malha_origem_tetraedros=1163077'),
      ('max_passes=10,passes_adicionais=2','max_passes=12,passes_adicionais=2'),
      ('CONTINUAR9_10','CONTINUAR11_12')]
    for a,b in edits:resolver=sub(resolver,a,b)
    checkpoint="""    d.Analyze('Centro')
    # Guardar o passe 11 antes de a solucao seguinte substituir LastAdaptive.
    checkpoint=os.path.join(root,'passe11')
    d.ExportConvergence('Centro','',os.path.join(checkpoint,'convergencia.txt'))
    conv11=open(os.path.join(checkpoint,'convergencia.txt')).read()
    assert int(re.search(r'Completed\\s*:\\s*(\\d+)',conv11).group(1))==11
    errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2));assert not errors,errors
    write('passe11/mensagens.json',list(oDesktop.GetMessages(p.GetName(),d.GetName(),0)))
    sol.ExportNetworkData('',['Centro : LastAdaptive'],3,os.path.join(checkpoint,'centro.s16p'),['All'],True,50,'S',-1,1,15,False,True,False)
    reports=d.GetModule('ReportSetup')
    for name in ['ALL_H','ALL_V','ALL_H_fino','ALL_V_fino','ALL_Potencia']:
        assert name in list(reports.GetAllReportNames()),name
        reports.ExportToFile(name,os.path.join(checkpoint,name+'.csv'),False)
    expressions=['RadiatedPower','AcceptedPower','IncidentPower','RadiationEfficiency','SystemEfficiency']
    data=reports.GetSolutionDataPerVariation('Antenna Parameters','Centro : LastAdaptive',['Context:=','Potencia'],['Freq:=',['All']],expressions)
    write('passe11/potencia.json',dict((q,dict(real=list(data[0].GetRealDataValues(q)),units=data[0].GetDataUnits(q))) for q in expressions))
    p.Save();oDesktop.CloseProject(p.GetName())
    before12=open(native).read()
    assert block(before12,'AnalysisSetup')==expected
    shutil.copy2(native,os.path.join(checkpoint,cfg['native']))
    results=os.path.splitext(native)[0]+'.aedtresults'
    for folder,dirs,files in os.walk(results):
        for name in files:
            if name.endswith(('.EMConvData','.ExprCache','.profile')):
                src=os.path.join(folder,name);rel=os.path.relpath(src,root);dst=os.path.join(checkpoint,rel)
                parent=os.path.dirname(dst)
                if not os.path.exists(parent):os.makedirs(parent)
                shutil.copy2(src,dst)
    assert os.path.isfile(os.path.join(checkpoint,'configuracao.json'))
    from System.IO import File
    from System.Security.Cryptography import SHA256
    from System import BitConverter
    digest=BitConverter.ToString(SHA256.Create().ComputeHash(File.ReadAllBytes(native))).Replace('-','').ToLower()
    write('passe11/snapshot.json',dict(passe=11,nativo_sha256=digest,fontes_iguais_em_fase=True))
    log('PASSE11_EXPORTADO_RETORNO_PASSE12')
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign(cfg['design'])
    d.GetModule('AnalysisSetup').EditSetup('Centro',['NAME:Centro','MinimumPasses:=',12,'MaximumPasses:=',12])
    p.Save();oDesktop.CloseProject(p.GetName())
    after12=open(native).read()
    expected12=expected.replace('MaximumPasses=11','MaximumPasses=12').replace('MinimumPasses=11','MinimumPasses=12')
    assert block(after12,'AnalysisSetup')==expected12
    for name in ['GeometryCore','Materials','BoundarySetup','MeshSetup','RadField']:
        assert block(before12,name)==block(after12,name),name
    assert re.findall(r'TraceID=(\\d+)',analysis)==re.findall(r'TraceID=(\\d+)',block(after12,'AnalysisSetup'))
    write('evidencias/retomada12_confirmada.json',dict(maximum_passes=12,minimum_passes=12,somente_min_max_alterados=True,cache_preservado=True))
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign(cfg['design']);sol=d.GetModule('Solutions')
    assert not list(d.GetModule('AnalysisSetup').GetSweeps('Centro'))
    sources(sol,ports)
    assert oDesktop.GetRegistryString('Desktop/ActiveDSOConfigurations/HFSS')=='P2M19_14nucleos'
    d.Analyze('Centro')
    d.ExportConvergence('Centro','',os.path.join(root,'convergencia.txt'))"""
    resolver=sub(resolver,"    d.Analyze('Centro')\n    d.ExportConvergence('Centro','',os.path.join(root,'convergencia.txt'))",checkpoint)
    ast.parse(resolver);(DEST/'scripts/resolver.py').write_text(resolver,encoding='utf-8')
    analysis=(SOURCE/'scripts/analisar.py').read_text(encoding='utf-8')
    for a,b in [(SOURCE.as_posix(),DEST.as_posix()),('R05: mesma geometria, oito passes; nao convergido','R06: mesma geometria, dez passes; DeltaS atendido'),('comparacao de oito versus dez passes','comparacao de dez versus doze passes'),('R05_oito_passes_nao_convergido','R06_dez_passes_deltaS_atendido')]:analysis=sub(analysis,a,b)
    analysis=analysis.replace('.read_text()',".read_text(encoding='utf-8-sig')")
    ast.parse(analysis);(DEST/'scripts/analisar.py').write_text(analysis,encoding='utf-8')
    runner=(SOURCE/'scripts/continuar.ps1').read_text(encoding='utf-8-sig').replace('CONTINUANDO_PASSES_9_E_10','CONTINUANDO_PASSES_11_E_12')
    (DEST/'scripts/continuar.ps1').write_text(runner,encoding='utf-8-sig')
    for name in ['resolver.py','analisar.py','continuar.ps1']:shutil.copy2(DEST/'scripts'/name,HERE/('continuacao12_'+name))
    print(json.dumps(dict(destino=str(DEST),arquivos_resultados=len(records),bytes_resultados=sum(x['bytes'] for x in records)),indent=2))
if __name__=='__main__':main()
