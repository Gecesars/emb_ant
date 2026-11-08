"""Sintese inicial dos divisores radiais; exige validacao EM posterior."""
import json,sys
from pathlib import Path
repo=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(repo/'automacao/r02'))
from radiais import layout
root=Path('D:/dev/EMBRAER/P2M21/R00_Concepcao')
for n in (4,8):
    dest=root/f'divisor_1x{n}'
    g=layout(n,dest,'ZYF300CA-C')
    g.update(arquivo=f'P2M21_Duplo_1x{n}',legenda=f'P2M21 2 x 1:{n}',
      montagem_furos=[[-17,-36],[17,-36],[-17,36],[17,36]],
      estado='SINTETIZADO_NAO_VALIDADO_EM')
    (dest/'geometria.json').write_text(json.dumps(g,indent=2),encoding='utf8')
    print(n,g['width'],g['l_arm'],len(g['ports']))
