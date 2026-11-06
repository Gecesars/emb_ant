"""Gerar as interfaces EM da montagem R01 no FreeCAD. Executar com P1H_R01 apontando à pasta de trabalho."""
import json, os, sys
from pathlib import Path
import FreeCAD as App, Part, Import
repo=Path(__file__).resolve().parents[2]
mechanics=repo/"freecad/mecanica_R01"
sys.path.insert(0,str(mechanics/"fonte"))
import construir as m
from dimensoes import *
V=App.Vector; Z=V(0,0,1); X=V(1,0,0)
out=Path(os.environ["P1H_R01"])/"cad";out.mkdir(parents=True,exist_ok=True)
d=App.openDocument(str(mechanics/"03_Antena_montada.FCStd"))
cad=App.newDocument("R01_EM")
objects=[];manifest={}
def obj(name,sh,material):
    assert not sh.isNull() and sh.isValid(),name
    ob=cad.addObject("Part::Feature",name);ob.Label=name;ob.Shape=sh
    objects.append(ob);manifest[name]=material
def disk(x,y,r,z):
    return Part.Face(Part.Wire([Part.makeCircle(r,V(x,y,z),Z)]))
def cyl(x,y,r,z,h):
    return Part.makeCylinder(r,h,V(x,y,z))
def polygon(pts,z):
    q=[V(x,y,z) for x,y in pts];return Part.Face(Part.makePolygon(q+[q[0]]))
def group(ss):return Part.makeCompound(ss)
def shifted(sh,dx):
    s=sh.copy();s.translate(V(dx,0,0));return s
def xy_perforate(sh,holes,z,h):
    return sh.cut(group([cyl(x,y,r,z,h) for x,y,r in holes]))
obj("Chassi",d.Chapa_Aluminio_2mm.Shape,"AL5052")
for g,material in [(d.Apoios_POM,"POM_nom"),(d.Passagens,"Silicone_nom")]:
    for o in g.Group:obj(o.Name,o.Shape,material)
for o in d.Distribuidor.Group:
    if o.Name.startswith("Trilho"):obj(o.Name,o.Shape,"POM_nom")
# Filetes de rosca e porcas são substituídos pelos envelopes instalados.
for o in d.Fixadores.Group:
    heads=[s for s in o.Shape.Solids if s.Volume>0]
    obj(o.Name,group(heads),"aco_nom")
g=json.loads((repo/"automacao/P1H/KiCad_Antenas/elemento_hfss.json").read_text())
base=PLACA_Z; h=CORE
ports=list(g["ports"].values());vias=g["vias"]
ply=[];local=[]
for land in g["lands"]:
    zz=base+(h if land["layer"]=="F" else 0);s=polygon(land["outer"],zz)
    for hole in land["holes"]:
        if len(hole)>100:
            cx=sum(a for a,b in hole)/len(hole);cy=sum(b for a,b in hole)/len(hole)
            s=s.cut(disk(cx,cy,.834856,zz))
        else:s=s.cut(polygon(hole,zz))
    # Unir os pads às redes efetivamente ligadas em cada face. Manter a ilha inferior da sonda independente da malha.
    name=land["name"];add=[]
    if name=="Feed_A":add=[(*ports[0],.6)]
    elif name=="Feed_B_Inner":add=[(*ports[1],.6),(*vias[1],.363)]
    elif name=="Feed_B_Outer":add=[(*vias[0],.363)]
    elif name=="Crossover_Bridge":add=[(*v,.363) for v in vias]
    for x,y,r in add:s=s.fuse(disk(x,y,r,zz))
    for x,y in ports:s=s.cut(disk(x,y,.45,zz))
    for x,y in vias:s=s.cut(disk(x,y,.225,zz))
    # Remover faces coincidentes sobre a seção de solda da blindagem.
    if name in ("Ring_Q1","Ring_Q4"):
        x,y=g["ports"]["B" if name=="Ring_Q1" else "A"]
        s=s.cut(disk(x,y,1.2704335,zz))
    local.append((name,s.removeSplitter()))
for i,(x,y) in enumerate(ports):local.append(("PadB"+str(i),disk(x,y,.6,base).cut(disk(x,y,.45,base))))
through=[]
for i in range(10):
    dx=(i-4.5)*PASSO
    for name,s in local:obj("Ant%02d_%s"%(i+1,name),shifted(s,dx),"folha_cu")
    for j,(x,y) in enumerate(vias):
        x+=dx;through.append((x,y,.225))
        obj(f"Via{i:02d}_{j}",cyl(x,y,.225,base,h).cut(cyl(x,y,.2,base,h)),"copper")
    through.extend((x+dx,y,.45) for x,y in ports)
core=m.bx(-250.85625,-14.15625,base,501.7125,28.3125,h)
obj("Rogers",xy_perforate(core,through,base-.01,h+.02),"RO4350B_R01")
div=json.loads((repo/"automacao/P1H/Divisor_10X_PTFE/geometria.json").read_text())
routes=json.loads((mechanics/"linhas_de_centro.json").read_text())
# O gabarito CSV do chicote arredonda os centros a 0,1 µm. Usar uma única origem para faces coincidentes.
for port in div["ports"]:
    if port[0] in routes:
        start=routes[port[0]][0][1]
        port[1:]=[start[0]-DIV_X,start[1]]
divholes=[(DIV_X+x,y,.525) for _,x,y in div["ports"]]
obj("PTFE_div",xy_perforate(m.bx(DIV_X-19.5,-39,DIV_B,39,78,1.52),divholes,DIV_B-.01,1.54),"ZYF300")
for pol,pts in div["copper"].items():
    sh=polygon([(DIV_X+x,y) for x,y in pts],DIV_F)
    for name,x,y in div["ports"]:
        if name[0]==pol:
            sh=sh.fuse(disk(DIV_X+x,y,.73,DIV_F)).cut(disk(DIV_X+x,y,.525,DIV_F))
    obj("Estrela_"+pol,sh.removeSplitter(),"folha_cu")
gnd=polygon([(DIV_X-18.98,-38.48),(DIV_X+18.98,-38.48),(DIV_X+18.98,38.48),(DIV_X-18.98,38.48)],DIV_B)
for name,x,y in div["ports"]:
    px=DIV_X+x
    # A camada inferior tem um pad de sinal e um plano de massa separados pela isolação do coaxial.
    obj("Pad_inferior_"+name,disk(px,y,.73,DIV_B).cut(disk(px,y,.525,DIV_B)),"folha_cu")
    # Evitar interfaces duplicadas entre o plano e a face da solda. A borda da solda fecha a massa nas saídas.
    gnd=gnd.cut(disk(px,y,1.515 if "_IN" in name else 2.13,DIV_B))
    if "_IN" not in name:
        obj("Solda_malha_"+name,cyl(px,y,2.13,DIV_B-.18,.18).cut(cyl(px,y,R_CABO,DIV_B-.18,.18)),"SAC305")
obj("Massa_div",gnd,"folha_cu")
for name,edges in routes.items():
    inp=name.startswith("IN_");pol=name[-1] if inp else name[0]
    xyz=V(*edges[-1][-1]);x,y=xyz.x,xyz.y
    edges[-1][-1][2]-=(4 if inp else 1)
    wire=m.wire_from_data(edges)
    outer=m.tube(wire,R_CABO);die=m.tube(wire,1.515);inner=m.tube(wire,.45975)
    outer=outer.cut(die);die=die.cut(inner)
    if inp:
        p=d.getObject("Terminal_"+name).Shape.Solids
        coil=d.getObject("Bobina_"+pol).Shape
        # União galvânica real entre capa e centro pela bobina e pelos terminais.
        barrel=cyl(x,y,.525,DIV_B,1.52)
        section=cyl(x,y,.45975,DIV_B-4,4)
        # União num único condutor permite contato sem volumes sobrepostos na parte da solda.
        # Os cilindros dos terminais e a hélice têm tangentes oblíquas. Formar as junções com solda.
        helix=Part.makeHelix(.73,1.46,.9)
        helix.rotate(V(),V(0,1,0),90);helix.translate(V(x+1.65,y,DIV_B-2.3))
        ends=[helix.Edges[0].valueAt(helix.Edges[0].FirstParameter),helix.Edges[-1].valueAt(helix.Edges[-1].LastParameter)]
        fillets=[Part.makeSphere(.18,pt) for pt in ends]+[Part.makeSphere(.18,V(x+1.74,y,DIV_B-4.3))]
        helix_wire,pin_lead,shield_lead=coil.Solids
        metal=helix_wire
        for contact in [fillets[0],pin_lead,fillets[1],shield_lead,fillets[2],outer,p[1],p[2],section,barrel,inner]:
            metal=metal.fuse(contact,1e-6)
        metal=metal.removeSplitter()
        assert len(metal.Solids)==1,name
        obj("Lancamento_"+pol,metal,"copper")
    else:
        # O cabo parte do divisor para -Z e retorna à placa de antenas pelo lado de +Z.
        sx,sy,_=edges[0][1]
        outer=m.union([outer,cyl(x,y,R_CABO,base-1,.25).cut(cyl(x,y,.834856,base-1,.25)),cyl(x,y,1.2704335,base-.75,.75).cut(cyl(x,y,.834856,base-.75,.75))])
        inner=m.union([inner,cyl(x,y,.362981,base-1,1),cyl(x,y,.45,base,h),cyl(sx,sy,.525,DIV_B,1.52)])
        obj("Capa_"+name,outer,"copper");obj("Sinal_"+name,inner,"copper")
    obj("Isol_"+name,die,"PTFE_cabo")
for pol,sign in [("A",-1),("B",1)]:
    y=sign*N_Y;z=N_Z;x0=BASE-RO-13
    def axial(r,x,h):return Part.makeCylinder(r,h,V(x,y,z),X)
    # Adaptador liso 50 ohm, com diâmetro de 7 mm no plano N. O desenho público não especifica a cavidade interna.
    # Extensão até o nariz dá plano coaxial de referência com blindagem circunferencial.
    at=BASE+11;delta=at-x0
    # O envelope mecânico deixa folga entre a rosca e a porca. O anel condutor inclui o contato metálico apertado.
    thread_contact=axial(8.12,BASE-RO+2.70,3.30)
    wall=m.union([d.getObject("Conector_N_"+pol).Shape,d.getObject("Porca_N_"+pol).Shape,d.getObject("Arruela_N_"+pol).Shape,axial(5.25,x0,12),axial(1.84,at-6.15,6.15),thread_contact])
    taper=Part.makeCone(3.5,1.515,delta,V(x0,y,z),X)
    wall=wall.cut(taper)
    assert len(wall.Solids)==1,pol
    center=Part.makeCone(3.5/2.30,.45975,delta,V(x0,y,z),X)
    obj("N_corpo_"+pol,wall,"latao_nom");obj("N_pino_"+pol,center,"latao_nom")
    # Preenchimento equivalente, uniforme, ajustado à impedância geométrica média das seções do taper.
    # A parte de 7 mm fica em ar; a transição adota PTFE parcial no último trecho.
    endfill=taper.common(axial(4.,at-8,8.)).cut(center)
    obj("N_isol_"+pol,endfill,"PTFE_cabo")
    for nm,mat in [("Junta_N_","Silicone_nom"),("Termorretratil_N_","PE_nom")]:
        obj(nm+pol,d.getObject(nm+pol).Shape,mat)
cad.recompute()
# Um STEP por material evita ambiguidade dos rótulos entre versões do tradutor ACIS.
for material in sorted(set(manifest.values())):
    items=[o for o in objects if manifest[o.Name]==material]
    Import.export(items,str(out/(material+".step")))
(out/"manifesto.json").write_text(json.dumps(manifest,indent=2),encoding="utf8")
print("CAD_EM_OK",len(objects))
