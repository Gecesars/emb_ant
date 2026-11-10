"""Clona a solucao R14 completa e preserva prova dos seis passes. Sem solve."""
from pathlib import Path
import json,shutil,hashlib
SOURCE=Path('D:/dev/EMBRAER/P2M21/R14_Oito_Celulas')
ROOT=Path('D:/dev/EMBRAER/P2M21/R15_Oito_Celulas_8passes')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not ROOT.exists(),'Continuacao ja preparada; nao duplicar'
cfg=json.loads((SOURCE/'configuracao.json').read_text())
assert not (SOURCE/(cfg['native']+'.lock')).exists()
assert json.loads((SOURCE/'resultado.json').read_text())['passes']==6
ROOT.mkdir();ref=ROOT/'referencia6';ref.mkdir()
static=[cfg['native'],'configuracao.json','HFSS_14nucleos.acf','P2M21_8celulas.FCStd','estimativa_H.csv','estimativa_V.csv']
for name in static:shutil.copy2(SOURCE/name,ROOT/name)
baseline=[cfg['native'],'configuracao.json','convergencia.txt','resultado.json','historico_passes.json','malha.json','centro.s16p','polar_HV.png']+[p.name for p in SOURCE.glob('*.csv')]
for name in set(baseline):shutil.copy2(SOURCE/name,ref/name)
results=Path(cfg['native']).with_suffix('.aedtresults')
shutil.copytree(SOURCE/results,ROOT/results)
entries=[]
for p in (SOURCE/results).rglob('*'):
    if p.is_file():
        rel=p.relative_to(SOURCE);digest=sha(p);assert sha(ROOT/rel)==digest
        entries.append(dict(arquivo=rel.as_posix(),bytes=p.stat().st_size,sha256=digest))
cfg.update(revisao='R15_Oito_Celulas_8passes',max_passes=8,min_passes=8,passes_iniciais=6,passes_adicionais_autorizados=2,fonte_continuacao=str(SOURCE))
(ROOT/'configuracao.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name,data in [('origem.json',dict(fonte=str(SOURCE),native_sha256=sha(SOURCE/cfg['native']),arquivos_resultados_copiados=entries)),('qualificacao.json',dict(estado='COPIA_PRONTA_AGUARDA_CONFIGURACAO'))]:
    (ROOT/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
print('COPIA_CONFIRMADA',len(entries),sum(e['bytes'] for e in entries))
