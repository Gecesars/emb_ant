"""Prepare uma cópia local para execução, preservando os arquivos versionados."""
import argparse
import json
from pathlib import Path
from shutil import copy2, copytree

base = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("destino", type=Path, help="pasta nova ou vazia, fora do checkout")
args = parser.parse_args()
dest = args.destino.resolve()
if dest.is_relative_to(base.parent) or (dest.exists() and (not dest.is_dir() or any(dest.iterdir()))):
    parser.error("Escolha uma pasta vazia fora do repositório.")
copytree(base / "P1H", dest, dirs_exist_ok=True)
for working, tracked in json.loads((base / "arquivos.json").read_text(encoding="utf8")).items():
    target = dest / working
    target.parent.mkdir(parents=True, exist_ok=True)
    copy2(base.parent / tracked, target)
print(dest)
