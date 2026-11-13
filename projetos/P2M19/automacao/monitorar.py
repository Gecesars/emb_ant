"""Monitor read-only; não conecta ao solver nem altera resultados."""
from pathlib import Path
import sys,json,datetime
ROOT=Path('D:/dev/EMBRAER/P2M19/R01_16x2_88mm')
sys.path.insert(0,'D:/dev/EMBRAER/emb_ant/projetos/P2M21/automacao')
from oito_celulas_monitorar import progress
out=dict(agora=datetime.datetime.now().isoformat())
for n in ['pipeline.json','qualificacao.json','processo_criacao.json','processo_centro.json']:
    p=ROOT/n
    if p.exists():out[n]=json.loads(p.read_text(encoding='utf-8-sig'))
if (ROOT/'P2M19_16x2_88mm.aedt').exists():
    p=progress(ROOT);p['historico']=p.get('historico',[])[-2:];out['adaptacao']=p
print(json.dumps(out,indent=2,ensure_ascii=False))
