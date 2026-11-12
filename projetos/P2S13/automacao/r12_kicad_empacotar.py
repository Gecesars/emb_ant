"""Empacota os Gerbers M00 e o manifesto do conjunto 3xM00 + C08."""
from pathlib import Path
import json,hashlib,zipfile,datetime
R=Path(__file__).resolve().parents[3];O=R/'projetos/P2S13/kicad/conjunto_R12';P=O/'placa2_M00'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert read(P/'verificacao.json')['aprovado_geometria']
assert read(P/'verificacao_gerbers.json')['aprovado']
assert read(O/'conferencia_CAD_conjunto.json')['aprovado_geometria_CAD']
files=[p for p in sorted((P/'gerbers').iterdir()) if p.is_file()]+[P/'FABRICACAO.txt']
zip_path=P/'M00_Gerbers_PARA_REVISAO_RF.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.name)
with zipfile.ZipFile(zip_path) as z:
 assert z.testzip() is None
 for p in files:assert hashlib.sha256(z.read(p.name)).hexdigest()==sha(p)
items=[]
for p in sorted(O.rglob('*')):
 if not p.is_file() or p.name in ['manifesto.json'] or p.suffix in ['.kicad_prl','.lck']:continue
 assert not any(x in str(p).lower() for x in ['aedtresults','.lock','.g3derr'])
 items.append(dict(arquivo=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
record=dict(data=datetime.datetime.now().astimezone().isoformat(),revisao='Conjunto R12: 3xM00 + 1xC08',
 liberacao_RF=False,geometria_preservada=True,placas_por_antena={'M00':3,'C08':1},
 nota='Sem alteracao RF; M00 com cobre de parede PTH35um, C08 com18um. Confirmacao de processo e qualificacao RF separadas.',arquivos=items)
(O/'manifesto.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Pacote M00:',zip_path,'Manifesto:',len(items),'arquivos,',sum(x['bytes'] for x in items),'bytes')
