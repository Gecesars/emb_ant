"""Montagem sem radome: placas e refletor preservados, C09 e seis coaxiais iguais."""
from pathlib import Path
import os,json,hashlib,copy
import FreeCAD as A,Part,Import
ROOT=Path(os.environ['P2S13_ROOT']);cfg=json.loads((ROOT/'configuracao.json').read_text());OUT=ROOT/'cad';OUT.mkdir(exist_ok=True)
REF=Path(cfg['fonte_CAD_preservado']);DIV=Path(cfg['fonte_divisor']);V=A.Vector
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(n,x):(OUT/(n+'.json')).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
src=A.openDocument(str(REF/'P2S13_Curvilinear.FCStd'));d=A.newDocument('P2S13_R14_SemRadome');man={};records={};original={};connections=[]
def add(n,sh,m):
    sh=sh.removeSplitter();assert sh.isValid() and sh.Volume>0 and len(sh.Solids)==1,(n,sh.Volume,len(sh.Solids))
    o=d.addObject('Part::Feature',n);o.Shape=sh;o.addProperty('App::PropertyString','Material_nominal');o.Material_nominal=m;man[n]=m;return o
oldman=read(REF/'cad/manifesto.json');oldrec=read(REF/'cad/folhas_solidas.json');routes=read(ROOT/'cabos.json')
clip=Part.makeBox(1000,1000,1000,V(-500,-500,10))
for n,m in oldman.items():
    if n.startswith('D_') or n=='Radome_FR4_2mm':continue
    sh=src.getObject(n).Shape.copy();original[n]=sh.copy()
    if any(n==cell+'_'+kind+'_'+pol for cell in ['R1','R2','R3'] for kind in ['Vivo','Blindagem','PTFE'] for pol in ['A','B']):
        cell,kind,pol=n.split('_');path=copy.deepcopy(routes[cell+'_'+pol]);path[-1][-1][2]=10.
        edges=[]
        for tag,*pts in path:
            pts=[V(*p) for p in pts];edges.append(Part.makeLine(*pts) if tag=='L' else Part.Arc(*pts).toShape())
        wire=Part.Wire(edges);start=V(*path[0][1]);normal=V(0,0,1)
        def swept(radius):
            profile=Part.Wire([Part.makeCircle(radius,start,normal)])
            result=wire.makePipeShell([profile],True,False)
            assert result.isValid() and len(result.Solids)==1
            return result
        ri,rd,ro=[cfg['cabos'][k] for k in ['raio_interno_mm','raio_dieletrico_mm','raio_externo_mm']]
        new=swept(ri) if kind=='Vivo' else (swept(rd).cut(swept(ri)) if kind=='PTFE' else swept(ro).cut(swept(rd)))
        top=sh.common(clip);assert top.Volume>0 and len(top.Solids)==1
        assert new.distToShape(top)[0]<1e-7
        sh=new.fuse(top).removeSplitter()
    add(n,sh,m)
    if n in oldrec:records[n]=oldrec[n]
A.closeDocument(src.Name)
dc=read(DIV/'configuracao.json');div=A.openDocument(str(DIV/'Divisor_Duplo3.FCStd'));dz=cfg['divisor_translacao_z_mm']
for n,m in read(DIV/'cad/manifesto.json').items():
    sh=div.getObject(n).Shape.copy();sh.rotate(V(),V(1,0,0),180);sh.translate(V(0,0,dz))
    if n=='Substrato':
        bx,by=dc['board'];ox,oy=dc['board_origin'];h=dc['h'];rh=dc['fabricacao']['furo_acabado_mm']/2+dc['fabricacao']['metalizacao_mm']
        baked=Part.makeBox(bx,by,h,V(ox,-oy-by,dz-h))
        for p in dc['portas']:baked=baked.cut(Part.makeCylinder(rh,h+.02,V(p['x'],-p['y'],dz-h-.01)))
        baked=baked.removeSplitter();assert sh.cut(baked).Volume+baked.cut(sh).Volume<1e-7;sh=baked
    add('D_'+n,sh,m)
for n,r in read(DIV/'cad/folhas_solidas.json').items():
    r=copy.deepcopy(r);r['base_z_mm']=-r['base_z_mm']+dz
    for hole in r.get('skip_hole_cylinders',[]):hole['y']=-hole['y']
    records['D_'+n]=r
A.closeDocument(div.Name)
for name in routes:
    cell,pol=name.split('_')
    for a,b in [(cell+'_Vivo_'+pol,'D_Pino_'+name),(cell+'_Blindagem_'+pol,'D_Massa_'+name),(cell+'_PTFE_'+pol,'D_PTFE_'+name)]:
        sa=d.getObject(a).Shape;sb=d.getObject(b).Shape;distance=sa.distToShape(sb)[0];assert distance<1e-7,(a,b,distance)
        contact=sum(f.common(g).Area for f in sa.Faces for g in sb.Faces if f.distToShape(g)[0]<1e-7)
        assert contact>1e-5,(a,b,contact)
        sh=sa.fuse(sb).removeSplitter();assert sh.isValid() and len(sh.Solids)==1
        assert abs(sh.Volume-sa.Volume-sb.Volume)<1e-6
        d.getObject(a).Shape=sh;d.removeObject(b);man.pop(b)
        connections.append(dict(a=a,b=b,area_contato_mm2=contact,distancia_mm=distance))
unchanged={}
for n,sh in original.items():
    if any(k in n for k in ['_Vivo_','_Blindagem_','_PTFE_']):continue
    diff=sh.cut(d.getObject(n).Shape).Volume+d.getObject(n).Shape.cut(sh).Volume;assert diff<1e-8,n;unchanged[n]=diff
objects=[d.getObject(n) for n in man];bad=[]
for i,a in enumerate(objects):
    for b in objects[i+1:]:
        if any(min(getattr(a.Shape.BoundBox,k+'Max'),getattr(b.Shape.BoundBox,k+'Max'))-max(getattr(a.Shape.BoundBox,k+'Min'),getattr(b.Shape.BoundBox,k+'Min'))<=1e-6 for k in 'XYZ'):continue
        vol=a.Shape.common(b.Shape).Volume
        if vol>1e-7:bad.append(dict(a=a.Name,b=b.Name,volume_mm3=vol))
write('intersecoes',dict(aprovado=not bad,objetos=len(man),intersecoes=bad));assert not bad,bad
d.recompute();native=ROOT/cfg['cad_native'];d.saveAs(str(native))
for mat in sorted(set(man.values())):Import.export([d.getObject(n) for n,m in man.items() if m==mat],str(OUT/(mat+'.step')))
write('manifesto',man);write('folhas_solidas',records);write('portas',cfg['portas']);write('conexoes',connections)
write('alteracoes_C09',dict(aprovado=True,radome_removido=True,objetos=len(man),inalterados=unchanged,cabos=cfg['cabos']))
write('geometria_esperada',dict((n,dict(volume_mm3=d.getObject(n).Shape.Volume,bbox_mm=[getattr(d.getObject(n).Shape.optimalBoundingBox(False,False),k) for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax']])) for n in man))
cfg['solidos_fisicos']=len(man);(ROOT/'configuracao.json').write_text(json.dumps(cfg,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
A.closeDocument(d.Name);d=A.openDocument(str(native));assert all(d.getObject(n).Shape.isValid() for n in man)
write('reabertura',dict(aprovado=True,objetos=len(man),sha256=hashlib.sha256(native.read_bytes()).hexdigest()));A.closeDocument(d.Name)
print('R14_CAD_OK',len(man),'contatos',len(connections))
