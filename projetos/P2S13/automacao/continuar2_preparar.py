"""Copia solucao m00 de seis passes para continuacao exata 7/8; sem solver."""
from pathlib import Path
import json,shutil,hashlib
SOURCE=Path('D:/dev/EMBRAER/P2S13/R02_Casamento_Placa2/m00')
ROOT=Path('D:/dev/EMBRAER/P2S13/R03_Continuacao_M00')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not ROOT.exists(),'Continuacao ja preparada; nao duplicar'
cfg=json.loads((SOURCE/'configuracao.json').read_text());result=json.loads((SOURCE/'resultado.json').read_text())
assert result['passes']==6 and cfg['max_passes']==6
assert not (SOURCE/(cfg['native']+'.lock')).exists()
ROOT.mkdir();ref=ROOT/'referencia6';ref.mkdir()
static=[cfg['native'],cfg['cad_native'],'configuracao.json','HFSS_14nucleos.acf','malha_inicial.json','geracao_malha.json','hfss_validacao.json','conferencia_reconstrucao.json','estatisticas_malha_inicial.txt']
for name in static:shutil.copy2(SOURCE/name,ROOT/name)
shutil.copytree(SOURCE/'cad',ROOT/'cad')
baseline=[cfg['native'],'configuracao.json','convergencia.txt','resultado.json','historico_passes.json','recursos_matriz.json','malha.json','centro.s4p','polar_HV.png','casamento.json']+[p.name for p in SOURCE.glob('*.csv')]
refs=[]
for name in sorted(set(baseline)):
    shutil.copy2(SOURCE/name,ref/name);assert sha(SOURCE/name)==sha(ref/name)
    refs.append(dict(arquivo=name,sha256=sha(ref/name)))
results=Path(cfg['native']).with_suffix('.aedtresults');shutil.copytree(SOURCE/results,ROOT/results);entries=[]
for p in (SOURCE/results).rglob('*'):
    if p.is_file():
        rel=p.relative_to(SOURCE);h=sha(p);assert sha(ROOT/rel)==h
        entries.append(dict(arquivo=rel.as_posix(),bytes=p.stat().st_size,sha256=h))
cfg.update(revisao='m00_continuacao8',max_passes=8,min_passes=8,passes_iniciais=6,passes_adicionais_autorizados=2,fonte_continuacao=str(SOURCE),referencia_continuacao=str(ref))
(ROOT/'configuracao.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name,data in [('origem.json',dict(fonte=str(SOURCE),native_sha256=sha(SOURCE/cfg['native']),referencias=refs,arquivos_resultados_copiados=entries)),('qualificacao.json',dict(estado='COPIA_PRONTA_AGUARDA_CONFIGURACAO'))]:
    (ROOT/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(arquivos_resultados_copiados=len(entries),bytes=sum(e['bytes'] for e in entries),malha_preservada=True)))
