"""Preserva R05 e copia sua solucao final para executar somente passes7/8."""
from pathlib import Path
import json,shutil,hashlib
SOURCE=Path('D:/dev/EMBRAER/P2S13/R05_Tres_Placas2/t04_b28p5_a150')
ROOT=Path('D:/dev/EMBRAER/P2S13/R06_Continuacao_Tres2')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()
assert not ROOT.exists(),'Continuacao existente; nao duplicar'
cfg=json.loads((SOURCE/'configuracao.json').read_text());r=json.loads((SOURCE/'resultado.json').read_text())
assert r['passes']==6 and cfg['max_passes']==6 and len(cfg['portas'])==6
assert cfg['inicio_dobra_y_mm']==28.5 and cfg['angulo_dobra_graus']==150 and cfg['nucleos']==14 and not cfg['sweep']
assert not (SOURCE/(cfg['native']+'.lock')).exists()
ROOT.mkdir();ref=ROOT/'referencia6';ref.mkdir()
for n in [cfg['native'],cfg['cad_native'],'configuracao.json','HFSS_14nucleos.acf','malha_inicial.json','geracao_malha.json','hfss_validacao.json','conferencia_reconstrucao.json','estatisticas_malha_inicial.txt']:
    shutil.copy2(SOURCE/n,ROOT/n)
shutil.copytree(SOURCE/'cad',ROOT/'cad')
baseline=[cfg['native'],'configuracao.json','convergencia.txt','resultado.json','historico_passes.json','recursos_matriz.json','malha.json','centro.s6p','polar_HV.png']+[p.name for p in SOURCE.glob('*.csv')]
refs=[]
for n in sorted(set(baseline)):
    shutil.copy2(SOURCE/n,ref/n);assert sha(SOURCE/n)==sha(ref/n);refs.append(dict(arquivo=n,sha256=sha(ref/n)))
results=Path(cfg['native']).with_suffix('.aedtresults');entries=[]
shutil.copytree(SOURCE/results,ROOT/results)
for p in (SOURCE/results).rglob('*'):
    if p.is_file():
        rel=p.relative_to(SOURCE);h=sha(p);assert sha(ROOT/rel)==h
        entries.append(dict(arquivo=rel.as_posix(),bytes=p.stat().st_size,sha256=h))
cfg.update(revisao='t04_b28p5_a150_continuacao8',max_passes=8,min_passes=8,passes_iniciais=6,passes_adicionais_autorizados=2,fonte_continuacao=str(SOURCE),referencia_continuacao=str(ref))
(ROOT/'configuracao.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for n,d in [('origem.json',dict(fonte=str(SOURCE),native_sha256=sha(SOURCE/cfg['native']),referencias=refs,arquivos_resultados_copiados=entries)),('qualificacao.json',dict(estado='COPIA_PRONTA_AGUARDA_CONFIGURACAO'))]:
    (ROOT/n).write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(arquivos_resultados_copiados=len(entries),bytes=sum(e['bytes'] for e in entries),malha_preservada=True)))
