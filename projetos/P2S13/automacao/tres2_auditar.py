"""Confere topologia3xPCB2, fontes, execucao e preservacao das PCBs."""
from pathlib import Path
import json,hashlib,re
ROOT=Path('D:/dev/EMBRAER/P2S13/R05_Tres_Placas2');rows=[]
for p in sorted(ROOT.glob('t*/resultado.json')):
    folder=p.parent;r=json.loads(p.read_text());c=json.loads((folder/'configuracao.json').read_text())
    assert len(c['celulas'])==3 and all(x['radiadores']==2 for x in c['celulas']) and [x['x'] for x in c['celulas']]==[-96,0,96]
    assert all(x['fontes_sha256']==c['celulas'][0]['fontes_sha256'] for x in c['celulas'])
    for cell in c['celulas']:
        for n,h in cell['fontes_sha256'].items():assert hashlib.sha256((Path(cell['fonte'])/n).read_bytes()).hexdigest()==h
    cad=json.loads((folder/'cad/intersecoes.json').read_text());assert cad['aprovado'] and cad['celulas']==3 and not cad['intersecoes'] and cad['objetos']==c['solidos_fisicos']==88
    assert r['passes']<=6 and c['max_passes']==6 and c['max_delta_s']==.05 and not c['sweep']
    assert r['nucleos']==14 and r['frequencia_GHz']==5.17 and r['fase_graus']==0 and abs(r['potencia_por_porta_W']-1/6)<1e-12
    assert len(r['ordem_portas'])==6 and max(r['recomposicao'].values())<1e-7
    rec=json.loads((folder/'recursos_matriz.json').read_text());adap=[x for x in rec if x['passe_adaptativo'] is not None]
    assert [x['passe_adaptativo'] for x in adap]==list(range(1,r['passes']+1)) and all(x['nucleos']==14 for x in adap)
    assert r['major']==0 and r['verificacoes']['passividade'] and r['verificacoes']['eficiencia_e_balanco'] and r['cache_confere']
    raw=(folder/c['native']).read_text(errors='replace');src=re.findall(r'SourceEntry\([^\n]+',raw)
    assert len(src)==6 and all(abs(float(re.search("Magnitude='([0-9.e+-]+)W'",x)[1])-1/6)<1e-10 and "Phase='0deg'" in x for x in src)
    rows.append(dict(caso=folder.name,PCBs_identicas_SHA=True,centros_mm=[-96,0,96],CAD_sem_intersecoes=True,portas=6,potencia_por_porta_W=1/6,nucleos=14,passes=r['passes'],DeltaS=r['delta_s'],convergencia_S=r['convergiu'],estabilidade_campo=r['estavel_nove_sondas'],reciprocidade=r['verificacoes']['reciprocidade'],minor=r['minor'],major=r['major']))
assert rows
(ROOT/'auditoria_campanha.json').write_text(json.dumps(dict(escopo_e_execucao_conferidos=True,casos=rows,nota='Convergencia e metas RF avaliadas separadamente, sem aprovar por atingir o limite de passes.'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(rows,indent=2))
