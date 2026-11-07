"""Preparar ENIG apenas nas faces impressas que nao estao cobertas por metal volumetrico."""
import json
import os
import shutil
from pathlib import Path
import FreeCAD as App
import Import

source=Path(os.environ['P1H_CAD_ENIG_ORIGEM'])
target=Path(os.environ['P1H_CAD_ENIG_DESTINO'])
target.mkdir(parents=True,exist_ok=True)
metals=[]
for material in ['copper','SAC305','latao_nom','aco_nom','AL5052']:
    doc=App.newDocument('Metal')
    Import.insert(str(source/(material+'.step')),doc.Name)
    metals.extend((o.Label,o.Shape.copy()) for o in doc.Objects if o.TypeId=='Part::Feature')
    App.closeDocument(doc.Name)
doc=App.newDocument('ENIG')
Import.insert(str(source/'folha_cu.step'),doc.Name)
objects=[o for o in doc.Objects if o.TypeId=='Part::Feature']
assert len(objects)==138
record={}
for obj in objects:
    old=obj.Shape
    exposed=old.copy()
    contacts=[]
    for name,metal in metals:
        if not old.BoundBox.intersect(metal.BoundBox):
            continue
        patch=exposed.common(metal)
        if patch.Area>1e-8:
            before=exposed.Area
            exposed=exposed.cut(metal).removeSplitter()
            if before-exposed.Area>1e-8:contacts.append([name,before-exposed.Area])
    assert not exposed.isNull() and exposed.isValid() and exposed.Area>0,obj.Label
    assert all(abs(face.normalAt(0,0).z)> .999999 for face in exposed.Faces),obj.Label
    normals=set(round(face.normalAt(0,0).z) for face in exposed.Faces)
    assert len(normals)==1,obj.Label
    z=exposed.BoundBox.ZMin
    assert exposed.BoundBox.ZLength<1e-7
    outward=1 if min(abs(z+10),abs(z-17.37))<1e-6 else -1
    assert min(abs(z+10),abs(z+11.52),abs(z-17.37),abs(z-16.61))<1e-6
    record[obj.Label]=dict(z_mm=z,normal=normals.pop(),exposto=outward,
        area_original_mm2=old.Area,area_exposta_mm2=exposed.Area,contatos=contacts)
    obj.Shape=exposed
for path in source.glob('*.step'):
    if path.stem!='folha_cu':shutil.copy2(path,target/path.name)
Import.export(objects,str(target/'folha_cu.step'))
doc.recompute()
doc.saveAs(str(target/'Folhas_ENIG.FCStd'))
(target/'enig_faces.json').write_text(json.dumps(record,indent=2),encoding='utf8')
shutil.copy2(source/'manifesto.json',target/'manifesto.json')
print('ENIG_CAD_OK',len(record),'area removida sob metal',sum(r['area_original_mm2']-r['area_exposta_mm2'] for r in record.values()))
