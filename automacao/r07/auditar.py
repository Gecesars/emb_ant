"""Auditoria R07, criterios explicitamente pedidos: seis passes e DeltaS0.02."""
import sys,json,re,hashlib,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'r06'))
from auditar_convergencia import audit

def main(root):
    folder=root/'antena';native=folder/'PCB_R07.aedt'
    raw=native.read_text(encoding='latin1')
    assert re.search(r'MaximumPasses=6\s',raw)
    assert re.search(r'MaxDeltaS=0\.02\s',raw)
    config=json.loads((folder/'configuracao_hfss.json').read_text())
    assert hashlib.sha256(Path(config['fonte']).read_bytes()).hexdigest()==config['sha256_fonte']
    result=audit(native,write=False,max_delta_s=.02,max_delta_campo=.02)
    result['s_002_dois_passes']=result.pop('s_008_dois_passes')
    result['campo_002dB_nove_direcoes_dois_passes']=result.pop('campo_005dB_nove_direcoes_dois_passes')
    (folder/'auditoria_convergencia.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k!='historico'},indent=2))
    assert result['convergencia_aprovada'],'Sem convergencia real dentro dos seis passes; nao aprovar por limite.'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);main(p.parse_args().root)
