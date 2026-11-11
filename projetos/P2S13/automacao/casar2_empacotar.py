"""Empacota candidatos finalizados de casamento PCB2, sem malhas ou locks."""
from pathlib import Path
import json,hashlib,shutil
REPO=Path(__file__).resolve().parents[3];ROOT=Path('D:/dev/EMBRAER/P2S13/R02_Casamento_Placa2');OUT=REPO/'projetos/P2S13/casamento_placa2';OUT.mkdir(exist_ok=True);records=[]
def copy(src,dst):
    assert src.is_file(),src
    assert not any(p.lower().endswith('.aedtresults') for p in src.parts)
    assert src.suffix.lower() not in ['.g3derr','.g3d','.ngmesh','.lock','.fld']
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);sha=hashlib.sha256(src.read_bytes()).hexdigest();assert hashlib.sha256(dst.read_bytes()).hexdigest()==sha
    records.append(dict(arquivo=dst.relative_to(REPO).as_posix(),fonte=str(src),sha256=sha,bytes=src.stat().st_size))
for n in ['requisitos.json','qualificacao.json','comparacao.json','comparacao.csv','comparacao_HV.png']:copy(ROOT/n,OUT/n)
for f in ROOT.glob('estimativa*.json'):copy(f,OUT/f.name)
for p in sorted(ROOT.glob('m*/resultado.json')):
    src=p.parent;dest=OUT/src.name;c=json.loads((src/'configuracao.json').read_text());assert not (src/(c['native']+'.lock')).exists()
    for n in ['configuracao.json','resultado.json','casamento.json','qualificacao.json','historico_passes.json','convergencia.txt','centro.s4p','recursos_matriz.json','mensagens.json','malha.json','malha_inicial.json','geracao_malha.json','mensagens_malha.json','estatisticas_malha_inicial.txt','hfss_validacao.json','ordem_fontes.json','diagramas_HV.png','polar_HV.png','HFSS_14nucleos.acf',c['native'],c['cad_native'],'conferencia_reconstrucao.json']:copy(src/n,dest/n)
    for f in src.glob('*.csv'):
        if f.stem.startswith(('ALL_','POL_','R1_','R2_')):copy(f,dest/f.name)
    for f in (src/'cad').glob('*.json'):copy(f,dest/'cad'/f.name)
    for f in (src/'placa2').iterdir():
        if f.is_file() and f.suffix in ['.json','.py','.FCStd','.png']:copy(f,dest/'placa2'/f.name)
    for f in (src/'placa2/cad').glob('*.json'):copy(f,dest/'placa2/cad'/f.name)
(OUT/'manifesto.json').write_text(json.dumps(dict(artefatos=records,total_bytes=sum(r['bytes'] for r in records),excluidos='Malhas, aedtresults, g3derr, locks, campos volumetricos. Solucao FEM completa permanece local.'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(artefatos=len(records),bytes=sum(r['bytes'] for r in records))))
