"""Snapshot somente leitura da campanha; nao inicia nem altera solves."""
from pathlib import Path
import sys,json
REPO=Path(__file__).resolve().parents[3];sys.path.insert(0,str(REPO/'projetos/P2M21/automacao'))
from oito_celulas_monitorar import progress
ROOT=Path('D:/dev/EMBRAER/P2S13/R04_Dobras_Ajustadas');rows=[]
for p in sorted(ROOT.glob('d*/configuracao.json')):
    folder=p.parent;c=json.loads(p.read_text());row=dict(caso=folder.name)
    if (folder/'resultado.json').exists():
        r=json.loads((folder/'resultado.json').read_text());row.update(estado='CONCLUIDO',passes=r['passes'],DeltaS=r['delta_s'],G=r['cortes']['H']['ganho_frontal_dBi'],H=r['cortes']['H']['abertura_graus'],VSWR=max(r['VSWR_ativo']+r['VSWR_casado']),convergiu=r['convergiu'])
    else:
        row['estado']=json.loads((folder/'qualificacao.json').read_text())['estado']
        if (folder/c['native']).exists():
            h=progress(folder).get('historico',[])
            if h:row.update(passe_concluido=h[-1]['passe'],DeltaS=h[-1]['delta_s'],G_monitor=h[-1]['campos_dBi'].get('P2S13_Campo_00'))
    rows.append(row)
print(json.dumps(rows,ensure_ascii=False,indent=2))
