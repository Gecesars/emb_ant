"""Eliminar todo comprimento de cabo; reter somente as terminacoes soldadas locais."""
from pathlib import Path
import os,json,hashlib
import FreeCAD as A,Part,Import
ROOT=Path(os.environ['P2S13_ROOT']);cfg=json.loads((ROOT/'configuracao.json').read_text());REF=Path(cfg['fonte_CAD_preservado']);OUT=ROOT/'cad';OUT.mkdir(exist_ok=True)
src=A.openDocument(str(REF/'P2S13_Curvilinear.FCStd'));d=A.newDocument('R14_Antena_SemCabos');man={};records={};changes={};V=A.Vector
oldman=json.load(open(REF/'cad/manifesto.json'));oldrec=json.load(open(REF/'cad/folhas_solidas.json'));clip=Part.makeBox(1000,1000,1000,V(-500,-500,14.769))
for n,m in oldman.items():
    if n.startswith('D_') or n=='Radome_FR4_2mm':continue
    old=src.getObject(n).Shape;sh=old.copy();terminal=any(k in n for k in ['_Vivo_','_PTFE_','_Blindagem_'])
    if terminal:sh=sh.common(clip).removeSplitter()
    assert sh.isValid() and sh.Volume>0 and len(sh.Solids)==1,n
    o=d.addObject('Part::Feature',n);o.Shape=sh;o.addProperty('App::PropertyString','Material_nominal');o.Material_nominal=m;man[n]=m
    if n in oldrec:records[n]=oldrec[n]
    diff=old.cut(sh).Volume+sh.cut(old).Volume
    if not terminal:assert diff<1e-8,n
    changes[n]=dict(terminal_local=terminal,volume_removido_mm3=diff)
A.closeDocument(src.Name)
bad=[];objects=[d.getObject(n) for n in man]
for i,a in enumerate(objects):
    for b in objects[i+1:]:
        if any(min(getattr(a.Shape.BoundBox,k+'Max'),getattr(b.Shape.BoundBox,k+'Max'))-max(getattr(a.Shape.BoundBox,k+'Min'),getattr(b.Shape.BoundBox,k+'Min'))<=1e-6 for k in 'XYZ'):continue
        v=a.Shape.common(b.Shape).Volume
        if v>1e-7:bad.append(dict(a=a.Name,b=b.Name,volume_mm3=v))
assert not bad,bad
d.recompute();native=ROOT/cfg['cad_native'];d.saveAs(str(native))
for m in sorted(set(man.values())):Import.export([d.getObject(n) for n,mat in man.items() if mat==m],str(OUT/(m+'.step')))
geo={n:dict(volume_mm3=d.getObject(n).Shape.Volume,bbox_mm=[getattr(d.getObject(n).Shape.optimalBoundingBox(False,False),k) for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax']]) for n in man}
for name,data in [('manifesto',man),('folhas_solidas',records),('portas',cfg['portas']),('geometria_esperada',geo),('remocao_cabos',changes),('intersecoes',dict(aprovado=True,objetos=len(man),intersecoes=[]))]:
    (OUT/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
cfg['solidos_fisicos']=len(man);(ROOT/'configuracao.json').write_text(json.dumps(cfg,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
A.closeDocument(d.Name);d=A.openDocument(str(native));assert all(d.getObject(n).Shape.isValid() for n in man);A.closeDocument(d.Name)
(OUT/'reabertura.json').write_text(json.dumps(dict(aprovado=True,solidos=len(man),sha256=hashlib.sha256(native.read_bytes()).hexdigest()),indent=2)+'\n')
print('ANTENA_SEM_CABOS_OK',len(man))
