"""Confere hashes dos artefatos no disco e no índice Git, antes do commit."""
from pathlib import Path
import argparse,hashlib,json,subprocess
REPO=Path(__file__).resolve().parents[3]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pacote',default='centro_16x2_88mm')
args=parser.parse_args()
OUT=(REPO/'projetos/P2M19'/args.pacote).resolve()
assert OUT.is_relative_to(REPO/'projetos/P2M19'),OUT
manifest=json.loads((OUT/'manifesto.json').read_text())
total=0
for entry in manifest:
    p=OUT/entry['arquivo'];raw=p.read_bytes()
    assert p.resolve().is_relative_to(OUT),p
    assert len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256'],p
    relative=p.relative_to(REPO).as_posix()
    indexed=subprocess.check_output(['git','show',':'+relative],cwd=REPO)
    assert indexed==raw,relative
    total+=len(raw)
staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=REPO).decode().split('\0')
staged=[n for n in staged if n]
assert staged and all(n in ['README.md','.gitattributes'] or n.startswith('projetos/P2M19/') for n in staged)
for name in staged:
    low=name.lower()
    assert not any(s in low for s in ['.aedtresults/','.g3derr','.aedt.lock','.ngmesh','.profile','__pycache__']),name
print(json.dumps(dict(arquivos_manifesto=len(manifest),bytes_manifesto=total,
    arquivos_staged=len(staged),bytes_git_conferidos=True,sem_malhas=True),indent=2))
