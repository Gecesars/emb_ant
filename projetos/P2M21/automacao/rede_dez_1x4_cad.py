"""Montagem de posicionamento das cinco PCBs duplas, sem modificar os radiadores."""
from pathlib import Path
import json,hashlib
import FreeCAD as A,Part

repo=Path('D:/dev/EMBRAER/emb_ant')
dest=repo/'projetos/P2M21/rede_dez_1x4'
root=Path('D:/dev/EMBRAER/P2M21/R05_Dez_Divisores_1x4');(root/'freecad').mkdir(exist_ok=True)
src=Path('D:/dev/EMBRAER/P2M21/R00_Concepcao')
cfg=json.loads((dest/'configuracao.json').read_text(encoding='utf-8'))
old=A.openDocument(str(src/'mecanica/P2M21_Montagem.FCStd'))
board=A.openDocument(str(src/'divisor_1x4/P2M21_Duplo_1x4.FCStd'))
doc=A.newDocument('P2M21_Dez_1x4_Posicionamento');preserved={};new=[]
def feature(name,label,shape,material,group=None):
    o=doc.addObject('Part::Feature',name);o.Label=label;o.Shape=shape.copy()
    o.addProperty('App::PropertyString','Material_nominal','Projeto');o.Material_nominal=material
    if group:group.addObject(o)
    return o
for o in old.Objects:
    if not hasattr(o,'Shape') or o.Name.startswith(('D4_','D8_')):continue
    material=o.Material_nominal if 'Material_nominal' in o.PropertiesList else 'nao_definido'
    n=feature(o.Name,o.Label,o.Shape,material);preserved[n.Name]=o.Shape.Volume
for pos in cfg['posicoes']:
    name=pos['pcb'];part=doc.addObject('App::Part',name);part.Label=name+' - dois divisores 1:4'
    part.addProperty('App::PropertyString','Estado','Projeto');part.Estado='Interface com os radiadores pendente; referencia RF inalterada'
    part.Placement.Base=A.Vector(pos['centro_x_mm'],0,pos['base_z_mm'])
    for o in board.Objects:
        if not hasattr(o,'Shape'):continue
        material=o.Material_nominal if 'Material_nominal' in o.PropertiesList else 'nao_definido'
        n=feature(name+'_'+o.Name,o.Label,o.Shape,material,part);new.append(n)
doc.recompute()
shapes={}
for o in doc.Objects:
    if o.TypeId!='Part::Feature':continue
    assert o.Shape.isValid() and o.Shape.Volume>0,o.Name
    s=o.Shape.copy();s.transformShape(o.getGlobalPlacement().toMatrix());shapes[o.Name]=s
bad=[];tested=0
for o in new:
    a=shapes[o.Name];bb=a.BoundBox
    for name,b in shapes.items():
        if name==o.Name or (name.startswith(tuple(p['pcb']+'_' for p in cfg['posicoes'])) and name<o.Name):continue
        q=b.BoundBox
        if min(bb.XMax,q.XMax)-max(bb.XMin,q.XMin)<=1e-6 or min(bb.YMax,q.YMax)-max(bb.YMin,q.YMin)<=1e-6 or min(bb.ZMax,q.ZMax)-max(bb.ZMin,q.ZMin)<=1e-6:continue
        tested+=1;v=a.common(b).Volume
        if v>1e-7:bad.append(dict(a=o.Name,b=name,volume_mm3=v))
assert not bad,bad
path=root/'freecad/P2M21_Dez_1x4_Posicionamento.FCStd';doc.saveAs(str(path));A.closeDocument(doc.Name)
reopen=A.openDocument(str(path))
for name,vol in preserved.items():assert abs(reopen.getObject(name).Shape.Volume-vol)<1e-6,name
assert all(reopen.getObject(p['pcb']) for p in cfg['posicoes'])
result=dict(pcbs=5,circuitos_1x4=10,componentes_novos=len(new),formas_preservadas=len(preserved),
    pares_intersecoes_testados=tested,intersecoes=bad,todas_formas_validas=True,reaberto=True,
    tipo='Montagem por posicionamento com cinco App::Part; sem chicote e sem interfaces 1:2 novas.',
    volume_antenna_preservado=True)
(root/'freecad/verificacao.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
import shutil
for p in [path,root/'freecad/verificacao.json']:shutil.copy2(p,dest/'freecad'/p.name)
A.closeDocument(reopen.Name);A.closeDocument(old.Name);A.closeDocument(board.Name)
print(json.dumps(result))
