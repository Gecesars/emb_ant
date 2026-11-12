"""Renderizacao local. Nao declara revisao visual automaticamente."""
import os,json,hashlib
from pathlib import Path
import fitz
root=Path(os.environ['P2S13_ROOT']);p=root/'Relatorio_R11_C08_Radome.pdf'
doc=fitz.open(p);assert len(doc)==5
out=root/'revisao_pdf';out.mkdir(exist_ok=True)
pages=[]
for i,page in enumerate(doc):
    words=page.get_text('words');assert len(words)>20,(i,len(words))
    bad=[w for w in words if w[0]<0 or w[1]<0 or w[2]>page.rect.width+.01 or w[3]>page.rect.height+.01]
    assert not bad,(i,bad)
    image=out/('pagina_%02d.png'%(i+1));page.get_pixmap(matrix=fitz.Matrix(1.6,1.6)).save(image)
    pages.append(dict(pagina=i+1,palavras=len(words),imagem=str(image)))
(out/'render.json').write_text(json.dumps(dict(pdf_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),paginas=pages,revisao_visual='PENDENTE'),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps(dict(pdf=str(p),paginas=len(doc),revisao_visual='PENDENTE')))
