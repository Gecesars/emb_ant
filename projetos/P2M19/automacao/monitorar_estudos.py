"""Monitor compacto da fila; leitura somente, sem conectar ao AEDT."""
from pathlib import Path
from datetime import datetime
import json,sys
import psutil
sys.path.insert(0,'D:/dev/EMBRAER/emb_ant/projetos/P2M21/automacao')
from oito_celulas_monitorar import progress
WORK=Path('D:/dev/EMBRAER/P2M19')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
out=dict(agora=datetime.now().isoformat(),memoria_livre_GiB=round(psutil.virtual_memory().available/2**30,2))
p=WORK/'Campanha_72mm_20261113/estado.json'
if p.exists():out['fila']=read(p)
out['casos']=[]
for name in ['R02_16x2_72mm','R03_72mm_ref162','R04_72mm_ref146']:
    root=WORK/name;row=dict(caso=name)
    if (root/'pipeline.json').exists():row['pipeline']=read(root/'pipeline.json')
    cfg=read(root/'configuracao.json')
    if (root/cfg['native']).exists():
        try:
            hist=progress(root).get('historico',[])
            row['ultimo_passe']=({k:hist[-1][k] for k in ['passe','tetraedros','delta_s','delta_campo_max_dB']} | dict(G0_dBi=hist[-1]['campos_dBi'].get('P2M19_Campo_00'))) if hist else None
        except Exception as e:row['metadados_em_atualizacao']=str(e)
    out['casos'].append(row)
print(json.dumps(out,ensure_ascii=False,indent=2))
