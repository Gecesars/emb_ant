"""Checkpoint de concepcao: whitelist explicita, sem resultados volumetricos ou malhas."""
import json,hashlib,shutil
from pathlib import Path
repo=Path(__file__).resolve().parents[3];dest=repo/'projetos/P2M21';root=Path('D:/dev/EMBRAER/P2M21/R00_Concepcao')
items=[]
def copy(src,rel):
    target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True)
    data=src.read_bytes();target.write_bytes(data)
    sha=hashlib.sha256(data).hexdigest()
    assert hashlib.sha256(target.read_bytes()).hexdigest()==sha
    assert hashlib.sha256(src.read_bytes()).hexdigest()==sha,'Fonte mudou durante copia: '+str(src)
    items.append(dict(arquivo=str(rel).replace('\\','/'),bytes=len(data),sha256=sha,fonte=str(src)))
for name in ['configuracao.json','rede.json','mapa_conexoes.csv']:
    copy(root/name,Path(name))
for folder in ['planejamento','imagens']:
    for p in (root/folder).iterdir():
        if p.suffix in ('.json','.csv','.png'):copy(p,Path(folder)/p.name)
for p in (root/'mecanica').iterdir():
    if p.suffix in ('.FCStd','.step','.dxf') or p.name=='parametros.json':copy(p,Path('freecad')/p.name)
for p in (root/'kicad').rglob('*'):
    if p.is_file() and (p.suffix in ('.kicad_pcb','.kicad_pro') or p.name=='drc.json'):
        copy(p,Path('kicad')/p.relative_to(root/'kicad'))
for folder in ['antena','divisor_1x4','divisor_1x8']:
    src=root/folder
    for p in src.iterdir():
        if p.suffix in ('.aedt','.FCStd') or p.name in ('hfss_validacao.json','geometria.json','analise.json','malha.json'):
            copy(p,Path('hfss')/folder/p.name)
    for p in (src/'cad').iterdir():
        if p.suffix in ('.step','.json'):copy(p,Path('hfss')/folder/'cad'/p.name)
# Estado do primeiro estudo e resultados pequenos, quando efetivamente existentes.
if (root/'qualificacao.json').exists():copy(root/'qualificacao.json',Path('qualificacao.json'))
for p in root.glob('diagnostico_*.json'):copy(p,Path(p.name))
if (root/'antena/convergencia.txt').exists():copy(root/'antena/convergencia.txt',Path('hfss/antena/convergencia.txt'))
for p in root.glob('divisor_1x*/convergencia.txt'):copy(p,Path('hfss')/p.parent.name/p.name)
for p in root.glob('divisor_1x*/*.s*p'):copy(p,Path('hfss')/p.parent.name/p.name)
(dest/'manifesto.json').write_text(json.dumps(dict(estado='CONCEPCAO_NAO_QUALIFICADA_RF',arquivos=items),indent=2),encoding='utf8')
print('PACOTE',len(items),sum(v['bytes'] for v in items))
