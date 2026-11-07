"""Quantificar efeito do refinamento local com a mesma rede HFSS nos dois casos."""
import argparse, json
from pathlib import Path
import numpy as np
from circuito import Circuit

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path)
args=parser.parse_args();root=args.root
baseline=Circuit(root,antenna_folder=root/'antena_malha_inicial')
final=Circuit(root)
a,theta,ca,_=baseline.calculate();b,_,cb,_=final.calculate()
delta={k:float(b[k]-a[k]) for k in ['ganho_frontal_realizado_dBi','abertura_H_graus','abertura_V_graus']}
delta['VSWR_ativo_AB']=[y-x for x,y in zip(a['VSWR_ativo_AB'],b['VSWR_ativo_AB'])]
delta['VSWR_outro_porto_casado_AB']=[y-x for x,y in zip(a['VSWR_outro_porto_casado_AB'],b['VSWR_outro_porto_casado_AB'])]
delta['S_antena_max']=float(np.max(abs(final.parts['ANT']['s']-baseline.parts['ANT']['s'])))
for axis,lim in [('H',60),('V',4)]:
    mask=abs(theta)<=lim
    delta['corte_'+axis+'_max_dB']=float(np.max(abs(cb[axis][mask]-ca[axis][mask])))
mesh=json.loads((root/'antena/malha.json').read_text())
stable=(abs(delta['ganho_frontal_realizado_dBi'])<=.05 and abs(delta['abertura_H_graus'])<=.5
        and abs(delta['abertura_V_graus'])<=.1 and max(abs(x) for x in delta['VSWR_ativo_AB'])<=.05
        and max(abs(x) for x in delta['VSWR_outro_porto_casado_AB'])<=.05)
result=dict(inicial=a,refinada=b,diferencas=delta,reparo_major_final=mesh['reparos_major'],
            estabilidade_local_aprovada=bool(stable and mesh['reparos_major']==0),
            limites_comparacao=dict(ganho_dB=.05,H_graus=.5,V_graus=.1,VSWR=.05))
(root/'circuito/comparacao_malhas.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(result,indent=2))
assert result['estabilidade_local_aprovada'],'Rever efeito de malha e/ou reparo geometrico antes do aceite.'
