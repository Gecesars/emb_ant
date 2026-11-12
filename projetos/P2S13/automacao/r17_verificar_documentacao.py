"""Checagens de arquivos e registro explicito de revisao visual ja realizada."""
from pathlib import Path
import json,hashlib,fitz,ezdxf,sys
r=Path('D:/dev/EMBRAER/P2S13/R17_Flanges_Refletor/documentacao')
pdfs={f.name:dict(paginas=len(fitz.open(f)),sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in r.glob('*.pdf')}
assert sorted(x['paginas'] for x in pdfs.values())==[5,7]
checks=[]
for f in r.glob('*.dxf'):
    d=ezdxf.readfile(f);circles=[e for e in d.modelspace() if e.dxftype()=='CIRCLE' and e.dxf.layer=='CORTE']
    assert d.units==4 and not d.audit().errors
    checks.append(dict(arquivo=f.name,unidades_mm=True,erros=0,circulos_corte=len(circles)))
    assert len(circles)==(26 if f.stem=='Refletor_planificado' else 3)
(r/'verificacao_DXF.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
if '--revisao-visual-confirmada' in sys.argv:
    out=dict(aprovado=True,data='2026-11-12',pdfs=pdfs,paginas_revisadas=12,
      metodo='Todas as paginas renderizadas e inspecionadas; apos detalhar grampos, apenas A3 pagina4 mudou e foi revisada ampliada. Onze renders restantes identicos por SHA256.',
      ressalva='Revisao visual e dimensional, sem liberacao RF, estrutural ou IP.')
    (r/'revisao_visual.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(pdfs=pdfs,DXF=checks),indent=2))
