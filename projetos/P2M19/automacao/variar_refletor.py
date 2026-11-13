"""FreeCAD headless: varia apenas o refletor, preservando as oito PCBs."""
from pathlib import Path
import hashlib,json,shutil
import FreeCAD as A,Part,Import

def run(source_root,target_root):
    source_root=Path(source_root);root=Path(target_root);out=root/'cad';out.mkdir(exist_ok=True)
    cfg=json.loads((root/'configuracao.json').read_text())
    source_cfg=json.loads((source_root/'configuracao.json').read_text())
    assert cfg['celulas']==source_cfg['celulas'] and cfg['portas']==source_cfg['portas']
    assert not (root/cfg['cad_native']).exists()
    doc=A.openDocument(str(source_root/source_cfg['cad_native']))
    manifest=json.loads((source_root/'cad/manifesto.json').read_text())
    original=json.loads((source_root/'cad/geometria_esperada.json').read_text())
    before={n:(doc.getObject(n).Shape.Volume,doc.getObject(n).Shape.Area,len(doc.getObject(n).Shape.Faces)) for n in manifest if n!='Refletor_Al2mm'}
    rw,rh,rt=cfg['refletor_mm'];z=cfg['refletor_topo_z_mm']
    shape=Part.makeBox(rh,rw,rt,A.Vector(-rh/2,-rw/2,z-rt))
    for p in cfg['portas']:shape=shape.cut(Part.makeCylinder(2.1,rt,A.Vector(p['x'],p['y'],z-rt)))
    assert shape.isValid() and len(shape.Solids)==1
    ref=doc.getObject('Refletor_Al2mm');ref.Shape=shape
    intersections=[]
    for n in before:
        other=doc.getObject(n).Shape
        assert before[n]==(other.Volume,other.Area,len(other.Faces))
        a,b=shape.BoundBox,other.BoundBox
        if all(min(getattr(a,k+'Max'),getattr(b,k+'Max'))-max(getattr(a,k+'Min'),getattr(b,k+'Min'))>1e-6 for k in 'XYZ'):
            common=shape.common(other).Volume
            if common>1e-7:intersections.append(dict(a='Refletor_Al2mm',b=n,volume_mm3=common))
    assert not intersections
    doc.Label=cfg['design'];doc.recompute();doc.saveAs(str(root/cfg['cad_native']))
    geo={n:dict(volume_mm3=doc.getObject(n).Shape.Volume,bbox_mm=[getattr(doc.getObject(n).Shape.optimalBoundingBox(False,False),k) for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax']]) for n in manifest}
    assert all(abs(geo[n]['volume_mm3']-original[n]['volume_mm3'])<1e-7 and
        max(abs(x-y) for x,y in zip(geo[n]['bbox_mm'],original[n]['bbox_mm']))<1e-7 for n in before)
    for filename in ['manifesto.json','folhas_solidas.json','portas.json','contatos_portas.json']:
        shutil.copy2(source_root/'cad'/filename,out/filename)
    for material in sorted(set(manifest.values())):
        if material=='AL5052':Import.export([ref],str(out/'AL5052.step'))
        else:
            src=source_root/'cad'/(material+'.step');dst=out/(material+'.step')
            shutil.copy2(src,dst);assert src.read_bytes()==dst.read_bytes()
    source_audit=json.loads((source_root/'cad/intersecoes.json').read_text())
    assert source_audit['aprovado']
    audit=dict(aprovado=True,objetos=len(manifest),intersecoes=[],
        metodo='328 solidos e posicoes preservados; somente refletor alterado e verificado contra todos os demais.',
        fonte_sem_intersecoes=str(source_root/'cad/intersecoes.json'),
        fonte_auditoria_sha256=hashlib.sha256((source_root/'cad/intersecoes.json').read_bytes()).hexdigest(),
        nao_refletor_inalterados=len(before),refletor_mm=cfg['refletor_mm'],topo_z_mm=z)
    for name,value in [('geometria_esperada.json',geo),('intersecoes.json',audit)]:
        (out/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    A.closeDocument(doc.Name)
    re=A.openDocument(str(root/cfg['cad_native']))
    assert all(re.getObject(n).Shape.isValid() for n in manifest)
    A.closeDocument(re.Name)
    (out/'reabertura.json').write_text(json.dumps(dict(objetos=len(manifest),todos_validos=True,sha256=hashlib.sha256((root/cfg['cad_native']).read_bytes()).hexdigest()),indent=2)+'\n')
    print('CAD_VALIDADO',root,len(manifest),'solidos',flush=True)
