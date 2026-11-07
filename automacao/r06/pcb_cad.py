"""Extrair PCB completa, refletor e apoios; portas na terminação da PCB, sem chicote."""
import json, os
from pathlib import Path
import FreeCAD as App, Part, Import

root=Path(os.environ['P1H_R06'])
source=Path(os.environ['P1H_CAD_BASE'])
target=root/'antena/cad';target.mkdir(parents=True,exist_ok=True)
doc=App.newDocument('PCB_R06_sem_cabos')
zport=16.61-.035
clip=Part.makeBox(700,200,100,App.Vector(-350,-100,zport))
positions=[((i-4.5)*52.6+2.50916841304063,sgn*2.50916841304063)
           for i in range(10) for sgn in [-1,1]]
# Solda local une ilha inferior, pino atravessante e pad superior.
# Nenhum trecho de coaxial é mantido; a porta termina no contorno do pad inferior.
solder_shapes=[]
for x,y in positions:
    solder_shapes.extend([Part.makeCylinder(.6,.035,App.Vector(x,y,zport)),
                          Part.makeCylinder(.6,.05,App.Vector(x,y,17.37))])
solders=Part.makeCompound(solder_shapes)
rules={'AL5052':('',),'RO4350B_R01':('',),'POM_nom':('Berco_','Batente_'),
       'aco_nom':('Par_','Arruela_'),'folha_cu':('Ant',),
       'copper':('Via','Sinal_INF_','Sinal_SUP_','Capa_INF_','Capa_SUP_')}
manifest={};counts={};selected_records={}
records=json.loads((source/'folhas_solidas.json').read_text())
for material,prefixes in rules.items():
    src=App.newDocument('Fonte_PCB')
    Import.insert(str(source/(material+'.step')),src.Name)
    output=[]
    for obj in src.Objects:
        if obj.TypeId!='Part::Feature' or not obj.Label.startswith(prefixes):continue
        name=obj.Label;shape=obj.Shape.copy()
        if name.startswith(('Sinal_','Capa_')):shape=shape.common(clip)
        if material=='folha_cu' and any(shape.BoundBox.intersect(s.BoundBox) for s in solder_shapes):
            shape=shape.cut(solders).removeSplitter()
            if shape.isNull() or shape.Volume<1e-10:continue
        if name.startswith('Sinal_'):
            b=shape.BoundBox;x=(b.XMin+b.XMax)/2;y=(b.YMin+b.YMax)/2
            shape=Part.makeCylinder(.45,.76,App.Vector(x,y,16.61))
        if material=='aco_nom' and shape.BoundBox.ZMax<=0:continue
        assert shape.isValid() and not shape.isNull(),name
        fragments=list(shape.Solids) if material=='folha_cu' else [shape]
        for k,fragment in enumerate(fragments):
            key=name if len(fragments)==1 else name+'_Cu%d'%k
            item=doc.addObject('Part::Feature',key);item.Label=key;item.Shape=fragment
            output.append(item);manifest[key]=material
            if material=='folha_cu':selected_records[key]=records[name]
    assert output,material
    Import.export(output,str(target/(material+'.step')))
    counts[material]=len(output)
    App.closeDocument(src.Name)
output=[]
for i,shape in enumerate(solder_shapes):
    name='Solda_terminal_%02d'%i
    item=doc.addObject('Part::Feature',name);item.Label=name;item.Shape=shape
    output.append(item);manifest[name]='SAC305'
Import.export(output,str(target/'SAC305.step'));counts['SAC305']=len(output)
records=selected_records
assert len(records)==counts['folha_cu']
ports=[{'name':'E%02d_%s'%(i+1,p),'x':(i-4.5)*52.6+2.50916841304063,
        'y':sgn*2.50916841304063,'z':zport,'ri':.6,'ro':.834856}
       for i in range(10) for p,sgn in [('A',-1),('B',1)]]
for port in ports:
    # Plano atravessa apenas a terminação metálica local de 35um sob a PCB.
    assert not any(n.startswith(('Isol_','Lancamento_','N_')) for n in manifest)
doc.recompute();doc.saveAs(str(root/'antena/PCB_R06.FCStd'))
for name,data in [('manifesto',manifest),('folhas_solidas',records),('portas',ports),
                  ('verificacao',{'objetos':counts,'z_porta_mm':zport,'comprimento_terminal_sob_pcb_mm':.035,
                   'chicote_3d':False,'todos_validos':True,'modelo':'PCB completa + refletor + apoios; sem cabos, N ou divisores'})]:
    (target/(name+'.json')).write_text(json.dumps(data,indent=2),encoding='utf8')
print('PCB_SEM_CABOS_CAD_OK',counts)
