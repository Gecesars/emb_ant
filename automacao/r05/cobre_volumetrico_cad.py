"""Representar os 35 µm de cobre por sólidos sem interseção com pinos e soldas."""
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
original=App.newDocument('Folhas')
Import.insert(str(source/'folha_cu.step'),original.Name)
inputs=[(o.Label,o.Shape.copy()) for o in original.Objects if o.TypeId=='Part::Feature']
App.closeDocument(original.Name)
doc=App.newDocument('Cobre_35um_R05')
records={}
objects=[]
for name,face in inputs:
    z=face.BoundBox.ZMin
    assert face.BoundBox.ZLength<1e-7
    outward=1 if min(abs(z+10),abs(z-17.37))<1e-6 else -1
    shape=face.extrude(App.Vector(0,0,outward*.035))
    volume=shape.Volume
    contacts=[]
    for label,metal in metals:
        if not shape.BoundBox.intersect(metal.BoundBox):continue
        common=shape.common(metal)
        if common.Volume>1e-10:
            shape=shape.cut(metal).removeSplitter()
            contacts.append([label,common.Volume])
    assert shape.isValid() and shape.Volume>1e-10,name
    for i,solid in enumerate(shape.Solids):
        key=name if len(shape.Solids)==1 else name+'_Cu%d'%i
        obj=doc.addObject('Part::Feature',key)
        obj.Label=key
        obj.Shape=solid
        objects.append(obj)
        records[key]=dict(base_z_mm=z,exposto=outward,espessura_mm=.035,
            volume_original_mm3=volume,volume_final_mm3=solid.Volume,contatos=contacts)
    assert shape.Volume<=volume+1e-7
for path in source.glob('*.step'):
    if path.stem!='folha_cu':shutil.copy2(path,target/path.name)
Import.export(objects,str(target/'folha_cu.step'))
doc.recompute()
doc.saveAs(str(target/'Cobre_35um.FCStd'))
(target/'folhas_solidas.json').write_text(json.dumps(records,indent=2),encoding='utf8')
print('COBRE_VOLUMETRICO_OK',len(objects),sum(o.Shape.Volume for o in objects))
