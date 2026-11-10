"""Nativos e evidencias do conjunto4+2; exclui todas as malhas."""
from pathlib import Path
import json,hashlib,shutil
REPO=Path(__file__).resolve().parents[3];ROOT=Path('D:/dev/EMBRAER/P2S13/R01_Seis_Elementos');OUT=REPO/'projetos/P2S13/seis_elementos';OUT.mkdir(exist_ok=True);records=[]
def copy(src,dst):
    assert src.is_file(),src
    assert not any(x.lower().endswith('.aedtresults') for x in src.parts)
    assert src.suffix.lower() not in ['.g3derr','.g3d','.ngmesh','.lock','.fld']
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);h=hashlib.sha256(src.read_bytes()).hexdigest();assert hashlib.sha256(dst.read_bytes()).hexdigest()==h
    records.append(dict(arquivo=dst.relative_to(REPO).as_posix(),fonte=str(src),sha256=h,bytes=src.stat().st_size))
for n in ['requisitos.json','qualificacao.json','montagem_6elementos.png','comparacao.json','comparacao.csv','comparacao_HV.png']:copy(ROOT/n,OUT/n)
src=ROOT/'celula2_simetrica';dest=OUT/'celula2_simetrica'
for n in ['geometria.json','simetria.json','conectividade.json','radiadores_conferidos.json','2_elementos_simetrica.FCStd','layout.png','criar_cad.py']:copy(src/n,dest/n)
for f in (src/'cad').iterdir():
    if f.is_file() and f.suffix.lower() in ['.json','.step']:copy(f,dest/'cad'/f.name)
for p in sorted(ROOT.glob('s*/resultado.json')):
    src=p.parent;dest=OUT/src.name;c=json.loads((src/'configuracao.json').read_text());assert not (src/(c['native']+'.lock')).exists()
    for n in ['configuracao.json','resultado.json','qualificacao.json','historico_passes.json','convergencia.txt','centro.s4p','recursos_matriz.json','mensagens.json','malha.json','malha_inicial.json','geracao_malha.json','mensagens_malha.json','estatisticas_malha_inicial.txt','hfss_validacao.json','ordem_fontes.json','diagramas_HV.png','polar_HV.png','contribuicoes_placas.json','HFSS_14nucleos.acf',c['native'],c['cad_native']]:copy(src/n,dest/n)
    for f in src.glob('*.csv'):
        if f.stem.startswith(('ALL_','POL_','R1_','R2_')):copy(f,dest/f.name)
    if (src/'conferencia_reconstrucao.json').exists():copy(src/'conferencia_reconstrucao.json',dest/'conferencia_reconstrucao.json')
    for f in (src/'cad').iterdir():
        if f.is_file() and f.suffix.lower()=='.json':copy(f,dest/'cad'/f.name)
(OUT/'manifesto.json').write_text(json.dumps(dict(artefatos=records,total_bytes=sum(x['bytes'] for x in records),excluidos='Malhas/aedtresults/campos volumetricos/g3d/g3derr/locks. Modelos nativos conservam geometria; a solucao FEM completa permanece local.'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(arquivos=len(records),bytes=sum(x['bytes'] for x in records))))
