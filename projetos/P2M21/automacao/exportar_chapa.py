"""DXF de corte e dobra da chapa preliminar; K e raio dependem do ferramental."""
import json,math
from pathlib import Path
import ezdxf
root=Path('D:/dev/EMBRAER/P2M21/R00_Concepcao');dest=root/'mecanica'
cfg=json.loads((root/'configuracao.json').read_text());p=json.loads((dest/'parametros.json').read_text())
doc=ezdxf.new('R2010');doc.units=4
for name,color in [('CORTE',7),('DOBRA',1),('NOTAS',3)]:doc.layers.new(name,dxfattribs={'color':color})
m=doc.modelspace();left=425-p['comprimento_plano_mm'];ba=math.pi/2*(2+.4*2)
m.add_lwpolyline([(left,-50),(425,-50),(425,50),(left,50)],close=True,dxfattribs={'layer':'CORTE'})
for pt in json.loads((root/'antena/cad/portas.json').read_text()):m.add_circle((pt['x'],pt['y']),2.1,dxfattribs={'layer':'CORTE'})
for cx in [0]+cfg['centros_modulos_x_mm']:
    for dx in (-17,17):
        for y in (-36,36):m.add_circle((cx+dx,y),1.6,dxfattribs={'layer':'CORTE'})
for cx in cfg['centros_modulos_x_mm']:
    for dx in (-52.6,52.6):
        for y in (-30,30):m.add_circle((cx+dx,y),1.6,dxfattribs={'layer':'CORTE'})
for y in (-22,22):m.add_circle((-425-ba-20,y),8,dxfattribs={'layer':'CORTE'})
m.add_line((-425-ba/2,-50),(-425-ba/2,50),dxfattribs={'layer':'DOBRA'})
m.add_text('P2M21 R00 - AL 2 mm - Ri2 - 90graus - K0.4 assumido - NAO LIBERADO',dxfattribs={'layer':'NOTAS','height':4,'insert':(-425,60)})
doc.saveas(str(dest/'Refletor_corte_dobra_R00.dxf'))
assert not doc.audit().has_errors
print('DXF_OK',len(m))
