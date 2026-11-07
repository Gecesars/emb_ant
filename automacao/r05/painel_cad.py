"""Montagem R05 completa com chicote ajustado, nova bobina e refletor selecionado."""
from itertools import combinations
import json
import os
import sys
from pathlib import Path

import FreeCAD as App
import Import
import Part

repo=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(repo/'freecad/mecanica_R01/fonte'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import construir as m
from cupons_cad import geometry,origin

V=App.Vector
source=Path(os.environ['P1H_CAD_BASE'])
work=Path(os.environ['P1H_R05_WORK'])
cad=work/'cad'
cad.mkdir(parents=True,exist_ok=True)
doc=App.newDocument('Painel_R05')
parts={}
obstacles={}
def add(name,shape,material):
    assert shape.isValid() and not shape.isNull(),name
    obj=doc.addObject('Part::Feature',name)
    obj.Label=name
    obj.Shape=shape
    obj.addProperty('App::PropertyString','MaterialHFSS','RF').MaterialHFSS=material
    parts.setdefault(material,[]).append(obj)
    return obj
for path in source.glob('*.step'):
    material=path.stem
    original=App.newDocument('Origem')
    Import.insert(str(path),original.Name)
    for obj in original.Objects:
        # Import STEP cria App::Part com Shape agregada e objetos de origem.
        # Exportar somente as folhas geometricas evita duplicar conjuntos.
        if obj.TypeId != 'Part::Feature':
            continue
        name=obj.Label
        if material=='copper' and name.startswith(('Sinal_','Capa_','Lancamento_')):
            continue
        if material=='PTFE_cabo' and name.startswith('Isol_'):
            continue
        if material=='AL5052':
            shape=Part.read(os.environ['P1H_REFLETOR_STEP'])
            name='Refletor_R05'
        else:
            shape=obj.Shape.copy()
        add(name,shape,material)
        if material not in ('copper','folha_cu','PTFE_cabo','SAC305'):
            obstacles[name]=shape
    App.closeDocument(original.Name)
routes=json.loads((work/'compacta/caminhos.json').read_text())
routes.update(json.loads((work/'compacta/enlaces.json').read_text()))
metals,dielectric=geometry(.9)
clip=Part.makeBox(12,12,5,origin+V(-6,-6,-5))
metal_chunk=metals[0][1].common(clip)
dielectric_chunk=dielectric.common(clip)
zb=-11.52
wires={}
envelopes={}
def cylinder(x,y,r,z,h):return Part.makeCylinder(r,h,V(x,y,z))
for name,route in routes.items():
    wire=m.wire_from_data(route)
    wires[name]=wire
    envelopes[name]=m.tube(wire,m.R_CABO)
    edges=json.loads(json.dumps(route))
    inp=name.startswith('IN_')
    trunk=name.startswith('TR_')
    x,y,z=edges[-1][-1]
    sx,sy,sz=edges[0][1]
    if inp or not trunk:
        edges[-1][-1][2]-=5 if inp else 1
    path=m.wire_from_data(edges)
    outer=m.tube(path,m.R_CABO)
    die=m.tube(path,1.515)
    inner=m.tube(path,.45975)
    outer=outer.cut(die)
    die=die.cut(inner)
    if inp:
        shift=V(0,2*m.N_Y if name[-1]=='B' else 0,zb-origin.z)
        coil=metal_chunk.copy();coil.translate(shift)
        core=dielectric_chunk.copy();core.translate(shift)
        flange=cylinder(x,y,4,zb-.18,.18).cut(cylinder(x,y,1.515,zb-.18,.18))
        metal=m.union([outer,inner,coil,flange,cylinder(x,y,.525,zb,1.52)])
        die=m.union([die,core])
        assert len(metal.Solids)==1,name
        add('Lancamento_'+name[-1],metal,'copper')
    else:
        barrel=cylinder(sx,sy,.525,zb,1.52)
        if trunk:
            inner=m.union([inner,barrel,cylinder(x,y,.525,zb,1.52)])
        else:
            base=m.PLACA_Z
            lower=cylinder(x,y,m.R_CABO,base-1,.25).cut(cylinder(x,y,.834856,base-1,.25))
            upper=cylinder(x,y,1.2704335,base-.75,.75).cut(cylinder(x,y,.834856,base-.75,.75))
            outer=m.union([outer,lower,upper])
            inner=m.union([inner,barrel,cylinder(x,y,.362981,base-1,1),cylinder(x,y,.45,base,m.CORE)])
        assert len(inner.Solids)==1 and len(outer.Solids)==1,name
        add('Sinal_'+name,inner,'copper')
        add('Capa_'+name,outer,'copper')
    assert len(die.Solids)==1,name
    add('Isol_'+name,die,'PTFE_cabo')
errors=[]
for name,shape in envelopes.items():
    for other,obstacle in obstacles.items():
        if shape.BoundBox.intersect(obstacle.BoundBox):
            volume=shape.common(obstacle).Volume
            if volume>1e-5:errors.append([name,other,volume])
minimum,pair_a,pair_b=min((a.distToShape(b)[0]-2*m.R_CABO,na,nb)
    for (na,a),(nb,b) in combinations(wires.items(),2))
record=dict(interferencias_mm3=errors,folga_minima_entre_capas_mm=minimum,par_critico=[pair_a,pair_b],
    comprimentos_mm={name:wire.Length for name,wire in wires.items()},
    objetos={key:len(value) for key,value in parts.items()},bobina_raio_mm=.9,abertura_mm=1)
(cad/'verificacao.json').write_text(json.dumps(record,indent=2),encoding='utf8')
assert not errors,errors
assert minimum>.4,minimum
for material,objects in parts.items():
    Import.export(objects,str(cad/(material+'.step')))
doc.recompute()
doc.saveAs(str(cad/'Painel_R05.FCStd'))
(cad/'manifesto.json').write_text(json.dumps({o.Label:key for key,value in parts.items() for o in value},indent=2),encoding='utf8')
print('PAINEL_CAD_OK',record)
