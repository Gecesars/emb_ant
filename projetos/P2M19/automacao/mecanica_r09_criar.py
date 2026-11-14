"""P2M19: montagem mecanica preliminar. Executar no FreeCADCmd; nunca inicia RF.

Conserva todos os 328 corpos das oito PCBs C12 e o refletor original oculto.
As pecas de fabricacao sao adicionais; furos novos ficam rastreados em CSV.
"""
from pathlib import Path
import FreeCAD as A, Part, Import
import json, math, hashlib, csv, shutil

REPO=Path('D:/dev/EMBRAER/emb_ant')
SRC=REPO/'projetos/P2M19/continuacao_72mm_ref146_14passes'
OUT=REPO/'projetos/P2M19/mecanica_R09_PRELIMINAR'
WORK=Path('D:/dev/EMBRAER/P2M19/R09_Mecanica_Rede')
OUT.mkdir(parents=True,exist_ok=True); WORK.mkdir(parents=True,exist_ok=True)
(OUT/'referencias').mkdir(exist_ok=True)
cfg=json.loads((SRC/'configuracao.json').read_text())
doc=A.openDocument(str(SRC/cfg['cad_native']))
doc.Label='P2M19 R09 — PRELIMINAR — base e rede planejada'
V=A.Vector
colors={}; final=[]; hidden=[]; holes=[]; check=[]
rf=[o for o in doc.Objects if o.isDerivedFrom('Part::Feature') and not o.Shape.isNull()]
def sha_shape(s):return hashlib.sha256(s.exportBrepToString().encode()).hexdigest()
source_hashes={o.Name:sha_shape(o.Shape) for o in rf}
def meta(o,k,v):
    if k not in o.PropertiesList:o.addProperty('App::PropertyString',k,'Rastreabilidade')
    setattr(o,k,str(v))
def group(name):return doc.addObject('App::DocumentObjectGroup',name)
mech=group('Mecanica_R09'); fast=group('Fixadores'); supports=group('Grampos_POM'); net=group('Rede_PCB_RESERVA'); connectors=group('Entradas_N')
def add(name,shape,mat,col,grp=mech,critical=True):
    assert shape.isValid() and len(shape.Solids)>0 and shape.Volume>0,name
    o=doc.addObject('Part::Feature',name);o.Shape=shape
    meta(o,'Material_nominal',mat);meta(o,'Estado','PRELIMINAR — nao liberado para fabricacao')
    if grp:grp.addObject(o)
    colors[name]=col;final.append(o)
    if critical:check.append(o)
    return o
def primitive(name,kind,**kwargs):
    o=doc.addObject(kind,name)
    for k,v in kwargs.items():setattr(o,k,v)
    hidden.append(o);return o
def cut(name,a,b):
    o=doc.addObject('Part::Cut',name);o.Base=a;o.Tool=b;hidden.append(o);return o
for o in rf:
    mat=getattr(o,'Material_nominal','')
    colors[o.Name]=[.68,.42,.14] if any(t in o.Name for t in ['Cu','Via','Vivo','Solda','PTH']) else [.18,.48,.30] if 'RO4350' in o.Name else [.87,.88,.85] if 'PTFE' in o.Name else [.68,.71,.74]
    if o.Name!='Refletor_Al2mm':final.append(o)
original=doc.getObject('Refletor_Al2mm');original.Label='REF RF original 146x776x2 — preservado e oculto'
hidden.append(original)

# Grampos de borda. Quatro por PCB: nao perfuram laminado/cobre da C12.
clip_positions=[]
for cell in cfg['celulas']:
    for sx in [-1,1]:
        for sy in [-1,1]:clip_positions.append((cell['nome'],sx,cell['x']+sx*92,cell['y']+sy*25))
plate=original.Shape.copy()
for p in cfg['portas']:holes.append(dict(peca='Refletor',funcao='Passagem coax existente no RF',x=p['x'],y=p['y'],z=-2,diametro_mm=4.2,eixo='Z',origem='RF preservado'))
for _,sx,x,y in clip_positions:
    xx=x+sx*1.5;plate=plate.cut(Part.makeCylinder(1.1,2,V(xx,y,-2)))
    holes.append(dict(peca='Refletor',funcao='Grampo POM M2',x=xx,y=y,z=-2,diametro_mm=2.2,eixo='Z',origem='NOVO mecanico'))
rail_mounts=[(x,y) for x in [-374,0,374] for y in [-52,52]]
for x,y in rail_mounts:
    plate=plate.cut(Part.makeCylinder(2.25,2,V(x,y,-2)))
    holes.append(dict(peca='Refletor',funcao='Reforco L M4',x=x,y=y,z=-2,diametro_mm=4.5,eixo='Z',origem='NOVO mecanico'))
board_defs=[('Central_duplo_1x2',0,60),('Inferior_duplo_1x4',-192,39),('Superior_duplo_1x4',192,39)]
board_holes=[]
for name,x0,l in board_defs:
    for sx in [-1,1]:
        for sy in [-1,1]:
            x=x0+sx*(l/2-4);y=sy*35;board_holes.append((name,x,y))
            plate=plate.cut(Part.makeCylinder(1.6,2,V(x,y,-2)))
            holes.append(dict(peca='Refletor',funcao='Suporte PCB rede M3',x=x,y=y,z=-2,diametro_mm=3.2,eixo='Z',origem='NOVO reserva'))
refl=add('Refletor_fabricacao',plate,'Aluminio 5052, 2 mm, tempera/acabamento a definir',[.71,.73,.76])
meta(refl,'Alteracao_RF','Somente furos mecanicos novos; face/envelope RF preservados. Furos novos e demais pecas nao simulados.')

# Base usinada 4 mm: recortes double-D e rebaixo interno que mantem parede de montagem 2 mm para N.
base=primitive('Base_bruta','Part::Box',Length=4,Width=146,Height=70,Placement=A.Placement(V(-396,-73,-70),A.Rotation()))
base.Label='Base bruta editavel 4 x 146 x 70 mm'
rotX=A.Rotation(V(0,0,1),V(1,0,0))
for tag,y in [('A',-24),('B',24)]:
    cy=primitive('N_'+tag+'_furo_circular','Part::Cylinder',Radius=8.25,Height=6,Placement=A.Placement(V(-397,y,-45),rotX))
    bx=primitive('N_'+tag+'_limite_planos','Part::Box',Length=6,Width=14,Height=24,Placement=A.Placement(V(-397,y-7,-57),A.Rotation()))
    tool=doc.addObject('Part::Common','N_'+tag+'_duplo_D');tool.Base=cy;tool.Tool=bx;hidden.append(tool)
    base=cut('Base_recorte_'+tag,base,tool)
    cb=primitive('N_'+tag+'_rebaixo','Part::Cylinder',Radius=16,Height=2,Placement=A.Placement(V(-394,y,-45),rotX))
    base=cut('Base_rebaixada_'+tag,base,cb)
    holes.append(dict(peca='Base',funcao='N '+tag+' double-D 14 entre planos; rebaixo D32x2 interno',x=-396,y=y,z=-45,diametro_mm=16.5,eixo='X',origem='STEP 082-6784 / parede2mm'))
for tag,y in [('E',-55),('D',55)]:
    cy=primitive('Base_M4_'+tag,'Part::Cylinder',Radius=2.25,Height=6,Placement=A.Placement(V(-397,y,-12),rotX))
    base=cut('Base_furada_'+tag,base,cy)
    holes.append(dict(peca='Base',funcao='Fixacao pe reforco M4',x=-396,y=y,z=-12,diametro_mm=4.5,eixo='X',origem='NOVO'))
doc.recompute();base.Label='Base aluminio 4 mm — N em parede local 2 mm'
meta(base,'Material_nominal','Aluminio 6061-T6 proposto; sem validacao estrutural')
meta(base,'Estado','PRELIMINAR');colors[base.Name]=[.64,.67,.71];final.append(base);check.append(base);mech.addObject(base)
hidden.remove(base)
base_nominal_volume=base.Shape.Volume
brute=doc.getObject('Base_bruta');brute.Height=71;doc.recompute();assert base.Shape.isValid() and base.Shape.Volume>base_nominal_volume
brute.Height=70;doc.recompute();assert abs(base.Shape.Volume-base_nominal_volume)<1e-5

# Dois L20x20x2 longitudinais, com pe soldado 4 mm em cada perfil. Novos metais traseiros, sem validacao EM.
for sign in [-1,1]:
    yy=45 if sign>0 else -65
    sh=Part.makeBox(780,20,2,V(-392,yy,-4)).fuse(Part.makeBox(780,2,20,V(-392,63 if sign>0 else -65,-22)))
    sh=sh.fuse(Part.makeBox(4,20,20,V(-392,yy,-22)))
    sh=sh.cut(Part.makeCylinder(2.25,4,V(-392,sign*55,-12),V(1,0,0)))
    for x,y in rail_mounts:
        if y*sign>0:sh=sh.cut(Part.makeCylinder(2.25,2,V(x,y,-4)))
    for _,sx,x,y in clip_positions:
        if abs(y)>50 and y*sign>0:sh=sh.cut(Part.makeCylinder(1.1,2,V(x+sx*1.5,y,-4)))
    rail=add('Reforco_L_'+('E' if sign<0 else 'D'),sh.removeSplitter(),'Aluminio 6061-T6 proposto; perfil L20x20x2, pe4mm soldado',[.60,.64,.68])
    meta(rail,'Comprimento_mm',780);meta(rail,'Fabricacao','Pe soldado 4mm; solda nao desenhada nem dimensionada; confirmar processo/tempera apos solda')

def washer(r,ri,t,org,axis=V(0,0,1)):return Part.makeCylinder(r,t,org,axis).cut(Part.makeCylinder(ri,t,org,axis))
def nut_shape(radius,ri,h,p,axis=V(0,0,1)):
    pts=[V(radius*math.cos(j*math.pi/3),radius*math.sin(j*math.pi/3),0) for j in range(6)]
    sh=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,h)).cut(Part.makeCylinder(ri,h))
    sh.Placement=A.Placement(p,A.Rotation(V(0,0,1),axis));return sh
for i,(cell,sx,edge,y) in enumerate(clip_positions,1):
    sh=Part.makeBox(7,5,14.949,V(-4,-2.5,0)).fuse(Part.makeBox(3,5,2.810,V(0,-2.5,14.949))).fuse(Part.makeBox(2,5,2,V(-2,-2.5,15.759)))
    sh=sh.cut(Part.makeCylinder(1.1,20,V(1.5,0,-1))).removeSplitter()
    if sx<0:sh.rotate(V(),V(0,0,1),180)
    sh.translate(V(edge,y,0))
    clip=add('Grampo_%02d'%i,sh,'POM natural; largura5mm; apoio14.949mm',[.86,.87,.82],supports)
    meta(clip,'Celula',cell);meta(clip,'Folga','Geometria de retencao nominal: conferir laminado acabado no prototipo')
    x=edge+sx*1.5;bottom=-4 if abs(y)>50 else -2
    add('M2_parafuso_%02d'%i,Part.makeCylinder(1,25,V(x,y,-6.741)).fuse(Part.makeCylinder(1.8,1.8,V(x,y,18.259))),'Inox A2 M2x25; rosca simplificada',[.47,.51,.55],fast)
    add('M2_arruelas_%02d'%i,Part.makeCompound([washer(2,1.1,.5,V(x,y,17.759)),washer(2,1.1,.5,V(x,y,bottom-.5))]),'Inox A2; 2x arruelaM2',[.52,.56,.60],fast)
    add('M2_porca_%02d'%i,nut_shape(2.25,1,1.6,V(x,y,bottom-2.1)),'Inox A2 M2; rosca simplificada',[.47,.51,.55],fast)
# 6 fixacoes M4 de reforcos ao refletor. Cabeca na face frontal, abaixo das PCBs.
for i,(x,y) in enumerate(rail_mounts,1):
    add('M4_refletor_%d'%i,Part.makeCylinder(2,12,V(x,y,-11.2)).fuse(Part.makeCylinder(3.8,3,V(x,y,.8))),'Inox A2 M4x12; rosca simplificada',[.47,.51,.55],fast)
    add('M4_arruelas_%d'%i,Part.makeCompound([washer(4.5,2.2,.8,V(x,y,0)),washer(4.5,2.2,.8,V(x,y,-4.8))]),'Inox A2 M4; 2 arruelas',[.52,.56,.60],fast)
    add('M4_porcas_%d'%i,nut_shape(4.04,2,3.2,V(x,y,-8)),'Inox A2 M4; rosca simplificada',[.47,.51,.55],fast)
for i,y in enumerate([-55,55],1):
    # Cabeca exterior -X, porca interior +X. Eixo reverso para manter cabeça abaixo da base.
    add('M4_base_%d'%i,Part.makeCylinder(2,16,V(-396.8,y,-12),V(1,0,0)).fuse(Part.makeCylinder(3.8,3,V(-399.8,y,-12),V(1,0,0))),'Inox A2 M4x16; rosca simplificada',[.47,.51,.55],fast)
    add('M4_base_arruelas_%d'%i,Part.makeCompound([washer(4.5,2.2,.8,V(-396.8,y,-12),V(1,0,0)),washer(4.5,2.2,.8,V(-388,y,-12),V(1,0,0))]),'Inox A2 M4; 2 arruelas',[.52,.56,.60],fast)
    add('M4_base_porca_%d'%i,nut_shape(4.04,2,3.2,V(-387.2,y,-12),V(1,0,0)),'Inox A2 M4; rosca simplificada',[.47,.51,.55],fast)

# Envelopes honestos da rede planejada, com furos de montagem reais, sem traçado de cobre RF ficticio.
for name,x,l in board_defs:
    sh=Part.makeBox(l,78,1.52,V(x-l/2,-39,-12))
    for bn,hx,hy in board_holes:
        if bn==name:sh=sh.cut(Part.makeCylinder(1.6,1.52,V(hx,hy,-12)))
    b=add('PCB_RESERVA_'+name,sh,'ZYF300CA-C 1.52mm proposto; ENVELOPE SEM COBRE',[.17,.37,.64],net)
    meta(b,'Liberacao','PLANEJAMENTO: nao e PCB pronta para fabricar; sem continuidade RF demostrada')
for i,(bn,x,y) in enumerate(board_holes,1):
    add('Espacador_rede_M3_%02d'%i,washer(2.5,1.6,8.48,V(x,y,-10.48)),'POM natural; altura8.48mm',[.86,.87,.82],net)
    add('M3_rede_%02d'%i,Part.makeCylinder(1.5,16,V(x,y,-15.5)).fuse(Part.makeCylinder(2.75,2,V(x,y,.5))),'Inox A2 M3x16; rosca simplificada',[.47,.51,.55],fast)
    add('M3_rede_arruelas_%02d'%i,Part.makeCompound([washer(3.5,1.6,.5,V(x,y,0)),washer(3.5,1.6,.5,V(x,y,-12.5))]),'Inox A2 M3; 2 arruelas',[.52,.56,.60],fast)
    add('M3_rede_porca_%02d'%i,nut_shape(3.18,1.5,2.4,V(x,y,-14.9)),'Inox A2 M3; rosca simplificada',[.47,.51,.55],fast)

# Modelo fornecido: nut/washer extraido da pose original e deslocado como no R18 verificado.
conn_source=REPO/'projetos/P2M21/mecanica_preliminar_R18/referencias/82-6784.stp'
raw=Part.read(str(conn_source));isolator=Part.makeCylinder(16,3.851,V(.6,0,0),V(1,0,0)).cut(Part.makeCylinder(7.88,3.851,V(.6,0,0),V(1,0,0)))
nutpack=raw.common(isolator);body=raw.cut(isolator)
connector_boolean_volume_delta=nutpack.Volume+body.Volume-raw.Volume
assert abs(connector_boolean_volume_delta)/raw.Volume<2e-5
nutpack.translate(V(4.25,0,0))
for tag,y in [('A',-24),('B',24)]:
    for label,s,col in [('Corpo',body,[.71,.74,.76]),('Porca_arruela',nutpack,[.55,.58,.61])]:
        sh=s.copy();sh.rotate(V(),V(0,0,1),180);sh.translate(V(-385.3,y,-45))
        o=add('N_'+tag+'_'+label,sh,'Amphenol 082-6784; STEP fornecido',[*col],connectors)
        meta(o,'Montagem','Plano externoX=-396; parede local2mm; porca/arruela deslocadas4.25mm da poseSTEP')
        meta(o,'Referencia','referencias/82-6784.stp; nao e modelo RF interno qualificado')
shutil.copy2(conn_source,OUT/'referencias/82-6784.stp')

params=doc.addObject('App::FeaturePython','Parametros_R09')
for k,v in dict(PassoVertical=48,PassoColunas=72,PassoPlacas=192,AlturaNucleo=14.949,EspessuraRefletor=2,EspessuraBase=4,EspessuraLocalN=2,LarguraGrampo=5).items():
    params.addProperty('App::PropertyLength',k,'Dimensoes');setattr(params,k,v)
meta(params,'Reconstrucao','Base e seus recortes: primitivas/cortes nativos editaveis. Demais pecas: BREP reconstruivel pelo script. Montagem posicionada, sem juntas cinematicas.')
meta(params,'Estado','PRELIMINAR; sem calculo estrutural/vento ou RF das adicoes; sem radome, compra ou liberacao')
doc.recompute()
assert all(o.Shape.isValid() and o.Shape.Volume>0 for o in final)
assert all(sha_shape(doc.getObject(k).Shape)==v for k,v in source_hashes.items()),'RF alterado'
report=dict(estado='PRELIMINAR',rf_corpos_preservados=328,refletor_RF_original_preservado_oculto=True,geometria_RF_hashes_iguais=True,
    corpos_finais=len(final),solidos_finais=sum(len(o.Shape.Solids) for o in final),todos_validos=True,
    base_parametro_70_71_70_testado=True,fonte_cad_sha256=hashlib.sha256((SRC/cfg['cad_native']).read_bytes()).hexdigest(),
    conector_step_sha256=hashlib.sha256(conn_source.read_bytes()).hexdigest(),conector_boolean_delta_volume_mm3=connector_boolean_volume_delta,
    observacao='Montagem posicionada, sem juntas cinematicas. Interferencias e cabos em etapa seguinte; nenhuma analise RF/estrutural.')
(OUT/'cores.json').write_text(json.dumps(colors,indent=2),encoding='utf-8')
(OUT/'objetos.json').write_text(json.dumps(dict(finais=[o.Name for o in final],ocultos=[o.Name for o in hidden],criticos=[o.Name for o in check],rf_hashes=source_hashes),indent=2),encoding='utf-8')
(OUT/'verificacao_inicial.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
with (OUT/'furacao_PRELIMINAR.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(holes[0]),delimiter=';');w.writeheader();w.writerows(holes)
dim=dict(unidade='mm',sistema='X vertical positivo para cima, Y horizontal, Z para frente',estado='PRELIMINAR',
    refletor=dict(X=[-388,388],Y=[-73,73],Z=[-2,0],material='Al5052 2mm proposto'),
    base=dict(X=[-396,-392],Y=[-73,73],Z=[-70,0],material='Al6061-T6 proposto',espessura=4,parede_local_N=2,rebaixo_N=[32,2]),
    reforcos=dict(quantidade=2,perfil='L20x20x2',comprimento=780,pe='4x20x20mm soldado',Y=[[45,65],[-65,-45]],Z=[-22,-2]),
    N=dict(modelo='Amphenol082-6784',plano_fixacao_X=-396,centros_Y=[-24,24],centro_Z=-45,recorte_diametro=16.5,entre_planos=14,terminacao_cabo_X=-367.25),
    PCBs_rede=dict(central=[60,78,1.52],filiais=[39,78,1.52],centros_X=[0,-192,192],Z=[-12,-10.48],furos='M3 Ø3.2, a4mm das bordas'),
    PCBs_radiantes=dict(quantidade=8,dimensoes=[184,70,.76],passo_X=192,passo_Y=72,nucleo_Z=14.949,grampos=32),
    nao_qualificado=['RF das adicoes','cargas de vento','resistencia/rigidez','solda dos pes','vedacao do produto','chicote final','cobre da rede externa'])
(OUT/'dimensoes.json').write_text(json.dumps(dim,ensure_ascii=False,indent=2),encoding='utf-8')
doc.saveAs(str(OUT/'P2M19_R09_PRELIMINAR.FCStd'))
for name,obj in [('Base_aluminio_PRELIMINAR',base),('Refletor_furado_PRELIMINAR',refl)]:
    obj.Shape.exportStep(str(OUT/(name+'.step')))
print(json.dumps(report,indent=2),flush=True)
