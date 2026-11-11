"""Arquiva continuacao de oito passes sem resultados volumetricos nem malhas."""
from pathlib import Path
import json,hashlib,shutil
REPO=Path(__file__).resolve().parents[3];ROOT=Path('D:/dev/EMBRAER/P2S13/R03_Continuacao_M00');OUT=REPO/'projetos/P2S13/continuacao_placa2';OUT.mkdir(exist_ok=True);records=[]
cfg=json.loads((ROOT/'configuracao.json').read_text());assert not (ROOT/(cfg['native']+'.lock')).exists()
assert json.loads((ROOT/'continuidade_auditada.json').read_text())['aprovado']
def copy(p):
    assert p.is_file(),p
    assert not any(q.lower().endswith('.aedtresults') for q in p.parts)
    assert p.suffix.lower() not in ['.g3d','.g3derr','.lock','.fld','.ngmesh']
    d=OUT/p.relative_to(ROOT);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d);h=hashlib.sha256(p.read_bytes()).hexdigest();assert hashlib.sha256(d.read_bytes()).hexdigest()==h
    records.append(dict(arquivo=d.relative_to(REPO).as_posix(),fonte=str(p),sha256=h,bytes=p.stat().st_size))
for n in [cfg['native'],cfg['cad_native'],'HFSS_14nucleos.acf','configuracao.json','origem.json','antes_convergencia.txt','preparacao_auditada.json','continuidade_auditada.json','qualificacao.json','entrega.json','resultado.json','diagnostico_numerico.json','comparacao.json','comparacao.csv','comparacao_HV.png','convergencia.txt','historico_passes.json','recursos_matriz.json','ordem_fontes.json','mensagens.json','malha.json','malha_inicial.json','diagramas_HV.png','polar_HV.png','centro.s4p']:
    copy(ROOT/n)
for p in ROOT.glob('*.csv'):
    if p.stem.startswith(('ALL_','POL_','R1_','R2_')):copy(p)
for p in (ROOT/'cad').glob('*.json'):copy(p)
(OUT/'manifesto.json').write_text(json.dumps(dict(artefatos=records,total_bytes=sum(e['bytes'] for e in records),excluidos='aedtresults, malhas, g3derr, campos volumetricos, locks. Referencia6 preservada na revisao anterior.'),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps(dict(artefatos=len(records),bytes=sum(e['bytes'] for e in records))))
