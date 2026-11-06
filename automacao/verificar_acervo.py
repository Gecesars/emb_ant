"""Confira os arquivos que serão compartilhados. Execute após git add."""
from pathlib import Path
import re
import subprocess
import zipfile

repo = Path(__file__).resolve().parents[1]
items = subprocess.check_output(["git","ls-files","-z"], cwd=repo).decode().split("\0")
files = [repo / name for name in items if name]
assert files
for file in files:
    rel = file.relative_to(repo).as_posix().lower()
    assert not re.search(r"\.aedtresults(?:/|$)|\.aedb/|(?:^|/)(?:__pycache__|verificacao_malha)/|\.(?:msh|mesh|ngmesh|asol\w*|fld|field|profile|log|tmp|lock|aedtz|bak|pyc|raw|kicad_prl|fcstd1)$", rel), rel
    assert file.stat().st_size < 50 * 1024**2, rel
    if file.suffix.lower() == ".zip":
        assert "gerber" in file.name.lower(), rel
        with zipfile.ZipFile(file) as archive:
            names = archive.namelist()
            assert archive.testzip() is None, rel
            assert any(n.endswith(".drl") for n in names), rel
            assert all(Path(n).suffix.lower() in {".gbp",".gtp",".gtl",".gbl",".gts",".gbs",".gto",".gbo",".gbrjob",".gm1",".gbr",".drl"} for n in names), (rel,names)
    if file.suffix.lower() == ".fcstd":
        with zipfile.ZipFile(file) as archive:
            assert "Document.xml" in archive.namelist() and archive.testzip() is None, rel
    if file.suffix.lower() == ".md":
        for link in re.findall(r"\]\(([^)\n]+)\)",file.read_text(encoding="utf-8-sig")):
            if not link.startswith(("https://","http://","#")):
                assert (file.parent / link).resolve().exists(), (rel,link)
size=sum(f.stat().st_size for f in files)/1024**2
print(f"{len(files)} arquivos rastreados; {size:.1f} MiB; links e arquivos de fabricação íntegros.")
