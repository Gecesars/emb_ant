"""PCBs distribuidoras completas com terminais locais; nenhuma rota de cabo."""
import json,os
from pathlib import Path
import FreeCAD as App, Part, Import
V=App.Vector
root=Path(os.environ['P1H_R06']);source=Path(os.environ['P1H_CAD_BASE'])
geometries=Path(r'D:/dev/EMBRAER/P1H/R02_Estudo/placas')
allrecords=json.loads((source/'folhas_solidas.json').read_text())
shapes={}
for material in ['ZYF300','folha_cu','SAC305']:
    d=App.newDocument('Fonte_div')
    Import.insert(str(source/(material+'.step')),d.Name)
    shapes[material]=[(o.Label,o.Shape.copy()) for o in d.Objects if o.TypeId=='Part::Feature']
    App.closeDocument(d.Name)
for side,offset in [('Inferior',2.50916841304063-2.5*52.6),('Superior',2.50916841304063+2.5*52.6)]:
    target=root/('divisor_'+side.lower());cad=target/'cad';cad.mkdir(parents=True,exist_ok=True)
    d=App.newDocument('Divisor_'+side);group={};manifest={};records={};pins=[]
    g=json.loads((geometries/side/'geometria.json').read_text())
    zb=-11.52;zf=-10.;zp=zb-.18
    def add(name,shape,material):
        assert shape.isValid() and not shape.isNull(),name
        o=d.addObject('Part::Feature',name);o.Label=name;o.Shape=shape
        group.setdefault(material,[]).append(o);manifest[name]=material
        return o
    for name,px,y in g['ports']:
        x=px+offset
        # Pino soldado atravessando a PCB; terminal posterior de 0,18 mm.
        pin=Part.makeCylinder(.525,zf+.07-zp,V(x,y,zp))
        cap=Part.makeCylinder(.65,.07,V(x,y,zf))
        signal=pin.fuse(cap).removeSplitter();pins.append(signal)
        add('Terminal_'+name,signal,'copper')
        ro=4. if name in ('RA_IN','RB_IN') else 1.7905
        ground=Part.makeCylinder(ro,.18,V(x,y,zp)).cut(Part.makeCylinder(1.515,.18,V(x,y,zp)))
        add('Massa_terminal_'+name,ground,'copper')
        dielectric=Part.makeCylinder(1.515,.18,V(x,y,zp)).cut(Part.makeCylinder(.525,.18,V(x,y,zp)))
        add('Isol_terminal_'+name,dielectric,'PTFE_terminal')
    for material,objects in shapes.items():
        for name,shape in objects:
            if side not in name:continue
            if material=='folha_cu':
                for pin in pins:
                    if shape.BoundBox.intersect(pin.BoundBox):shape=shape.cut(pin).removeSplitter()
                records[name]=allrecords[name]
            add(name,shape,material)
    for material,objects in group.items():Import.export(objects,str(cad/(material+'.step')))
    ports=[dict(name=n,x=x+offset,y=y,z=zp,ri=.525,ro=1.515) for n,x,y in g['ports']]
    for filename,data in [('manifesto',manifest),('folhas_solidas',records),('portas',ports),
      ('verificacao',dict(placa=side,portas=len(ports),chicote_3d=False,terminal_mm=.18,
       solda_sinal_topo_raio_mm=.65,solda_sinal_topo_altura_mm=.07,objetos={k:len(v) for k,v in group.items()}))]:
        (cad/(filename+'.json')).write_text(json.dumps(data,indent=2),encoding='utf8')
    d.recompute();d.saveAs(str(target/('Divisor_'+side+'.FCStd')))
    App.closeDocument(d.Name)
    print('DIVISOR_CAD_OK',side,len(ports),len(records))
