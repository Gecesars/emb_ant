"""CAD novo P2M21. Executar com o Python do FreeCAD, sem alterar a GUI do usuario."""
import json,math
from pathlib import Path
import FreeCAD as A,Part,Import
V=A.Vector
root=Path('D:/dev/EMBRAER/P2M21/R00_Concepcao')
oldroot=Path('D:/dev/EMBRAER/P1H/R06_sem_cabos/antena')
config=json.loads((root/'configuracao.json').read_text())
old=A.openDocument(str(oldroot/'PCB_R06.FCStd'))
oldmat=json.loads((oldroot/'cad/manifesto.json').read_text())
oldfoils=json.loads((oldroot/'cad/folhas_solidas.json').read_text())

def box(x,y,z,a,b,c):return Part.makeBox(a,b,c,V(x,y,z))
def cyl(x,y,z,r,h):return Part.makeCylinder(r,h,V(x,y,z))
def face(points,z):
    p=[V(x,y,z) for x,y in points];return Part.Face(Part.makePolygon(p+[p[0]]))
def shift(s,x=0,y=0,z=0):
    s=s.copy();s.translate(V(x,y,z));return s
def begin(name):return A.newDocument(name),{},{}
def add(d,manifest,name,shape,mat):
    assert shape.isValid() and not shape.isNull() and shape.Volume>0,name
    o=d.addObject('Part::Feature',name);o.Shape=shape;o.Label=name
    o.addProperty('App::PropertyString','Material_nominal','Projeto');o.Material_nominal=mat
    manifest[name]=mat;return o
def save(d,manifest,records,ports,folder,name):
    cad=folder/'cad';cad.mkdir(parents=True,exist_ok=True)
    for mat in sorted(set(manifest.values())):
        Import.export([d.getObject(n) for n,m in manifest.items() if m==mat],str(cad/(mat+'.step')))
    for f,data in [('manifesto',manifest),('folhas_solidas',records),('portas',ports)]:
        (cad/(f+'.json')).write_text(json.dumps(data,indent=2),encoding='utf8')
    check=dict(objetos=len(manifest),portas=len(ports),todos_validos=True,
       solidos=sum(len(d.getObject(n).Shape.Solids) for n in manifest),chicote_3d=False,
       volumes_mm3={n:d.getObject(n).Shape.Volume for n in manifest})
    (cad/'verificacao.json').write_text(json.dumps(check,indent=2),encoding='utf8')
    d.recompute();d.saveAs(str(folder/(name+'.FCStd')))
    return check

# Antena: copiar exatamente cobre, vias, terminais e vazios locais do elemento R06.
d,manifest,records=begin('P2M21_Antena_32')
source_center=-236.7
source_objs=[]
for o in old.Objects:
    if o.Name not in oldmat:continue
    m=oldmat[o.Name];b=o.Shape.BoundBox
    if (o.Name.startswith('Ant01_') or
        m in ('copper','SAC305') and b.XMin>source_center-14.2 and b.XMax<source_center+14.2):
        source_objs.append(o)
localbox=box(source_center-14.15625,-14.15625,16.61,28.3125,28.3125,.76)
voids=localbox.cut(old.getObject('Rogers').Shape)
assert voids.Volume>0
ports=[];pcbshapes=[];supportholes=[]
for module,mc in enumerate(config['centros_modulos_x_mm'],1):
    core=box(mc-93.05625,-34.15625,16.61,186.1125,68.3125,.76)
    for row in range(4):
        x=mc+(row-1.5)*52.6
        for col,y in enumerate((-20,20),1):
            index=(module-1)*8+row*2+col;dx=x-source_center
            core=core.cut(shift(voids,dx,y))
            for o in source_objs:
                name='E%02d_'%index+o.Name
                add(d,manifest,name,shift(o.Shape,dx,y),oldmat[o.Name])
                if o.Name in oldfoils:records[name]=oldfoils[o.Name]
            for pol,sgn in [('A',-1),('B',1)]:
                ports.append(dict(name='E%02d_%s'%(index,pol),x=x+2.50916841304063,
                  y=y+sgn*2.50916841304063,z=16.575,ri=.6,ro=.834856,
                  module=module,row=(module-1)*4+row+1,column=col,polarization=pol))
    pcbshapes.append(add(d,manifest,'PCB_Modulo_%d'%module,core,'RO4350B_R01'))
    # Berco transversal novo: a PCB une as colunas, portanto nao usar garras internas da P1H.
    for gap in (-52.6,52.6):
        x=mc+gap
        s=box(x-2.5,-38,0,5,76,19.6)
        s=s.cut(box(x-2.5,-34.25625,16.61,5,68.5125,3.1))
        for hy in (-30,30):
            s=s.cut(cyl(x,hy,0,1.25,8));supportholes.append((x,hy))
        add(d,manifest,'Berco_%d_%s'%(module,'M' if gap<0 else 'P'),s,'POM_nom')

# Chapa de 2mm com base dobrada 90 graus, raio interno2; furos reais.
plate=box(-425,-50,-2,850,100,2)
passholes=[(p['x'],p['y']) for p in ports]
mounts=[(cx+dx,y) for cx in [0]+config['centros_modulos_x_mm'] for dx in (-17,17) for y in (-36,36)]
for x,y in passholes:plate=plate.cut(cyl(x,y,-2,2.1,2))
for x,y in mounts+supportholes:plate=plate.cut(cyl(x,y,-2,1.6,2))
# Extruded quarter-annulus in XZ, tangent to plate and downward base.
p1=V(-425,-50,0);p2=V(-429,-50,-4);p3=V(-427,-50,-4);p4=V(-425,-50,-2)
edges=[Part.Arc(p1,V(-425-4/math.sqrt(2),-50,-4+4/math.sqrt(2)),p2).toShape(),
 Part.makeLine(p2,p3),Part.Arc(p3,V(-425-2/math.sqrt(2),-50,-4+2/math.sqrt(2)),p4).toShape(),Part.makeLine(p4,p1)]
bend=Part.Face(Part.Wire(edges)).extrude(V(0,100,0))
base=box(-429,-50,-45,2,100,41)
for y in (-22,22):base=base.cut(Part.makeCylinder(8,2,V(-429,y,-24),V(1,0,0)))
reflector=plate.fuse(bend).fuse(base).removeSplitter()
add(d,manifest,'Refletor_dobrado',reflector,'AL5052')
save(d,manifest,records,ports,root/'antena','P2M21_Antena')

# Montagem separada: duplicar shapes, nao poluir o modelo EM com cabos/divisores.
assembly=A.newDocument('P2M21_Montagem');am={}
for name,mat in manifest.items():add(assembly,am,name,d.getObject(name).Shape.copy(),mat)
board_docs={}
for n in (4,8):
    folder=root/f'divisor_1x{n}';g=json.loads((folder/'geometria.json').read_text())
    dd,dm,dr=begin('Duplo_1x%d'%n);h=g['h']
    core=box(-19.5,-39,0,39,78,h)
    ground=box(-19,-38.5,-.035,38,77,.035)
    stars={pol:face(coords,h).extrude(V(0,0,.035)) for pol,coords in g['copper'].items()}
    for x,y in g['montagem_furos']:
        core=core.cut(cyl(x,y,0,1.6,h));ground=ground.cut(cyl(x,y,-.035,2.25,.035))
    pp=[]
    for name,x,y in g['ports']:
        core=core.cut(cyl(x,y,0,.525,h));ground=ground.cut(cyl(x,y,-.035,1.515,.035))
        pin=cyl(x,y,-.18,.525,h+.25).fuse(cyl(x,y,h,.65,.07)).removeSplitter()
        stars[name[0]]=stars[name[0]].cut(pin).removeSplitter()
        pad=cyl(x,y,-.035,.73,.035).cut(cyl(x,y,-.035,.525,.035))
        ann=cyl(x,y,-.18,2.13,.145).cut(cyl(x,y,-.18,1.515,.145))
        die=cyl(x,y,-.18,1.515,.18).cut(cyl(x,y,-.18,.525,.18)).cut(pad)
        add(dd,dm,'Terminal_'+name,pin,'copper');add(dd,dm,'Massa_terminal_'+name,ann,'copper')
        add(dd,dm,'Isol_terminal_'+name,die,'PTFE_terminal')
        add(dd,dm,'Pad_'+name,pad,'folha_cu');dr['Pad_'+name]=dict(base_z_mm=0,exposto=-1,espessura_mm=.035)
        pp.append(dict(name=name,x=x,y=y,z=-.18,ri=.525,ro=1.515))
    add(dd,dm,'PCB',core,'ZYF300');add(dd,dm,'GND',ground,'folha_cu')
    dr['GND']=dict(base_z_mm=0,exposto=-1,espessura_mm=.035)
    for pol,s in stars.items():
        add(dd,dm,'Estrela_'+pol,s,'folha_cu');dr['Estrela_'+pol]=dict(base_z_mm=h,exposto=1,espessura_mm=.035)
    save(dd,dm,dr,pp,folder,'P2M21_Duplo_1x%d'%n);board_docs[n]=dd
    for k,cx in enumerate([0] if n==4 else config['centros_modulos_x_mm'],1):
        for name,mat in dm.items():add(assembly,am,'D%d_%d_'%(n,k)+name,shift(dd.getObject(name).Shape,cx,0,-11.52),mat)
        for j,(x,y) in enumerate(g['montagem_furos']):
            st=cyl(cx+x,y,-10,3,8).cut(cyl(cx+x,y,-10,1.6,8))
            add(assembly,am,'Espacador_D%d_%d_%d'%(n,k,j),st,'POM_nom')

mech=root/'mecanica';mech.mkdir(exist_ok=True)
ba=math.pi/2*(2+.4*2);length=850+ba+41
flat=box(-425-ba-41,-50,0,length,100,2)
for x,y in passholes:flat=flat.cut(cyl(x,y,0,2.1,2))
for x,y in mounts+supportholes:flat=flat.cut(cyl(x,y,0,1.6,2))
for y in (-22,22):flat=flat.cut(cyl(-425-ba-20,y,0,8,2))
fd=A.newDocument('Chapa_planificada');fm={};add(fd,fm,'Chapa_Al2mm',flat,'AL5052')
fd.recompute();fd.saveAs(str(mech/'Refletor_planificado.FCStd'));Import.export([fd.getObject('Chapa_Al2mm')],str(mech/'Refletor_planificado.step'))
assembly.recompute();assembly.saveAs(str(mech/'P2M21_Montagem.FCStd'))
Import.export([assembly.getObject('Refletor_dobrado')],str(mech/'Refletor_dobrado.step'))
(mech/'parametros.json').write_text(json.dumps(dict(face_mm=[850,100],espessura_mm=2,raio_interno_mm=2,
  fator_K_assumido=.4,angulo_graus=90,aba_reta_mm=41,comprimento_plano_mm=length,
  nota='Raio e K para projeto; confirmar ferramental antes da fabricacao. Montagem por posicionamento, nao cinematica.',
  furos_passagem_mm=4.2,furos_N_mm=16,furos_montagem_mm=3.2,
  centros_divisores=[0]+config['centros_modulos_x_mm'],apoios_POM_espessura_mm=5,
  pecas=len(am),objetos_validos=True),indent=2),encoding='utf8')
# Extrair tesselas da geometria real para vistas de revisao, sem alterar os nativos.
meshes=[]
for name,mat in am.items():
    if mat in ('copper','SAC305','PTFE_terminal'):continue
    o=assembly.getObject(name);pts,tris=o.Shape.tessellate(.18)
    meshes.append(dict(name=name,material=mat,vertices=[[p.x,p.y,p.z] for p in pts],triangles=tris))
(mech/'visualizacao.json').write_text(json.dumps(meshes),encoding='utf8')
print('CAD_P2M21_OK',len(ports),len(am),length)
