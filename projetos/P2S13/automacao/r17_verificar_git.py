"""Comparar os artefatos preparados com o indice Git ou um commit especifico."""
from pathlib import Path
import hashlib,json,subprocess,sys,ast
repo=Path('D:/dev/EMBRAER/emb_ant');prefix=sys.argv[1] if len(sys.argv)>1 else ''
records=json.loads((repo/'projetos/P2S13/mecanica_R17/manifesto_arquivos.json').read_text())
p=subprocess.Popen(['git','cat-file','--batch'],cwd=repo,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
errors=[]
for row in records:
    spec=prefix+':'+row['arquivo'];p.stdin.write((spec+'\n').encode());p.stdin.flush();head=p.stdout.readline().decode().strip()
    if head.endswith(' missing'):errors.append((row['arquivo'],'missing'));continue
    n=int(head.split()[-1]);data=p.stdout.read(n);assert p.stdout.read(1)==b'\n'
    digest=hashlib.sha256(data).hexdigest()
    if digest!=row['sha256']:errors.append((row['arquivo'],'different'))
p.stdin.close();p.wait()
for f in (repo/'projetos/P2S13/automacao').glob('r17_*.py'):ast.parse(f.read_text(encoding='utf-8-sig'),str(f))
print(json.dumps(dict(artefatos=len(records),bytes=sum(r['bytes'] for r in records),erros=errors,referencia=prefix or 'index'),indent=2))
assert not errors
