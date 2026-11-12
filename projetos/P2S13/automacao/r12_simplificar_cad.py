"""Unir somente contatos do mesmo material; nao homogeneizar solda, Cu ou dielétricos distintos."""
from pathlib import Path
import json,hashlib
import FreeCAD as A,Part,Import
ROOT=Path('D:/dev/EMBRAER/P2S13/R12_Curvilinear_Simplificado');OUT=ROOT/'cad';OUT.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(n,v):(OUT/(n+'.json')).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
cfg=read(ROOT/'configuracao.json');srcdir=Path(cfg['fonte_integral']);man=read(srcdir/'cad/manifesto.json');rec=read(srcdir/'cad/folhas_solidas.json')
src=A.openDocument(str(srcdir/'P2S13_Radome.FCStd'));d=A.newDocument('P2S13_R12_Curvilinear')
original={};before_faces=0
for n,m in man.items():
    sh=src.getObject(n).Shape.copy();o=d.addObject('Part::Feature',n);o.Shape=sh
    o.addProperty('App::PropertyString','Material_nominal');o.Material_nominal=m
    original[n]=sh.copy();before_faces+=len(sh.Faces)
A.closeDocument(src.Name)
unions=[];affected=set()
for cell in ['R1','R2','R3']:
    for pol in ['A','B']:
        for a,b in [(cell+'_Vivo_'+pol,'D_Pino_'+cell+'_'+pol),(cell+'_Blindagem_'+pol,'D_Massa_'+cell+'_'+pol),(cell+'_PTFE_'+pol,'D_PTFE_'+cell+'_'+pol)]:
            assert man[a]==man[b] and a not in rec and b not in rec,(a,b)
            sa=d.getObject(a).Shape;sb=d.getObject(b).Shape
            dist=sa.distToShape(sb)[0];assert dist<1e-7,(a,b,dist)
            merged=sa.fuse(sb).removeSplitter();assert merged.isValid() and len(merged.Solids)==1,(a,b)
            diff=sa.cut(merged).Volume+sb.cut(merged).Volume+merged.cut(sa).cut(sb).Volume
            assert diff<1e-7,(a,b,diff)
            assert abs(merged.Volume-(sa.Volume+sb.Volume))<1e-6,(a,b,'volume')
            unions.append(dict(mantido=a,absorvido=b,material=man[a],distancia_original_mm=dist,diferenca_volume_mm3=diff,
                faces_antes=len(sa.Faces)+len(sb.Faces),faces_depois=len(merged.Faces),volume_mm3=merged.Volume))
            d.getObject(a).Shape=merged;d.removeObject(b);man.pop(b);affected.update([a,b])
unchanged={}
for n,old in original.items():
    if n in affected:continue
    new=d.getObject(n).Shape;diff=old.cut(new).Volume+new.cut(old).Volume
    assert diff<1e-8,n
    unchanged[n]=dict(diferenca_volume_mm3=diff,volume_mm3=new.Volume)
objects=[d.getObject(n) for n in man];bad=[]
for i,a in enumerate(objects):
    for b in objects[i+1:]:
        if any(min(getattr(a.Shape.BoundBox,k+'Max'),getattr(b.Shape.BoundBox,k+'Max'))-max(getattr(a.Shape.BoundBox,k+'Min'),getattr(b.Shape.BoundBox,k+'Min'))<=1e-6 for k in 'XYZ'):continue
        vol=a.Shape.common(b.Shape).Volume
        if vol>1e-7:bad.append(dict(a=a.Name,b=b.Name,volume_mm3=vol))
assert not bad,bad
assert len(man)==123 and len(unions)==18
d.recompute();native=ROOT/cfg['cad_native'];d.saveAs(str(native))
for material in sorted(set(man.values())):
    Import.export([d.getObject(n) for n,m in man.items() if m==material],str(OUT/(material+'.step')))
write('simplificacao',dict(aprovado=True,corpos_antes=len(original),corpos_depois=len(man),faces_antes=before_faces,
    faces_depois=sum(len(o.Shape.Faces) for o in objects),unioes=unions,objetos_inalterados=unchanged,
    aproximacao_fisica='Nenhuma: unioes de dominios contiguos com material identico; contornos externos preservados.'))
write('manifesto',man);write('folhas_solidas',rec);write('portas',cfg['portas'])
write('intersecoes',dict(aprovado=True,objetos=len(man),intersecoes=bad))
write('geometria_esperada',dict((n,dict(volume_mm3=d.getObject(n).Shape.Volume,
    bbox_mm=[getattr(d.getObject(n).Shape.BoundBox,k) for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax']])) for n in man))
cfg['solidos_fisicos']=len(man);(ROOT/'configuracao.json').write_text(json.dumps(cfg,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
A.closeDocument(d.Name);d=A.openDocument(str(native));assert all(d.getObject(n).Shape.isValid() for n in man)
write('reabertura',dict(validos=True,objetos=len(man),sha256=hashlib.sha256(native.read_bytes()).hexdigest()))
A.closeDocument(d.Name);print('R12_CAD_OK',len(man),'corpos',len(unions),'unioes')
