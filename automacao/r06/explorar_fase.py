"""Estudo de fase ideal em 5.17 GHz; nao muda a montagem nem aprova candidatos."""
import argparse,csv,functools,json
from pathlib import Path
import numpy as np
import circuito

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path)
root=parser.parse_args().root
circuito.read=functools.lru_cache(maxsize=10)(circuito.read)
circuito.read_pattern=functools.lru_cache(maxsize=80)(circuito.read_pattern)
rows=[]
for trunk in np.arange(128.,136.001,.25):
    for branch in np.arange(133.,137.001,.25):
        c=circuito.Circuit(root,antenna_folder=root/'antena_malha_inicial',lengths=(290,trunk,branch))
        active=abs(c.Sout@np.ones(2));matched=abs(np.diag(c.Sout))
        va=(1+active)/(1-active);vm=(1+matched)/(1-matched)
        rows.append(dict(tronco_mm=float(trunk),ramal_mm=float(branch),
            VSWR_ativo_max=float(max(va)),VSWR_individual_max=float(max(vm)),
            total_coax_mm=float(580+4*trunk+20*branch)))
out=root/'estudo_fase';out.mkdir(exist_ok=True)
with (out/'grade.csv').open('w',newline='',encoding='utf8') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
candidates=sorted([r for r in rows if max(r['VSWR_ativo_max'],r['VSWR_individual_max'])<1.4],key=lambda r:(r['total_coax_mm'],r['VSWR_individual_max']))
result=dict(estado='EXPLORATORIO: PCB inicial; exige geometria de cabos realizavel, malha PCB refinada e Nexxim.',candidatos=[])
selected=candidates[:5] or sorted(rows,key=lambda r:max(r['VSWR_ativo_max'],r['VSWR_individual_max']))[:5]
for r in selected:
    c=circuito.Circuit(root,antenna_folder=root/'antena_malha_inicial',lengths=(290,r['tronco_mm'],r['ramal_mm']))
    metrics=c.calculate()[0];result['candidatos'].append(metrics)
(out/'candidatos.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(result,indent=2))
