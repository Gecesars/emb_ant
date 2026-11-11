"""Auditoria de escopo e execucao da campanha, sem exigir metas RF para arquivar falhas."""
from pathlib import Path
import hashlib,json,re
ROOT=Path('D:/dev/EMBRAER/P2S13/R04_Dobras_Ajustadas');SRC=Path('D:/dev/EMBRAER/P2S13/R03_Continuacao_M00')
ref=json.loads((SRC/'configuracao.json').read_text());old=json.loads((SRC/'continuidade_auditada.json').read_text())
assert hashlib.sha256((SRC/ref['native']).read_bytes()).hexdigest()==old['native_sha256']
keys=['celulas','portas','refletor_comprimento_mm','refletor_desenvolvido_largura_mm','espessura_mm','raio_interno_mm','K_dobra','passo_vertical_mm','nucleo_z_mm','potencia_por_porta_W','fase_graus','nucleos','frequencia_GHz','sweep','percent_refinement','basis_order']
rows=[]
for p in sorted(ROOT.glob('d*/resultado.json')):
    folder=p.parent;r=json.loads(p.read_text());c=json.loads((folder/'configuracao.json').read_text())
    assert all(c[k]==ref[k] for k in keys)
    for cell in c['celulas']:
        for n,h in cell['fontes_sha256'].items():assert hashlib.sha256((Path(cell['fonte'])/n).read_bytes()).hexdigest()==h,(cell['nome'],n)
    cad=json.loads((folder/'cad/intersecoes.json').read_text());assert cad['aprovado'] and not cad['intersecoes'] and cad['objetos']==c['solidos_fisicos']
    assert r['passes']<=6 and c['max_passes']==6 and c['min_passes']==2 and c['max_delta_s']==.05
    assert r['nucleos']==14 and r['frequencia_GHz']==5.17 and r['fase_graus']==0 and r['potencia_por_porta_W']==.25
    raw=(folder/c['native']).read_text(errors='replace');src=re.findall(r'SourceEntry\([^\n]+',raw)
    assert len(src)==4 and all("Magnitude='0.25W'" in s and "Phase='0deg'" in s for s in src)
    assert 'MaximumPasses=6' in raw and 'DoLambdaRefine=false' in raw
    rec=json.loads((folder/'recursos_matriz.json').read_text());adap=[x for x in rec if x['passe_adaptativo'] is not None]
    assert [x['passe_adaptativo'] for x in adap]==list(range(1,r['passes']+1)) and all(x['nucleos']==14 for x in adap)
    assert r['major']==0 and r['verificacoes']['passividade'] and r['verificacoes']['eficiencia_e_balanco'] and r['cache_confere']
    assert max(r['recomposicao'].values())<1e-7
    rows.append(dict(caso=folder.name,passes=r['passes'],nucleos=14,excitacoes='4x0.25W/0deg',componentes_preservados=True,fonte_SHA_conferida=True,CAD_sem_intersecoes=True,major=r['major'],minor=r['minor'],convergencia_S=r['convergiu'],reciprocidade_ok=r['verificacoes']['reciprocidade'],campos_estaveis=r['estavel_nove_sondas']))
expected=3 if (ROOT/'interrupcao.json').exists() else 4
assert len(rows)==expected,'Esperar os casos previstos antes da auditoria final'
out=dict(escopo_e_execucao_conferidos=True,referencia8passes_preservada=True,casos=rows,nota='Esta auditoria confere execucao e escopo. Convergencia, estabilidade e metas RF permanecem separadas.')
(ROOT/'auditoria_campanha.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps(out,indent=2))
