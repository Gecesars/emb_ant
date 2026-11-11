"""Diagnostico somente numerico; nao altera S4 nem aplica outro solver."""
from pathlib import Path
import json
import numpy as np
import skrf as rf
ROOT=Path('D:/dev/EMBRAER/P2S13/R03_Continuacao_M00')
h=json.loads((ROOT/'historico_passes.json').read_text())['historico'];a,b=h[-2]['campos_dBi'],h[-1]['campos_dBi']
angles=[(0,90),(-50,90),(50,90),(-60,90),(60,90),(-8,0),(8,0),(-10,0),(10,0)]
points=[]
for i,(theta,phi) in enumerate(angles):
    title='P2S13_Campo_%02d'%i;points.append(dict(sonda=title,theta_graus=theta,phi_graus=phi,ganho7_dBi=a[title],ganho8_dBi=b[title],delta_dB=b[title]-a[title]))
n=rf.Network(str(ROOT/'centro.s4p'));s=n.s[0];sym=(s+s.T)/2;i,j=np.unravel_index(abs(s-s.T).argmax(),s.shape)
vs=lambda g:(1+abs(g))/(1-abs(g))
r=dict(sondas=points,maior_delta_sonda=max(points,key=lambda v:abs(v['delta_dB'])),par_reciprocidade=[n.port_names[i],n.port_names[j]],residuo_reciprocidade=float(abs(s-s.T).max()),limite_reciprocidade=1e-5,
    sensibilidade_VSWR_ativo_max_ao_simetrizar=float(abs(vs(s@np.ones(4))-vs(sym@np.ones(4))).max()),
    escopo='Somente diagnostico algebrico de sensibilidade. S4 original mantido, nao simetrizado na entrega. Nao estima erro FEM completo nem relaxa a auditoria.')
(ROOT/'diagnostico_numerico.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(r,indent=2))
