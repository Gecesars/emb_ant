"""Hipótese de sensibilidade: película de 20 µm na hélice da bobina."""
import json
import os
from pathlib import Path
import FreeCAD as App
import Part
import Import
from cupons_cad import geometry, origin, mechanical

folder=Path(os.environ['P1H_R05'])/'cupons/Bobina_esmalte20'
folder.mkdir(exist_ok=True)
doc=App.newDocument('Bobina_esmalte20')
metals,ptfe=geometry(.9)
helix=Part.makeHelix(.73,1.46,.9)
helix.rotate(App.Vector(),App.Vector(0,1,0),90)
helix.translate(origin+App.Vector(2.2,0,-1.9))
envelope=mechanical.tube(Part.Wire(helix.Edges),.17)
enamel=envelope.cut(metals[0][1]).removeSplitter()
assert enamel.isValid() and enamel.Volume>0
assert enamel.common(ptfe).Volume<1e-8
for material,shapes in [('copper',metals),('PTFE',[('Isolador',ptfe)]),('Esmalte_hipotese',[('Pelicula',enamel)])]:
    objects=[]
    for label,shape in shapes:
        obj=doc.addObject('Part::Feature',label)
        obj.Shape=shape
        objects.append(obj)
    Import.export(objects,str(folder/(material+'.step')))
doc.recompute()
doc.saveAs(str(folder/'Bobina_esmalte20.FCStd'))
data=dict(espessura_mm=.02,permissividade=4.5,tangente_perdas=.03,
          volume_mm3=enamel.Volume,hipotese='Ensaio de sensibilidade; não é ficha do fio comprado. Película somente na hélice; pontas sem esmalte.')
(folder/'hipotese.json').write_text(json.dumps(data,indent=2),encoding='utf8')
print(data)
