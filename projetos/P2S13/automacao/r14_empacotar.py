"""Arquivar somente engenharia compacta do C09, sem resultados volumetricos."""
from pathlib import Path
import json,shutil,hashlib,datetime
ROOT=Path('D:/dev/EMBRAER/P2S13/R14_Compacto_Simetrico_SemRadome/c00')
REPO=Path(__file__).resolve().parents[3]
DEST=REPO/'projetos/P2S13/compacto_c09/c00'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert read(ROOT/'circuito/verificacao_nexxim.json')['matriz_conferida']
assert not read(ROOT/'circuito/resultado.json')['nexxim_pendente']
assert (ROOT/'README.md').exists()
sources=[ROOT/p for p in ['README.md','configuracao.json','cabos.json','igualdade_cabos.json','HFSS_14nucleos.acf','P2S13_Compacto_SemRadome.FCStd']]
for folder in ['antena','divisor']:
    for pat in ['*.aedt','*.FCStd','*.s*p','*.csv','*.json','*.txt','*.acf','*.png']:
        sources.extend((ROOT/folder).glob(pat))
    sources.extend((ROOT/folder/'cad').glob('*.json'))
sources.extend((ROOT/'cad').glob('*.json'))
for pat in ['*.aedt','*.aedtz','*.s*p','*.csv','*.json','*.png']:
    sources.extend((ROOT/'circuito').glob(pat))
for pat in ['*.FCStd','*.png']:sources.extend((ROOT/'visual').glob(pat))
records=[]
for p in sorted(set(sources)):
    assert p.is_file(),p
    rel=p.relative_to(ROOT)
    assert not any(x.endswith('.aedtresults') for x in rel.parts)
    assert p.suffix.lower() not in ['.lock','.g3derr','.fld','.field','.ngmesh','.profile','.log','.fcbak']
    out=DEST/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
    source=hashlib.sha256(p.read_bytes()).hexdigest();assert hashlib.sha256(out.read_bytes()).hexdigest()==source
    records.append(dict(arquivo=str(rel).replace('\\','/'),bytes=p.stat().st_size,sha256=source))
manifest=dict(data=datetime.datetime.now().astimezone().isoformat(),origem=str(ROOT),estado=read(ROOT/'circuito/resultado.json').get('qualificado'),
    conteudo='HFSS separado sem malhas, Nexxim com Touchstones, campos distantes, CAD mecanico e auditorias. Nativo HFSS integral com cabos excluido.',arquivos=records)
(DEST/'manifesto.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps(dict(destino=str(DEST),arquivos=len(records),bytes=sum(x['bytes'] for x in records)),indent=2))
