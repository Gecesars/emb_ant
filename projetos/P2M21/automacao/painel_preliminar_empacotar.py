"""Pacote R18 apos revisao visual: nativos e documentos, sem resultados FEM."""
from pathlib import Path
import json,hashlib,shutil
WORK=Path('D:/dev/EMBRAER/P2M21/R18_Mecanica_Preliminar')
REPO=Path(__file__).resolve().parents[3]
DEST=REPO/'projetos/P2M21/mecanica_preliminar_R18'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    qa=json.loads((WORK/'revisao_visual.json').read_text())
    assert qa['aprovado'] and all(sha(WORK/r['arquivo'])==r['sha256'] for r in qa['arquivos'])
    v=json.loads((WORK/'verificacao_cad.json').read_text())
    assert v['solidos_validos'] and not v['intersecoes'] and v['geometria_celulas_preservada']==410 and v['reaberto']
    manifest=[]
    def copy(src,dst):
        assert src.is_file() and src.stat().st_size<100*1024**2
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert sha(src)==sha(dst)
        manifest.append(dict(arquivo=dst.relative_to(DEST).as_posix(),origem=str(src),bytes=src.stat().st_size,sha256=sha(src)))
    patterns=['*.FCStd','*.step','*.dxf','*.pdf','lista_materiais*.csv','furacao*.csv']
    files=set(p for pat in patterns for p in WORK.glob(pat))
    files.update(WORK/n for n in ['README.md','dimensoes.json','cores.json','verificacao_cad.json','lista_materiais.json','revisao_visual.json'])
    for p in sorted(files):copy(p,DEST/p.name)
    for p in sorted((WORK/'imagens').glob('*.png')):copy(p,DEST/'imagens'/p.name)
    copy(Path('D:/dev/EMBRAER/82-6784.stp'),DEST/'referencias/82-6784.stp')
    for n in ['fontes.json','estado.json']:copy(WORK/n,DEST/n)
    (DEST/'manifesto.json').write_text(json.dumps(dict(estado='PRELIMINAR',arquivos=manifest,malhas_incluidas=False,campos_volumetricos_incluidos=False),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    prohibited=[p for p in DEST.rglob('*') if p.is_file() and (p.suffix in ['.lock','.g3derr','.adp','.ngmesh','.bak'] or '.aedtresults' in str(p))]
    assert not prohibited,prohibited
    print('R18_PACOTE_VERIFICADO',len(manifest),sum(x['bytes'] for x in manifest))
if __name__=='__main__':main()
