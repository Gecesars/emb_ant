"""Preserva a R05 e prepara apenas os passes 9/10, sem reconstruir a malha."""
from pathlib import Path
import json,shutil,hashlib,ast
SOURCE=Path('D:/dev/EMBRAER/P2M19/R05_72mm_ref146_8passes')
DEST=Path('D:/dev/EMBRAER/P2M19/R06_72mm_ref146_10passes')
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sub(text,old,new):
    assert old in text,old
    return text.replace(old,new)
def main():
    assert not DEST.exists(),'Continuacao existente: inspecionar, nao duplicar.'
    cfg=json.loads((SOURCE/'configuracao.json').read_text(encoding='utf-8'))
    h=json.loads((SOURCE/'historico_passes.json').read_text(encoding='utf-8'))
    assert len(h['historico'])==8 and h['historico'][-1]['tetraedros']==834197
    assert sha(SOURCE/cfg['native'])=='29ecf853bae4d91cdb0b6b4d98edee175621c9689b8ce842daeca29190a25100'
    assert not (SOURCE/(cfg['native']+'.lock')).exists()
    DEST.mkdir();(DEST/'scripts').mkdir();(DEST/'evidencias').mkdir()
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
        shutil.copy2(SOURCE/name,DEST/'evidencias'/('referencia8_'+name))
    cfg.update(revisao='P2M19_R06_72mm_ref146_10passes',max_passes=10,min_passes=10,
      referencia_comparacao=str(SOURCE),continuacao=dict(passes_preservados=8,passes_adicionais=2,
      nativo_referencia_sha256=sha(SOURCE/cfg['native']),geometria_inalterada=True),
      controle_comparacao='Mesma geometria de 72/146 mm; somente passes 9 e 10, preservando malha e cache.')
    (DEST/'configuracao.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    resolver=(SOURCE/'scripts/resolver.py').read_text(encoding='utf-8')
    edits=[(SOURCE.as_posix(),DEST.as_posix()),
      ("['MaximumPasses=6','MaxDeltaS=0.05','MinimumPasses=2'","['MaximumPasses=8','MaxDeltaS=0.05','MinimumPasses=8'"),
      ("'MinimumPasses:=',8,'MaximumPasses:=',8","'MinimumPasses:=',10,'MaximumPasses:=',10"),
      ("analysis.replace('MaximumPasses=6','MaximumPasses=8').replace('MinimumPasses=2','MinimumPasses=8')","analysis.replace('MaximumPasses=8','MaximumPasses=10').replace('MinimumPasses=8','MinimumPasses=10')"),
      ('maximum_passes=8,minimum_passes=8','maximum_passes=10,minimum_passes=10'),
      ('malha_origem_passes=6,malha_origem_tetraedros=602282','malha_origem_passes=8,malha_origem_tetraedros=834197'),
      ('max_passes=8,passes_adicionais=2','max_passes=10,passes_adicionais=2'),
      ('CONTINUAR7_8','CONTINUAR9_10')]
    for a,b in edits:resolver=sub(resolver,a,b)
    ast.parse(resolver);(DEST/'scripts/resolver.py').write_text(resolver,encoding='utf-8')
    analysis=(SOURCE/'scripts/analisar.py').read_text(encoding='utf-8')
    for a,b in [(SOURCE.as_posix(),DEST.as_posix()),('R04: mesma geometria, seis passes; nao convergido','R05: mesma geometria, oito passes; nao convergido'),('comparacao de seis versus oito passes','comparacao de oito versus dez passes'),('R04_seis_passes_nao_convergido','R05_oito_passes_nao_convergido')]:analysis=sub(analysis,a,b)
    ast.parse(analysis);(DEST/'scripts/analisar.py').write_text(analysis,encoding='utf-8')
    runner=(SOURCE/'scripts/continuar.ps1').read_text(encoding='utf-8-sig').replace('CONTINUANDO_PASSES_7_E_8','CONTINUANDO_PASSES_9_E_10')
    (DEST/'scripts/continuar.ps1').write_text(runner,encoding='utf-8-sig')
    for name in ['resolver.py','analisar.py','continuar.ps1']:shutil.copy2(DEST/'scripts'/name,HERE/('continuacao10_'+name))
    print(json.dumps(dict(destino=str(DEST),arquivos_resultados=len(records),bytes_resultados=sum(x['bytes'] for x in records)),indent=2))
if __name__=='__main__':main()
