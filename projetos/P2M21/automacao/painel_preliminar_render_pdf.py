"""Renderiza todas as paginas; contato para revisao visual humana, sem aprovar sozinho."""
from pathlib import Path
import fitz
from PIL import Image,ImageDraw
root=Path('D:/dev/EMBRAER/P2M21/R18_Mecanica_Preliminar')
out=root/'revisao_pdf';out.mkdir(exist_ok=True)
imgs=[]
for p in sorted(root.glob('*.pdf')):
    d=fitz.open(p);print(p.name,len(d),'paginas')
    for i,page in enumerate(d):
        f=out/(p.stem+'_%02d.png'%(i+1));page.get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(f);imgs.append(f)
        spans=[s for b in page.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans']]
        assert all(s['bbox'][0]>=0 and s['bbox'][2]<=page.rect.width+1 and s['bbox'][1]>=0 and s['bbox'][3]<=page.rect.height+1 for s in spans)
for k in range(0,len(imgs),4):
    c=Image.new('RGB',(1200,1700),'#cccccc')
    for j,f in enumerate(imgs[k:k+4]):
        im=Image.open(f);im.thumbnail((580,800));c.paste(im,(10+(j%2)*600,30+(j//2)*850))
        ImageDraw.Draw(c).text((10+(j%2)*600,10+(j//2)*850),f.name,fill='black')
    c.save(out/('contato_%02d.jpg'%(k//4+1)))
