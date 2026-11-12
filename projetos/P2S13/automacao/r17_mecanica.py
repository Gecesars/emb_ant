"""R17: montagem nominal DN100, flanges e fixadores. Executar em FreeCADCmd.

Geometria RF das PCBs/C02 e seis cabos preservada. Novas pecas mecanicas
nao sao automaticamente qualificadas pela comparacao RF plano/dobrado.
"""
from pathlib import Path
import os, json, math, hashlib
import FreeCAD as A, Part, Import
V=A.Vector
ROOT=Path('D:/dev/EMBRAER/P2S13/R17_Flanges_Refletor')
OUT=ROOT/os.environ.get('R17_MECANICA_DIR','mecanica'); OUT.mkdir(exist_ok=True,parents=True)
SRC=Path('D:/dev/EMBRAER/P2S13/R16_Tubo_PVC/dn100_c02/visual/Antena_PVC_DN100_C02_PRELIMINAR.FCStd')
STEP=Path('D:/dev/EMBRAER/82-6784.stp')
MODE=os.environ.get('R17_REFLETOR','dobrado150')
assert MODE in ['plano90','dobrado150']
src=A.openDocument(str(SRC)); d=A.newDocument('P2S13_R17_DN100_PRELIMINAR')
colors={}; original={}; critical=[]; groups={}; bom=[]
def group(n):
    if n not in groups: groups[n]=d.addObject('App::DocumentObjectGroup',n)
    return groups[n]
def prop(o,n,v):
    if n not in o.PropertiesList:o.addProperty('App::PropertyString',n,'Engenharia')
    setattr(o,n,str(v))
def add(n,sh,mat,col=(.65,.68,.7),g='Estrutura',new=True):
    assert not sh.isNull() and sh.isValid() and sh.Volume>0,(n,'forma invalida')
    o=d.addObject('Part::Feature',n);o.Shape=sh
    prop(o,'Material_nominal',mat);prop(o,'Estado','PRELIMINAR - interfaces mecanicas novas; sem homologacao RF do fechamento')
    group(g).addObject(o); colors[n]=list(col)
    if new:critical.append(o)
    return o
for o in src.Objects:
    if not o.isDerivedFrom('Part::Feature') or o.Shape.isNull():continue
    mat=getattr(o,'Material_nominal','Ver fonte R16')
    c=(.72,.42,.16) if any(s in o.Name for s in ['Cu','Sinal','Vivo','Blindagem','Massa','Pino','Terra']) else (.12,.43,.26) if 'PCB' in o.Name or 'Substrato' in o.Name else (.86,.87,.84)
    if o.Name=='Refletor_Al2mm':c=(.73,.76,.78)
    if 'PVC' in o.Name:c=(.84,.86,.88)
    g='Radiantes' if o.Name.startswith('R') and o.Name!='Refletor_Al2mm' else 'Divisor_C02' if o.Name.startswith('D_') else 'Estrutura'
    add(o.Name,o.Shape.copy(),mat,c,g,False); original[o.Name]=o.Shape.copy()
A.closeDocument(src.Name)

# Parametros unicos de montagem, usados tambem nos desenhos.
p=dict(estado='PRELIMINAR',refletor=MODE,tubo=dict(DE=101.6,DI=98.,parede=1.8,comprimento=350.,centro_z=-10.141),
 flange=dict(diametro=110.,espessura=4.76,canal_DI=97.3,canal_DE=102.3,canal_largura=2.5,canal_profundidade=2.5,
 face_interna_x=172.8,face_externa_x=177.56,parede_residual=2.26,folga_radial_tubo=.35,insercao=2.2),
 junta=dict(material='EPDM 60 Shore A nominal; anel recortado',DI=98.,DE=101.6,espessura_livre=.5,espessura_montada=.3,compressao_percent=40),
 chapa=dict(material='Aluminio 5052-H32 nominal',espessura=2.,face_comprimento=296.,largura_desenvolvida=90.,
 Ri=2.,K=.4,angulo_abas=0 if MODE=='plano90' else 150,linha_dobra_lateral=28.5 if MODE!='plano90' else None,
 lingueta_largura=20.,tangencia_x=168.8,leg_reta=14.,aba_final_z=[-18.,-4.],centros_furos_flange_y=[-5.,5.],centros_furos_flange_z=-11.,furo_fixacao=3.4),
 pcb=dict(quantidade=3,dimensoes=[88.,50.,.76],centros_x=[-96.,0.,96.],passo_elementos=48.,apoio_z=14.949,folga_lip=.05),
 divisor=dict(pcb=[36.,78.,1.52],x_min=-10.6598549068686,x_max=25.3401450931314,centro_x=7.3401450931314,
 z_solo=-35.196,z_core_top=-35.231,z_sinal=-36.786),
 conector=dict(modelo='Amphenol 082-6784',quantidade=2,y=[-22.,22.],z=-25.,furo_diametro=16.5,entre_planos=14.,
 face_junta_x=-177.56,face_junta_no_step_x=10.9,translacao_step_x=-166.66,deslocamento_porcas_no_step=1.69,torque_catalogo_Nm=3.39),
 fixacoes_radiantes=[],fixacoes_divisor=[],cabos_entrada=[],comprimento_cabos_saida=134.,
 limites='Nao validado estruturalmente/IP. Conferir lote do tubo e corte/preparo do coaxial antes da fabricacao em serie.')
BA=math.pi/2*(p['chapa']['Ri']+p['chapa']['K']*2)
p['chapa']['BA_extremidade']=BA;p['chapa']['comprimento_plano_total']=2*(168.8+BA+14)
p['comprimento_externo_sem_conectores']=355.12

# Refletor com duas linguetas centrais; abas longitudinais nao cruzam as dobras finais.
sheet=original['Refletor_Al2mm'].copy() if MODE!='plano90' else Part.makeBox(296,90,2,V(-148,-45,-2))
feedholes=[(x+2.50916841304063,y) for x in [-96,0,96] for y in [-18,18]]
if MODE=='plano90':
    for x,y in feedholes:sheet=sheet.cut(Part.makeCylinder(2.1,2,V(x,y,-2)))
for sx in [-1,1]:
    extension=Part.makeBox(20.8,20,2,V(148,-10,-2))
    bend=Part.makeCylinder(4,20,V(168.8,-10,-4),V(0,1,0)).cut(Part.makeCylinder(2,20,V(168.8,-10,-4),V(0,1,0)))
    bend=bend.common(Part.makeBox(4,20,4,V(168.8,-10,-4)))
    leg=Part.makeBox(2,20,14,V(170.8,-10,-18))
    for y in [-5,5]:leg=leg.cut(Part.makeCylinder(1.7,2,V(170.8,y,-11),V(1,0,0)))
    tab=extension.fuse(bend).fuse(leg).removeSplitter()
    if sx<0:tab.rotate(V(),V(0,0,1),180)
    sheet=sheet.fuse(tab).removeSplitter()

def annulus(ro,ri,h,org,axis=V(0,0,1)):
    return Part.makeCylinder(ro,h,org,axis).cut(Part.makeCylinder(ri,h,org,axis))
def hexx(r,h,org):
    pts=[org+V(r*math.cos(j*math.pi/3),r*math.sin(j*math.pi/3),0) for j in range(6)]
    return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,h))
def zfastener(name,x,y,zheadbase,length,diam=2,reverse=False):
    # Local base z=0 e topo do suporte z=zheadbase; refletor abaixo de zero.
    shaft=Part.makeCylinder(diam/2,length,V(x,y,zheadbase+.5-length))
    head=Part.makeCylinder(1.8 if diam==2 else 2.75,1.8 if diam==2 else 3,V(x,y,zheadbase+.5))
    w1=annulus(2,1.1,.5,V(x,y,zheadbase));w2=annulus(2,1.1,.5,V(x,y,-2.5))
    nut=hexx(2.25,1.6,V(x,y,-4.1)).cut(Part.makeCylinder(1,1.6,V(x,y,-4.1)))
    pieces=[('Parafuso',shaft.fuse(head)),('Arruelas',Part.makeCompound([w1,w2])),('Porca',nut)]
    for suffix,sh in pieces:
        if reverse:sh.rotate(V(),V(1,0,0),180);sh.translate(V(0,0,-2))
        add(name+'_'+suffix,sh,'Inox A2; M2x%d; roscas simplificadas'%length,(.48,.52,.55),'Fixadores')

# Quatro grampos por PCB, sem furos novos nas placas radiantes.
for cx in [-96.,0.,96.]:
    for sx in [-1,1]:
        for y in [-14.,14.]:
            edge=cx+sx*44; x=edge+sx*1.5;idx=len(p['fixacoes_radiantes'])+1
            sh=Part.makeBox(7,5,14.949,V(-4,-2.5,0)).fuse(Part.makeBox(3,5,2.810,V(0,-2.5,14.949)))
            sh=sh.fuse(Part.makeBox(2,5,2,V(-2,-2.5,15.759))).cut(Part.makeCylinder(1.1,20,V(1.5,0,-1))).removeSplitter()
            if sx<0:sh.rotate(V(),V(0,0,1),180)
            sh.translate(V(edge,y,0));add('Grampo_R%02d'%idx,sh,'POM natural usinado',(.85,.86,.8),'Suportes_POM')
            sheet=sheet.cut(Part.makeCylinder(1.1,2,V(x,y,-2)))
            zfastener('M2_R%02d'%idx,x,y,17.759,25)
            p['fixacoes_radiantes'].append(dict(x=x,y=y,edge=edge,sentido=sx,celula_x=cx))

# Quatro grampos invertidos para C02. Apoiam na face superior do cobre de massa.
for edge,sx in [(p['divisor']['x_min'],-1),(p['divisor']['x_max'],1)]:
    for y in [-12.,12.]:
        idx=len(p['fixacoes_divisor'])+1;x=edge+sx*1.5
        seat=33.196; lip=34.836; top=36.836
        sh=Part.makeBox(7,5,seat,V(-4,-2.5,0)).fuse(Part.makeBox(3,5,top-seat,V(0,-2.5,seat)))
        sh=sh.fuse(Part.makeBox(2,5,2,V(-2,-2.5,lip))).cut(Part.makeCylinder(1.1,40,V(1.5,0,-1))).removeSplitter()
        if sx<0:sh.rotate(V(),V(0,0,1),180)
        sh.translate(V(edge,-y,0));sh.rotate(V(),V(1,0,0),180);sh.translate(V(0,0,-2))
        add('Grampo_D%02d'%idx,sh,'POM natural usinado',(.85,.86,.8),'Suportes_POM')
        sheet=sheet.cut(Part.makeCylinder(1.1,2,V(x,y,-2)))
        zfastener('M2_D%02d'%idx,x,-y,top,45,reverse=True)
        p['fixacoes_divisor'].append(dict(x=x,y=y,edge=edge,sentido=sx))
sheet=sheet.removeSplitter();assert len(sheet.Solids)==1 and sheet.isValid()
d.getObject('Refletor_Al2mm').Shape=sheet;critical.append(d.getObject('Refletor_Al2mm'))
prop(d.getObject('Refletor_Al2mm'),'Alteracao_RF','Furos dos suportes e linguetas finais ainda sem HFSS de fechamento completo')

# Flanges: canal na face interna; quatro furos de linguetas no conjunto.
for sx,label in [(-1,'Inferior'),(1,'Superior')]:
    flange=Part.makeCylinder(55,4.76,V(172.8,0,-10.141),V(1,0,0))
    groove=annulus(51.15,48.65,2.5,V(172.8,0,-10.141),V(1,0,0));flange=flange.cut(groove)
    for y in [-5,5]:flange=flange.cut(Part.makeCylinder(1.7,4.76,V(172.8,y,-11),V(1,0,0)))
    if sx<0:
        for y in [-22,22]:
            cutter=Part.makeCylinder(8.25,4.76,V(172.8,y,-25),V(1,0,0)).common(Part.makeBox(4.76,14,20,V(172.8,y-7,-35)))
            flange=flange.cut(cutter)
        flange.rotate(V(0,0,-10.141),V(0,0,1),180)
    add('Flange_'+label,flange,'Aluminio 6061-T6 nominal',(.72,.75,.78),'Flanges')
    gasket=annulus(50.8,49,.3,V(175,0,-10.141),V(1,0,0))
    if sx<0:gasket.rotate(V(0,0,-10.141),V(0,0,1),180)
    add('Junta_'+label,gasket,'EPDM 60 Shore A nominal, comprimido de 0.5 para 0.3 mm',(.12,.13,.14),'Vedacao')
    # M3x12, arruela externa de vedacao, arruela interna e porca.
    for iy,y in enumerate([-5,5]):
        screw=Part.makeCylinder(1.5,12,V(166.06,y,-11),V(1,0,0)).fuse(Part.makeCylinder(2.75,3,V(178.06,y,-11),V(1,0,0)))
        outer=annulus(3.5,1.7,.5,V(177.56,y,-11),V(1,0,0));inner=annulus(3.5,1.7,.5,V(170.3,y,-11),V(1,0,0))
        nut=hexx(3.175,2.4,V()).cut(Part.makeCylinder(1.5,2.4,V()))
        nut.rotate(V(),V(0,1,0),90);nut.translate(V(167.9,y,-11))
        for suffix,shape,mat in [('Parafuso',screw,'Inox A2 M3x12, rosca simplificada'),('Arruela_vedacao',outer,'Arruela M3 com vedacao EPDM, nominal'),('Arruela',inner,'Inox A2 M3'),('Porca',nut,'Inox A2 M3')]:
            if sx<0:shape.rotate(V(0,0,-10.141),V(0,0,1),180)
            add('M3_%s_%d_%s'%(label,iy+1,suffix),shape,mat,(.48,.52,.55),'Fixadores')

# Conectores reais. Porca/arruela movidas segundo a espessura do flange.
raw=Part.read(str(STEP));mask=annulus(16,7.88,4.9,V(.6,0,0),V(1,0,0))
nutpack=raw.common(mask);body=raw.cut(mask);nutpack.translate(V(1.69,0,0))
for tag,y in [('A',-22.),('B',22.)]:
    for suffix,s in [('Corpo',body),('Porca_arruela',nutpack)]:
        sh=s.copy();sh.rotate(V(),V(0,0,1),180);sh.translate(V(-166.66,y,-25))
        o=add('N_'+tag+'_'+suffix,sh,'Amphenol 082-6784; STEP de referencia; subpartes nao tem materiais RF separados',(.65,.67,.7),'Conectores_N')
        prop(o,'Fonte_STEP',str(STEP));prop(o,'Deslocamento_porcas_mm','1.69 em X local do STEP; face anular de assentamento X10.9; flange 4.76')

# Dois cabos de entrada geometricamente identicos por espelhamento.
# Os seis ramais de saida de 134 mm permanecem literalmente os da R16.
for tag,sy in [('A',-1),('B',1)]:
    start=V(-148.61,sy*22.,-25);e=V(2.50916841304,sy*19.1,-35.051)
    b=V(e.x-6,e.y,-25);c=V(e.x,e.y,-31)
    bz=Part.BezierCurve();bz.setPoles([start,start+V(20,0,0),b-V(20,0,0),b]);edge=bz.toShape()
    mid=V(e.x-6+6/math.sqrt(2),e.y,-31+6/math.sqrt(2))
    wire=Part.Wire([edge,Part.Arc(b,mid,c).toShape(),Part.makeLine(c,e)])
    def sweep(r):return wire.makePipeShell([Part.Wire([Part.makeCircle(r,start,V(1,0,0))])],True,False)
    inside=sweep(.45975);dielectric=sweep(1.515);outside=sweep(1.7905)
    for kind,shape,mat,col in [('Vivo',inside,'Cobre prateado',(.76,.63,.37)),('PTFE',dielectric.cut(inside),'PTFE',(.86,.87,.84)),('Blindagem',outside.cut(dielectric),'UT-141C cobre',(.72,.42,.18))]:
        add('Entrada_'+tag+'_'+kind,shape,mat,col,'Cabos_entrada')
    shrink_path=Part.Wire([bz.toShape(bz.FirstParameter,edge.getParameterByLength(19.05))])
    def sleeve(r):return shrink_path.makePipeShell([Part.Wire([Part.makeCircle(r,start,V(1,0,0))])],True,False)
    o=add('Termorretratil_'+tag,sleeve(2.15).cut(sleeve(1.8)),'Termorretratil do kit N; comprimento19.05 de catalogo; diametro montado4.3 nominal',(.15,.16,.17),'Cabos_entrada')
    prop(o,'Representacao','Espessura e posicao finais dependem da retracao e montagem; representa protecao no trecho de cabo junto ao conector')
    p['cabos_entrada'].append(dict(porta=tag,comprimento_eixo_entre_planos=wire.Length,raio_dobra_minimo=6.,inicio=[start.x,start.y,start.z],fim=[e.x,e.y,e.z],
      corte='Acrescentar preparo de solda/encaixe do conector conforme desenho Amphenol. Nao usar este percurso como comprimento de corte pronto.'))

assert abs(p['cabos_entrada'][0]['comprimento_eixo_entre_planos']-p['cabos_entrada'][1]['comprimento_eixo_entre_planos'])<1e-8
params=d.addObject('App::FeaturePython','Parametros_R17');prop(params,'Dimensoes_JSON',json.dumps(p,ensure_ascii=False));prop(params,'Regeneracao','r17_mecanica.py; BREP parametrizado pelo script, sem juntas cinematicas')
d.recompute()
print('GEOMETRIA_PRONTA_CONFERINDO_INTERFERENCIAS',flush=True)
objects=[o for o in d.Objects if o.isDerivedFrom('Part::Feature') and not o.Shape.isNull()]
boxes=[o.Shape.optimalBoundingBox(False,False) for o in objects]
p['envelope_completo_mm']=[min(getattr(b,k) for b in boxes) for k in ['XMin','YMin','ZMin']]+[max(getattr(b,k) for b in boxes) for k in ['XMax','YMax','ZMax']]
bad=[];tested=0
for a in critical:
    aa=a.Shape.BoundBox
    for b in objects:
        if a.Name==b.Name or (b in critical and b.Name<a.Name):continue
        bb=b.Shape.BoundBox
        if any(min(getattr(aa,k+'Max'),getattr(bb,k+'Max'))-max(getattr(aa,k+'Min'),getattr(bb,k+'Min'))<1e-6 for k in 'XYZ'):continue
        tested+=1;vol=a.Shape.common(b.Shape).Volume
        if vol>1e-5:bad.append(dict(a=a.Name,b=b.Name,volume_mm3=vol))
unchanged={n:abs(sh.Volume-d.getObject(n).Shape.Volume) for n,sh in original.items() if n!='Refletor_Al2mm'}
assert max(unchanged.values())<1e-8
report=dict(estado='PRELIMINAR',modo=MODE,objetos_fisicos=len(objects),solidos=sum(len(o.Shape.Solids) for o in objects),validos=all(o.Shape.isValid() for o in objects),
 pares_testados=tested,intersecoes=bad,originais_inalterados=unchanged,
 fonte_sha256=hashlib.sha256(SRC.read_bytes()).hexdigest(),STEP_sha256=hashlib.sha256(STEP.read_bytes()).hexdigest())
(OUT/'verificacao_cad.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'dimensoes.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'cores.json').write_text(json.dumps(colors),encoding='utf-8')
native=OUT/'Antena_DN100_R17_PRELIMINAR.FCStd';d.saveAs(str(native))
if bad:print('INTERSECOES',json.dumps(bad,ensure_ascii=False),flush=True)
else:
    Import.export(objects,str(OUT/'Antena_DN100_R17_PRELIMINAR.step'))
    for name in ['Refletor_Al2mm','Flange_Inferior','Flange_Superior','Grampo_R01','Grampo_D01']:
        d.getObject(name).Shape.exportStep(str(OUT/(name+'.step')))

# Chapa planificada: coordenadas no plano neutro; K deve ser calibrado pela oficina.
flat=Part.makeBox(296,90,2,V(-148,-45,0))
ext=20.8+BA+14
for sx in [-1,1]:
    tongue=Part.makeBox(ext,20,2,V(148,-10,0))
    for y in [-5,5]:tongue=tongue.cut(Part.makeCylinder(1.7,2,V(168.8+BA+7,y,0)))
    if sx<0:tongue.rotate(V(),V(0,0,1),180)
    flat=flat.fuse(tongue)
for x,y in feedholes:flat=flat.cut(Part.makeCylinder(2.1,2,V(x,y,0)))
for item in p['fixacoes_radiantes']+p['fixacoes_divisor']:flat=flat.cut(Part.makeCylinder(1.1,2,V(item['x'],item['y'],0)))
flat=flat.removeSplitter(); fd=A.newDocument('Chapa_R17_Planificada')
fo=fd.addObject('Part::Feature','Chapa_planificada');fo.Shape=flat
prop(fo,'Dobra','Duas extremidades 90 graus; Ri2; K0.4 nominal; BA %.9f. Abas laterais conforme dimensoes.json'%BA)
fd.recompute();fd.saveAs(str(OUT/'Refletor_planificado_PRELIMINAR.FCStd'));flat.exportStep(str(OUT/'Refletor_planificado_PRELIMINAR.step'))
A.closeDocument(fd.Name);A.closeDocument(d.Name)
print('R17_MECANICA',len(objects),'intersecoes',len(bad),flush=True)
