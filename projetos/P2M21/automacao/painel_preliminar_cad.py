"""Mecanica R18: BREP C12 preservado; sem simulacao RF. Executar no FreeCAD."""
from pathlib import Path
import json, math, hashlib, csv
import FreeCAD as A, Part, Import

WORK=Path('D:/dev/EMBRAER/P2M21/R18_Mecanica_Preliminar')
SRC=Path('D:/dev/EMBRAER/P2M21/R17_Dez_Celulas_78mm')
WORK.mkdir(exist_ok=True)
cfg=json.loads((SRC/'configuracao.json').read_text())
doc=A.openDocument(str(SRC/cfg['cad_native']))
doc.Label='P2M21 R18 — PRELIMINAR — 10 placas / 78 mm'
V=A.Vector
colors={};bom=[];critical=[]
parts=doc.addObject('App::DocumentObjectGroup','Mecanica_R18')
def prop(o,k,v):
    if k not in o.PropertiesList:o.addProperty('App::PropertyString',k,'Rastreabilidade')
    setattr(o,k,str(v))
def add(name,shape,mat,color,group=parts):
    assert shape.isValid() and shape.Volume>0,name
    o=doc.addObject('Part::Feature',name);o.Shape=shape
    prop(o,'Material_nominal',mat);prop(o,'Estado','PRELIMINAR — nao liberado para fabricacao')
    if group:group.addObject(o)
    colors[name]=color;return o
for o in doc.Objects:
    if not o.isDerivedFrom('Part::Feature') or o.Shape.isNull():continue
    mat=getattr(o,'Material_nominal','')
    colors[o.Name]=[.70,.39,.10] if 'copper' in mat.lower() or 'Cu' in o.Name or 'Vivo' in o.Name else [.12,.45,.27] if 'RO4350' in o.Name else [.86,.87,.88] if 'PTFE' in o.Name else [.67,.70,.72]
    if o.Name.startswith('C'):prop(o,'Origem','C12; copia por translacao, geometria RF preservada')

# Face refletora preservada. Novos furos mecanicos e dobra requerem futura RF.
rh,rw,t=968.,162.,2.
ri=2.;ro=ri+t;K=.4;ba=math.pi/2*(ri+K*t);leg=66.
plate=doc.getObject('Refletor_Al2mm').Shape.copy()
clip_positions=[]
for c in cfg['celulas']:
    for sx in [-1,1]:
        for sy in [-1,1]:
            edge=c['x']+sx*92
            y=c['y']+sy*25
            clip_positions.append((c['nome'],sx,edge,y))
            plate=plate.cut(Part.makeCylinder(1.1,2,V(edge+sx*1.5,y,-2)))
mounts=[(x,y) for x in [-320,320] for y in [-50,50]]
for x,y in mounts:plate=plate.cut(Part.makeCylinder(3.25,2,V(x,y,-2)))
outer=Part.makeCylinder(ro,rw,V(-484,-81,-4),V(0,1,0))
inner=Part.makeCylinder(ri,rw,V(-484,-81,-4),V(0,1,0))
quarter=outer.cut(inner).common(Part.makeBox(4,rw,4,V(-488,-81,-4)))
base=Part.makeBox(2,rw,leg,V(-488,-81,-70))
for y in [-24,24]:
    hole=Part.makeCylinder(8.25,4,V(-489,y,-40),V(1,0,0))
    hole=hole.common(Part.makeBox(4,14,40,V(-489,y-7,-60)))
    base=base.cut(hole)
sheet=plate.fuse(quarter).fuse(base).removeSplitter()
assert len(sheet.Solids)==1 and sheet.isValid()
refl=doc.getObject('Refletor_Al2mm');refl.Shape=sheet;refl.Label='Refletor Al 5052 2 mm — base dobrada — PRELIMINAR'
prop(refl,'Material_nominal','Aluminio 5052; tempera e acabamento a definir')
prop(refl,'Dobra','90 graus; Ri 2 mm; K 0.4 hipotetico, confirmar ferramental')
prop(refl,'Alteracao_RF','40 furos M2 + 4 furos interface + dobra: nao simulados')
critical.append(refl)

# Grampos de POM de 5 mm de largura, sem perfurar as PCBs.
clip_group=doc.addObject('App::DocumentObjectGroup','Grampos_POM')
fix_group=doc.addObject('App::DocumentObjectGroup','Fixadores_M2')
for i,(cell,sx,edge,y) in enumerate(clip_positions,1):
    sh=Part.makeBox(7,5,14.949,V(-4,-2.5,0))
    sh=sh.fuse(Part.makeBox(3,5,2.810,V(0,-2.5,14.949)))
    sh=sh.fuse(Part.makeBox(2,5,2,V(-2,-2.5,15.759)))
    sh=sh.cut(Part.makeCylinder(1.1,20,V(1.5,0,-1))).removeSplitter()
    if sx<0:sh.rotate(V(),V(0,0,1),180)
    sh.translate(V(edge,y,0))
    clip=add('Grampo_%02d'%i,sh,'POM natural; usinado', [.83,.85,.80],clip_group)
    prop(clip,'Celula',cell);prop(clip,'Dimensoes','Largura 5; apoio Z14.949; folga superior PCB 0.05 mm')
    critical.append(clip)
    x=edge+sx*1.5
    washer_top=Part.makeCylinder(2,.5,V(x,y,17.759)).cut(Part.makeCylinder(1.1,.5,V(x,y,17.759)))
    washer_bot=Part.makeCylinder(2,.5,V(x,y,-2.5)).cut(Part.makeCylinder(1.1,.5,V(x,y,-2.5)))
    shaft=Part.makeCylinder(1,25,V(x,y,-6.741))
    head=Part.makeCylinder(1.8,1.8,V(x,y,18.259))
    screw=add('Parafuso_M2_%02d'%i,shaft.fuse(head),'Inox A2; M2x25; rosca simplificada',[.48,.52,.56],fix_group)
    washers=add('Arruelas_M2_%02d'%i,Part.makeCompound([washer_top,washer_bot]),'Inox A2; 2 arruelas por fixacao',[.52,.56,.60],fix_group)
    pts=[V(x+2.25*math.cos(j*math.pi/3),y+2.25*math.sin(j*math.pi/3),-4.1) for j in range(6)]
    nut=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,1.6)).cut(Part.makeCylinder(1,1.6,V(x,y,-4.1)))
    add('Porca_M2_%02d'%i,nut,'Inox A2; M2; rosca simplificada',[.48,.52,.56],fix_group)

# STEP fornecido pelo usuario. Isolar e transladar so a porca/arruela de sua pose de catalogo.
raw=Part.read('D:/dev/EMBRAER/82-6784.stp')
isolate=Part.makeCylinder(16,3.851,V(.6,0,0),V(1,0,0)).cut(Part.makeCylinder(7.88,3.851,V(.6,0,0),V(1,0,0)))
nutpack=raw.common(isolate);body=raw.cut(isolate)
assert nutpack.isValid() and body.isValid()
nutpack.translate(V(4.25,0,0))
ng=doc.addObject('App::DocumentObjectGroup','Entradas_N')
for tag,y in [('A',-24),('B',24)]:
    for label,s,color in [('Corpo',body,[.65,.68,.70]),('Porca_arruela',nutpack,[.53,.56,.59])]:
        z=s.copy();z.rotate(V(),V(0,0,1),180);z.translate(V(-477.3,y,-40))
        n=add('N_'+tag+'_'+label,z,'Amphenol 082-6784; STEP do fabricante',color,ng)
        prop(n,'Origem','D:/dev/EMBRAER/82-6784.stp')
        prop(n,'Montagem','Face da junta X=-488; chapa 2 mm; porca/arruela movidas 4.25 mm do STEP de catalogo')
        critical.append(n)

# Cabos de entrada retos, propostos ate a interface reservada central. Sem RF/corte final.
wire_group=doc.addObject('App::DocumentObjectGroup','Entradas_cabo_propostas')
length=459.25
for tag,y in [('A',-24),('B',24)]:
    org=V(-459.25,y,-40);axis=V(1,0,0)
    sh=Part.makeCylinder(1.7905,length,org,axis).cut(Part.makeCylinder(1.515,length,org,axis))
    add('IN_'+tag+'_Blindagem',sh,'UT-141C — percurso proposto, nao liberado',[.72,.42,.18],wire_group)
    add('IN_'+tag+'_PTFE',Part.makeCylinder(1.515,length,org,axis).cut(Part.makeCylinder(.45975,length,org,axis)),'PTFE',[.88,.88,.85],wire_group)
    add('IN_'+tag+'_Vivo',Part.makeCylinder(.45975,length,org,axis),'Cobre prateado',[.76,.63,.37],wire_group)

reserve=add('Reserva_distribuicao_2x10',Part.makeBox(820,130,20,V(-410,-65,-65)),
 'ENVELOPE — nao e placa fabricavel',[.18,.45,.77])
prop(reserve,'Estado','RESERVA DE ESPACO; duas redes 1:10 ainda nao projetadas')
prop(reserve,'Interfaces','2 entradas N; 20 conexoes A/B das 10 PCBs. Sem continuidade RF nesta reserva.')
params=doc.addObject('App::FeaturePython','Parametros_R18')
for k,v in dict(PassoVertical=48,PassoColunas=78,PassoPlacas=192,AlturaNucleo=14.949,EspessuraAl=2,LarguraGrampo=5,RaioDobra=2).items():
    params.addProperty('App::PropertyLength',k,'Dimensoes');setattr(params,k,v)
prop(params,'Reconstrucao','Alterar script/configuracao e regenerar; BREP posicionado, sem juntas cinematicas')
prop(params,'Liberacao','PRELIMINAR; RF 10 placas interrompida; rede externa e fechamento pendentes')
doc.recompute()

# Conferencia das interfaces acrescentadas, excluindo o envelope que nao e material.
shapes=[o for o in doc.Objects if o.isDerivedFrom('Part::Feature') and not o.Shape.isNull() and o!=reserve]
bad=[o.Name for o in shapes if not o.Shape.isValid()]
assert not bad,bad
inter=[];tested=0
for a in critical:
    aa=a.Shape.BoundBox
    for b in shapes:
        if a.Name==b.Name or (b in critical and b.Name<a.Name):continue
        bb=b.Shape.BoundBox
        if any(min(getattr(aa,k+'Max'),getattr(bb,k+'Max'))-max(getattr(aa,k+'Min'),getattr(bb,k+'Min'))<1e-6 for k in 'XYZ'):continue
        tested+=1;vol=a.Shape.common(b.Shape).Volume
        if vol>1e-5:inter.append(dict(a=a.Name,b=b.Name,volume_mm3=vol))
report=dict(estado='PRELIMINAR',formas=len(shapes),solidos_validos=not bad,pares_testados=tested,intersecoes=inter,
 observacao='Interfaces novas conferidas; roscas de fixadores simplificadas. Contatos de montagem nao sao analise estrutural.',
 fonte_cad_sha256=hashlib.sha256((SRC/cfg['cad_native']).read_bytes()).hexdigest(),
 conector_step_sha256=hashlib.sha256(Path('D:/dev/EMBRAER/82-6784.stp').read_bytes()).hexdigest())
(WORK/'verificacao_cad.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(WORK/'cores.json').write_text(json.dumps(colors),encoding='utf-8')
doc.saveAs(str(WORK/'P2M21_R18_PRELIMINAR.FCStd'))
sheet.exportStep(str(WORK/'Refletor_dobrado_PRELIMINAR.step'))

# Chapa plana, geometria de corte derivada dos mesmos centros; BA e proposta de oficina.
xmin=-484-ba-leg
flat=Part.makeBox(968+ba+leg,rw,t,V(xmin,-81,0))
for p in cfg['portas']:flat=flat.cut(Part.makeCylinder(2.1,t,V(p['x'],p['y'],0)))
for _,sx,x,y in clip_positions:flat=flat.cut(Part.makeCylinder(1.1,t,V(x+sx*1.5,y,0)))
for x,y in mounts:flat=flat.cut(Part.makeCylinder(3.25,t,V(x,y,0)))
for y in [-24,24]:
    x=-484-ba-36
    flat=flat.cut(Part.makeCylinder(8.25,t,V(x,y,0)).common(Part.makeBox(20,14,t,V(x-10,y-7,0))))
fd=A.newDocument('Chapa_R18_PRELIMINAR');fo=fd.addObject('Part::Feature','Chapa_planificada');fo.Shape=flat
prop(fo,'Dobra','Ri=2; K=0.4; 90 graus; BA=%.6f mm; confirmar em oficina'%ba)
fd.recompute();fd.saveAs(str(WORK/'Refletor_planificado_PRELIMINAR.FCStd'));flat.exportStep(str(WORK/'Refletor_planificado_PRELIMINAR.step'))
params_out=dict(placas=10,radiadores=40,conexoes=20,pcb_mm=[70,184,.76],passo_colunas_mm=78,passo_radiadores_mm=48,passo_placas_mm=192,
 nucleo_z_mm=14.949,folga_lateral_mm=8,folga_vertical_mm=8,refletor_face_mm=[968,162,2],base_profundidade_mm=70,
 chapa_plana_mm=[968+ba+leg,162,2],dobra=dict(Ri_mm=2,K=.4,BA_mm=ba),
 fixacoes_pom=[dict(celula=c,x=x+sx*1.5,y=y) for c,sx,x,y in clip_positions],montagem_mastro_interface=mounts,
 recortes_N=dict(diametro=16.5,entre_planos=14,y=[-24,24],z=-40,x_plano=-484-ba-36),
 entrada_cabos_proposta_mm=length,saidas_cabos_ensaio_mm=50,rede_externa='PENDENTE — 2 redes 1:10',
 material_fonte='RO4350B 0.76 mm, Cu35um, ENIG, sem mascara RF; C12 sem alteracao',estado='PRELIMINAR')
(WORK/'dimensoes.json').write_text(json.dumps(params_out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
A.closeDocument(fd.Name);A.closeDocument(doc.Name)
check=A.openDocument(str(WORK/'P2M21_R18_PRELIMINAR.FCStd'))
assert len([o for o in check.Objects if o.isDerivedFrom('Part::Feature') and not o.Shape.isNull()])==len(shapes)+1
assert all(o.Shape.isValid() for o in check.Objects if o.isDerivedFrom('Part::Feature') and not o.Shape.isNull())
A.closeDocument(check.Name)
print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
