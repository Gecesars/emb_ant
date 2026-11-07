"""Consolidar DRC e hashes das tres placas preservadas e cotadas."""
import argparse, collections, hashlib, json
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path)
args=parser.parse_args();repo=Path(__file__).resolve().parents[2]
result={}
for board in ['P1H_Coluna_10','R02_Inferior','R02_Superior']:
    path=args.root/'fabricacao'/(board+'.json');drc=json.loads(path.read_text(encoding='utf8'))
    errors=[v for v in drc['violations'] if v['severity']=='error']
    assert not errors and not drc['unconnected_items']
    warnings=collections.Counter(v['type'] for v in drc['violations'])
    if board=='P1H_Coluna_10':assert set(warnings)=={'solder_mask_bridge'}
    else:assert not warnings
    pcb=repo/'kicad'/board/(board+'.kicad_pcb')
    gerbers=list((repo/'fabricacao').rglob('Gerber_'+board+'.zip'));assert len(gerbers)==1
    result[board]=dict(erros=0,nao_conectados=0,avisos=dict(warnings),data=drc['date'],
        versao=drc['kicad_version'],pcb=str(pcb.relative_to(repo)),
        pcb_sha256=hashlib.sha256(pcb.read_bytes()).hexdigest(),
        gerber=str(gerbers[0].relative_to(repo)),gerber_sha256=hashlib.sha256(gerbers[0].read_bytes()).hexdigest())
result['nota']='As aberturas amplas de mascara nos radiadores RF geram avisos de ponte de mascara. Nao foram suprimidos. Nenhum erro eletrico ou item desconectado no DRC; nenhuma placa foi alterada por esta verificacao.'
(args.root/'fabricacao/verificacao.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(result,indent=2))
