"""Audita GenerateMesh por retorno, mensagens e estatisticas de todas as superficies."""
from pathlib import Path
import argparse,json,re,hashlib,sys,shutil
p=argparse.ArgumentParser();p.add_argument('pasta',type=Path);a=p.parse_args();root=a.pasta
c=json.loads((root/'configuracao.json').read_text());result=json.loads((root/'geracao_malha.json').read_text());messages=json.loads((root/'mensagens_malha.json').read_text())
assert result['retorno']==0 and any('Normal completion' in m for m in messages)
assert not any(re.search(r'\[(warning|error)\]',m,re.I) for m in messages),messages
files=list((root/Path(c['native']).with_suffix('.aedtresults')).rglob('initial.stats'));assert files
contents=[f.read_bytes() for f in files];assert len(set(contents))==1
stats=contents[0].decode();rows=[];has_recovery='RecoveredPlanarArea' in stats.splitlines()[0]
for line in stats.splitlines():
    if '|' not in line:continue
    q=[x.strip() for x in line.split('|')]
    try:bid=int(q[0]);tet=int(q[1])
    except ValueError:continue
    if bid==0:continue # tetraedros de fundo, nao um corpo fisico adicional
    rows.append(dict(body_id=bid,tetraedros=tet,planar_percent=float(q[2]) if has_recovery else None,curva_percent=float(q[3]) if has_recovery else None))
expected=c.get('solidos_fisicos',83)+1
assert len(rows)==expected and len({x['body_id'] for x in rows})==expected
assert all(x['tetraedros']>0 for x in rows)
if has_recovery:assert all(x['planar_percent']==x['curva_percent']==100 for x in rows)
else:assert c.get('mesh_method')=='AnsoftClassic' and not c.get('tau_flex',False)
err=list(root.rglob('nominalmesh.g3derr'))
if err:
    sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'automacao/r06'))
    from auditar_malha import audit
    report=audit(root);assert report['reparos_major']==report['reparos_minor']==0
else:report=dict(reparos_major=0,reparos_minor=0,origem='GenerateMesh concluiu, mensagens sem warning/error, estatisticas completas dos %d corpos. Nao foi gerado nominalmesh.g3derr. Classic estrito nao exporta colunas de area recuperada.'%expected,arquivo_avisos_presente=False)
report.update(tempo_s=result['tempo_s'],corpos=len(rows),recuperacao_percentual_exportada=has_recovery,todos_recuperados_100_percent=True if has_recovery else None,tetraedros=int(re.search(r'NumTotalTets (\d+)',stats)[1]),estatisticas_sha256=hashlib.sha256(contents[0]).hexdigest(),corpos_estatisticas=rows)
(root/'estatisticas_malha_inicial.txt').write_bytes(contents[0]);(root/'malha_inicial.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='corpos_estatisticas'},indent=2))
