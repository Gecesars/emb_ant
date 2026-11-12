"""Montagem integral: tres PCBs2, coaxiais, divisor DFM e radome FR4 2mm."""
from pathlib import Path
import os,json,hashlib,copy
import FreeCAD as A,Part,Import
ROOT=Path(os.environ['P2S13_ROOT']);cfg=json.loads((ROOT/'configuracao.json').read_text(encoding='utf-8'));OUT=ROOT/'cad';OUT.mkdir(exist_ok=True)
ANT=Path(cfg['fonte_antena']);DIV=Path(cfg['fonte_divisor']);V=A.Vector
d=A.newDocument('P2S13_R11_Radome');man={};rec={}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(n,x):(OUT/(n+'.json')).write_text(json.dumps(x,indent=2)+'\n')
def add(n,s,m):
    assert s.isValid() and len(s.Solids)==1 and s.Volume>0,n
    o=d.addObject('Part::Feature',n);o.Shape=s;o.addProperty('App::PropertyString','Material_nominal');o.Material_nominal=m;man[n]=m;return o
src=A.openDocument(str(ANT/'P2S13_TresPCB2.FCStd'));original={}
for n,m in read(ANT/'cad/manifesto.json').items():
    sh=src.getObject(n).Shape.copy();add(n,sh,m);original[n]=dict(volume_mm3=sh.Volume,area_mm2=sh.Area)
rec.update(read(ANT/'cad/folhas_solidas.json'));A.closeDocument(src.Name)
src=A.openDocument(str(DIV/'Divisor_Duplo3.FCStd'));dz=cfg['divisor_translacao_z_mm']
for n,m in read(DIV/'cad/manifesto.json').items():
    sh=src.getObject(n).Shape.copy();sh.rotate(V(0,0,0),V(1,0,0),180);sh.translate(V(0,0,dz))
    if n=='Substrato':
        # AEDT ignores the root placement of this single-body STEP. Rebuild
        # the isotropic drilled slab in world coordinates, retaining analytic faces.
        dc=read(DIV/'configuracao.json');h=dc['h'];rh=dc['fabricacao']['furo_acabado_mm']/2+dc['fabricacao']['metalizacao_mm']
        baked=Part.makeBox(220,64,h,V(-110,-32,dz-h))
        for p in dc['portas']:baked=baked.cut(Part.makeCylinder(rh,h+.02,V(p['x'],-p['y'],dz-h-.01)))
        baked=baked.removeSplitter();diff=sh.cut(baked).Volume+baked.cut(sh).Volume
        assert diff<1e-7,diff
        write('substrato_coordenadas_globais',dict(diferenca_volume_mm3=diff,placement=str(baked.Placement),motivo='AEDT importador STEP single-body descartou placement raiz; nenhuma mudanca geometrica.'))
        sh=baked
    add('D_'+n,sh,m)
for n,r in read(DIV/'cad/folhas_solidas.json').items():
    r=copy.deepcopy(r);r['base_z_mm']=-r['base_z_mm']+dz
    for hole in r.get('skip_hole_cylinders',[]):hole['y']=-hole['y']
    rec['D_'+n]=r
A.closeDocument(src.Name)
r=cfg['radome'];lo=r['inner_min_mm'];hi=r['inner_max_mm'];t=r['espessura_mm']
inside=Part.makeBox(*(hi[k]-lo[k] for k in range(3)),V(*lo))
outside=Part.makeBox(*(hi[k]-lo[k]+2*t for k in range(3)),V(*(x-t for x in lo)))
add('Radome_FR4_2mm',outside.cut(inside).removeSplitter(),r['material'])
connections=[]
for p in cfg['portas_coaxiais']:
    cell,pol=p['name'].split('_')
    for ant,div,kind in [(cell+'_Vivo_'+pol,'D_Pino_'+p['name'],'sinal'),(cell+'_Blindagem_'+pol,'D_Massa_'+p['name'],'terra')]:
        a=d.getObject(ant).Shape;b=d.getObject(div).Shape
        distance=a.distToShape(b)[0]
        contact=sum(f.common(g).Area for f in a.Faces for g in b.Faces if f.distToShape(g)[0]<1e-7)
        assert distance<1e-6 and contact>1e-5,(ant,div,distance,contact)
        connections.append(dict(antena=ant,divisor=div,tipo=kind,distancia_mm=distance,area_contato_mm2=contact))
objects=[d.getObject(n) for n in man];bad=[];pairs=0
for i,a in enumerate(objects):
    for b in objects[i+1:]:
        if any(min(getattr(a.Shape.BoundBox,k+'Max'),getattr(b.Shape.BoundBox,k+'Max'))-max(getattr(a.Shape.BoundBox,k+'Min'),getattr(b.Shape.BoundBox,k+'Min'))<=1e-6 for k in 'XYZ'):continue
        pairs+=1;vol=a.Shape.common(b.Shape).Volume
        if vol>1e-7:bad.append(dict(a=a.Name,b=b.Name,volume_mm3=vol))
assert not bad,bad
for n,e in original.items():assert abs(d.getObject(n).Shape.Volume-e['volume_mm3'])<1e-8,n
d.recompute();native=ROOT/cfg['cad_native'];d.saveAs(str(native))
for mat in sorted(set(man.values())):Import.export([d.getObject(n) for n,m in man.items() if m==mat],str(OUT/(mat+'.step')))
for n,v in [('manifesto',man),('folhas_solidas',rec),('portas',cfg['portas']),('conexoes',connections),('antena_preservada',original),('intersecoes',dict(aprovado=True,objetos=len(man),pares=pairs,intersecoes=bad))]:write(n,v)
write('geometria_esperada',dict((n,dict(volume_mm3=d.getObject(n).Shape.Volume,bbox_mm=[getattr(d.getObject(n).Shape.BoundBox,k) for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax']])) for n in man))
cfg['solidos_fisicos']=len(man);(ROOT/'configuracao.json').write_text(json.dumps(cfg,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
A.closeDocument(d.Name);d=A.openDocument(str(native));assert all(d.getObject(n).Shape.isValid() for n in man)
write('reabertura',dict(validos=True,objetos=len(man),sha256=hashlib.sha256(native.read_bytes()).hexdigest()))
A.closeDocument(d.Name);print('CONJUNTO_CAD_OK',len(man),'contatos',len(connections))
