"""Acrescentar proveniencia da comparacao; nao recalcula nem altera numeros RF."""
from pathlib import Path
import json,hashlib
root=Path('D:/dev/EMBRAER/P2S13/R17_Flanges_Refletor/plano90')
cfg=json.loads((root/'configuracao.json').read_text());div=Path(cfg['divisor_reutilizado'])
for name,digest in cfg['fontes_divisor_sha256'].items():assert hashlib.sha256((div/name).read_bytes()).hexdigest()==digest
path=root/'circuito/resultado.json';r=json.loads(path.read_text())
r['divisor_reutilizado']=dict(pasta=str(div),sha256=cfg['fontes_divisor_sha256'],novo_solve=False)
r['escopo_comparacao']='Somente refletor lateral: mesmas PCBs, C02 e seis cabos de saida no circuito. Flanges, suportes, linguetas e duas novas entradas N-divisor do CAD R17 nao simulados.'
path.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
path=root/'circuito/verificacao_nexxim.json';r=json.loads(path.read_text());r['origem_divisor']='S8 C02 HFSS R16 preservado e reauditado; nenhum novo solve do divisor nesta comparacao'
path.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('PROVENIENCIA_R17_OK')
