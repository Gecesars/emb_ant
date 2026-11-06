"""Executar no FreeCAD 1.1. Os perfis, extrusões, recortes e dobras da chapa são editáveis."""
import math, json, sys
from pathlib import Path
import FreeCAD as App
import Part, Sketcher
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dimensoes import *
V=App.Vector
Z=V(0,0,1);X=V(1,0,0);Y=V(0,1,0)
I=App.Rotation()
AL=(.73,.77,.80); POM=(.20,.23,.26); PCB=(.28,.58,.31); CU=(.79,.45,.19); SI=(.56,.33,.24); STEEL=(.48,.53,.58)
paints={}
def color(o,c):
    paints[o.Name]=list(c)
    if o.ViewObject:o.ViewObject.ShapeColor=c
def hide(o):
    if o.ViewObject:o.ViewObject.Visibility=False
def vec(p):return V(*p)
def bx(x,y,z,l,w,h):return Part.makeBox(l,w,h,V(x,y,z))
def cz(x,y,z,r,h):return Part.makeCylinder(r,h,V(x,y,z))
def union(shapes):return shapes[0].multiFuse(shapes[1:]).removeSplitter() if len(shapes)>1 else shapes[0]
def trace(vertices):
    edges=[]
    for a,b in zip(vertices,vertices[1:]+vertices[:1]):
        p=V(a[0],a[1],0);q=V(b[0],b[1],0);bulge=a[2] if len(a)>2 else 0
        if abs(bulge)<1e-10:edges.append(Part.LineSegment(p,q))
        else:
            chord=q-p;mid=(p+q)*.5+V(chord.y,-chord.x,0)*(.5*bulge)
            edges.append(Part.Arc(p,mid,q))
    return edges
def circle(x,y,r):return Part.Circle(V(x,y,0),Z,r)
def sketch(doc,name,edges,place):
    s=doc.addObject("Sketcher::SketchObject",name);s.Placement=place
    for geom in edges:
        n=s.addGeometry(geom,False)
        s.addConstraint(Sketcher.Constraint("Block",n))
    return s
def ext(doc,name,s,direction,length):
    o=doc.addObject("Part::Extrusion",name);o.Base=s;o.DirMode="Custom";o.Dir=direction;o.LengthFwd=length;o.Solid=True
    hide(s);return o
def place(x=0,y=0,z=0,rot=I):return App.Placement(V(x,y,z),rot)
def sketch_holes():return [g for x in CENTROS for g in trace(slot(x,0,R_PASSA,PIN))]+[circle(x,y,1.4) for x,y in ref_bolts()]
def save(doc,name,obj=None):
    doc.recompute()
    if obj:
        assert obj.Shape.isValid() and len(obj.Shape.Solids)==1,(name,obj.Shape.Volume)
        for o in doc.Objects:
            if o!=obj:hide(o)
        color(obj,AL)
    target=SAIDA/(name+".FCStd");doc.saveAs(str(target))
    return target
def spec(doc):
    table=doc.addObject("Spreadsheet::Sheet","Cotas")
    for i,(label,value) in enumerate([("Espessura",T),("Raio_interno",RI),("Fator_K",K),("Altura_PCB",PLACA_Z),("Passo_PCB",PASSO)]):
        table.set("A"+str(i+1),label);cell="B"+str(i+1);table.set(cell,str(value)+(" mm" if label!="Fator_K" else ""));table.setAlias(cell,label)
    return table
def flat():
    d=App.newDocument("Planificada");spec(d)
    geom=trace(contorno_plano())+sketch_holes()
    for y in (-N_Y,N_Y):geom+=trace(duplo_d(N_FLAT,y))
    s=sketch(d,"Corte_planificado",geom,place());o=ext(d,"Chapa_plana",s,Z,T);o.setExpression("LengthFwd","Cotas.Espessura")
    d.recompute();volume=o.Shape.Volume
    # Teste de uma cota funcional; a mudança deve atravessar toda a peça.
    d.Cotas.set("B1","2.1 mm");d.recompute();assert abs(o.Shape.Volume/volume-1.05)<1e-6
    d.Cotas.set("B1","2 mm");d.recompute()
    target=save(d,"02_Refletor_planificado",o);App.closeDocument(d.Name)
    d=App.openDocument(str(target));assert abs(d.Chapa_plana.Shape.Volume-volume)<1e-5;App.closeDocument(d.Name)
    return volume
def bend_profile(depth):
    b=math.tan(math.pi/8)
    return [(0,0,-b),(RO,-RO,0),(RO,-depth,0),(RI,-depth,0),(RI,-RO,b),(0,-T,0)]
def folded():
    d=App.newDocument("Dobrada");spec(d)
    web=ext(d,"Alma_furada",sketch(d,"Perfil_da_alma",trace(face_ext())+sketch_holes(),place()),-Z,T)
    web.setExpression("LengthFwd","Cotas.Espessura")
    # As coordenadas locais do perfil são avanço para fora e Z do refletor.
    parts=[web]
    tr=App.Rotation(-X,Z,Y,"XYZ")
    p=sketch(d,"Perfil_dobra_base",trace(bend_profile(PROF_BASE)),place(BASE,-MEIA_BASE,0,tr))
    parts.append(ext(d,"Aba_inferior",p,Y,82))
    for side in [-1,1]:
        orient=App.Rotation(Y*side,Z,X*side,"XYZ")
        for j,(a,b) in enumerate(TRECHOS):
            suffix=("E" if side<0 else "D")+str(j+1)
            p=sketch(d,"Perfil_nervura_"+suffix,trace(bend_profile(PROF_NERV)),place(a,side*18,0,orient))
            parts.append(ext(d,"Nervura_"+suffix,p,X,b-a))
    blank=d.addObject("Part::MultiFuse","Dobras_unidas");blank.Shapes=parts;blank.Refine=True
    # Local X = Z físico, local Y = Y físico. Normal para -X.
    orientation=App.Rotation(Z,Y,-X,"XYZ")
    cuts=sketch(d,"Recortes_antirrotacao",trace(duplo_d(N_Z,-N_Y))+trace(duplo_d(N_Z,N_Y)),place(BASE+1,0,0,orientation))
    tool=ext(d,"Puncoes_N",cuts,-X,8)
    o=d.addObject("Part::Cut","Refletor_dobrado");o.Base=blank;o.Tool=tool;o.Refine=True
    target=save(d,"01_Refletor_dobrado",o)
    sh=o.Shape.copy();App.closeDocument(d.Name);d=App.openDocument(str(target))
    assert abs(sh.Volume-d.Refletor_dobrado.Shape.Volume)<1e-5;App.closeDocument(d.Name)
    sh.exportStep(str(SAIDA/"01_Refletor_dobrado.step"))
    rt=Part.read(str(SAIDA/"01_Refletor_dobrado.step"))
    assert len(rt.Solids)==1 and abs(rt.Volume/sh.Volume-1)<1e-6
    return sh
def oval(x,rad,z,h):
    wire=Part.Wire([g.toShape() for g in trace(slot(x,0,rad,PIN))])
    face=Part.Face(wire);face.translate(V(0,0,z));return face.extrude(Z*h)
def shaped(doc,group,name,shape,c):
    assert not shape.isNull() and shape.isValid(),name
    o=doc.addObject("Part::Feature",name);o.Shape=shape;group.addObject(o);color(o,c);return o
def hexa(x,y,z,af,height):
    rr=af/math.sqrt(3)
    pts=[V(x+rr*math.cos(i*math.pi/3),y+rr*math.sin(i*math.pi/3),z) for i in range(6)]
    return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(Z*height)
def support(x,stop=False):
    w=31 if stop else 36
    solid=bx(x-2.5,-w/2,0,5,w,19.6)
    if not stop:
        channel=bx(x-3,-14.50,PLACA_Z,6,29.0,1.01)
        opening=bx(x-3,-12.70,PLACA_Z+1.01,6,25.4,5)
        solid=solid.cut(union([channel,opening]))
    for y in [-ROSCA_Y,ROSCA_Y]:solid=solid.cut(cz(x,y,-.1,1.025,8.1))
    return solid
def rail(x,side):
    sh=bx(x-4,-41,-10.0,8,82,8)
    # Batentes nas extremidades. F.Cu se apoia em -6 e B.Cu tem folga de 0,23 mm.
    e=DIV_X+side*19.75
    x0=e if side<0 else e-4
    sh=sh.cut(bx(x0,-39.3,-7.75,4,78.6,1.75))
    for y in [-ROSCA_Y,ROSCA_Y]:
        sh=sh.cut(cz(x,y,-8.75,1.025,7.0))
    for y in [-PIN,PIN]:
        sh=sh.cut(cz(DIV_X+side*PASSO/2,y,-10.1,2.60,8.2))
    return sh
def make_capsule_grommet(x):
    sh=union([oval(x,4.65,-3.2,1.2),oval(x,3.49,-2,2),oval(x,4.65,0,1.2)])
    for y in [-PIN,PIN]:sh=sh.cut(cz(x,y,-3.3,1.815,4.7))
    return sh
def wire_from_data(data):
    return Part.Wire([Part.makeLine(vec(e[1]),vec(e[2])) if e[0]=="L" else Part.Arc(vec(e[1]),vec(e[2]),vec(e[3])).toShape() for e in data])
def tube(w,r):
    p=w.Edges[0].valueAt(w.Edges[0].FirstParameter)
    tangent=w.Edges[0].tangentAt(w.Edges[0].FirstParameter)
    return w.makePipeShell([Part.Wire([Part.makeCircle(r,p,tangent)])],True,False)
def connector(y):
    # Eixo local +Z aponta para o cabo interno (+X da antena).
    # Origem no lado externo da base. Junta sob o flange e porca interna.
    flat=bx(-12,-6.88,0,24,13.76,11)
    stem=cz(0,0,0,7.91,8.8).common(flat)
    nose=cz(0,0,-13.0,7.85,10.8).cut(cz(0,0,-13.1,5.15,9))
    main=union([nose,hexa(0,0,-2.2,22,2.0),cz(0,0,-.2,7.7,.2),stem,cz(0,0,8.75,2.32,6.25)])
    nipple=cz(0,0,9.15,1.825,6.);main=main.cut(nipple)
    washer=cz(0,0,2,10.7,.65).cut(cz(0,0,1.9,8.02,1))
    nut=hexa(0,0,2.65,22,3.5).cut(cz(0,0,2.55,8,4))
    seal=cz(0,0,-.2,10.4,.2).cut(cz(0,0,-.3,8.05,.5))
    sleeve=cz(0,0,9.0,2.78,19.05).cut(cz(0,0,8.98,2.34,6.04)).cut(cz(0,0,14.99,1.81,13.1))
    # Remapeamento local (X,Y,Z) para (Z,Y,X); orientação positiva = -Z,Y,X.
    orientation=App.Rotation(-Z,Y,X,"XYZ")
    out=[]
    for sh in [main,nut,washer,seal,sleeve]:
        sh.Placement=place(BASE-RO,y,N_Z,orientation).multiply(sh.Placement);out.append(sh)
    return out
def coil(input_y,sign):
    # Shunt de ensaio na janela do lançamento coaxial; eixo da bobina em X.
    r=.9;pitch=.73;h=2*pitch
    helix=Part.makeHelix(pitch,h,r)
    helix.rotate(V(),Y,90);helix.translate(V(DIV_X+1.65,input_y,DIV_B-2.3))
    p=helix.Edges[0].valueAt(helix.Edges[0].FirstParameter);q=helix.Edges[-1].valueAt(helix.Edges[-1].LastParameter)
    sh=tube(Part.Wire(helix.Edges),.15)
    a=V(DIV_X,input_y,DIV_B-2.1);b=V(DIV_X+1.70,input_y,DIV_B-4.3)
    def lead(u,v):return Part.makeCylinder(.15,(v-u).Length,u,v-u)
    return Part.makeCompound([sh,lead(a,p),lead(q,b)])
def screw(x,y,z,sign,length):
    # Envelope M2,5 x L com arruela 0,5. Diâmetro de raiz convenção CAD no trecho roscado.
    a=cz(x,y,z-.5,2.65,.5).cut(cz(x,y,z-.55,1.31,.65))
    body=union([cz(x,y,z-.5,1.01,length),cz(x,y,z-2.5,2.25,2)])
    if sign<0:
        for sh in [a,body]:sh.rotate(V(x,y,z),X,180)
    return Part.makeCompound([a,body])
def assembly(ref):
    d=App.newDocument("Montagem");groups={key:d.addObject("App::DocumentObjectGroup",key) for key in ("Chassi","Radiadores","Apoios_POM","Distribuidor","Passagens","Entradas_N","Cabos_A","Cabos_B","Shunts_DC","Fixadores")}
    def add(g,n,s,c):return shaped(d,groups[g],n,s,c)
    add("Chassi","Chapa_Aluminio_2mm",ref,AL)
    source=App.openDocument(str(SAIDA.parent/"P1H_10_Continua.FCStd"))
    frontboard=source.Nucleo_continuo.Shape.copy()
    for obj in source.Objects:
        if obj.Name.startswith(("CobreRF","Nucleo")):add("Radiadores",obj.Name,obj.Shape.copy(),CU if "Cobre" in obj.Name else PCB)
    App.closeDocument(source.Name)
    obstacles=[("Refletor",ref)]
    for i,x in enumerate(SUP_X+BAT_X):
        name=("Berco_" if i<5 else "Batente_")+str(i+1)
        sh=support(x,i>=5);add("Apoios_POM",name,sh,POM);obstacles.append((name,sh))
        assert sh.common(frontboard).Volume<1e-6,name
        for j,y in enumerate((-ROSCA_Y,ROSCA_Y)):
            fix=screw(x,y,-T,1,8);add("Fixadores",f"Par_{i}_{j}",fix,STEEL)
            obstacles.append((f"Par_{i}_{j}",fix))
    geo=json.loads((REPO/"automacao/P1H/Divisor_10X_PTFE/geometria.json").read_text())
    board=bx(DIV_X-19.5,-39,DIV_B,39,78,1.52)
    for _,x,y in geo["ports"]:board=board.cut(cz(DIV_X+x,y,DIV_B-.1,.5,1.8))
    add("Distribuidor","Divisor_PTFE",board,PCB)
    for pol,pts in geo["copper"].items():
        w=Part.Wire([g.toShape() for g in trace(pts)]);sh=Part.Face(w);sh.translate(V(DIV_X,0,DIV_F))
        for name,x,y in geo["ports"]:
            if name.startswith(pol):sh=sh.cut(cz(x+DIV_X,y,DIV_F-.1,.5,.2))
        add("Distribuidor","Rede_"+pol,sh,CU)
    for i,(x,side) in enumerate(zip(DIV_RAIL,[-1,1])):
        sh=rail(x,side);add("Distribuidor","Trilho_"+str(i+1),sh,POM)
        assert sh.common(board).Volume<1e-6
        obstacles.append(("Trilho_"+str(i+1),sh))
        for j,y in enumerate((-ROSCA_Y,ROSCA_Y)):
            fix=screw(x,y,0,-1,8);add("Fixadores",f"Par_trilho_{i}_{j}",fix,STEEL)
            obstacles.append((f"Par_trilho_{i}_{j}",fix))
    for i,x in enumerate(CENTROS):
        sh=make_capsule_grommet(x);add("Passagens",f"Passa_cabos_{i+1:02d}",sh,SI)
    for sign,pol in [(-1,"A"),(1,"B")]:
        for n,s in zip(["Conector","Porca","Arruela","Junta","Termorretratil"],connector(sign*N_Y)):
            add("Entradas_N",n+"_N_"+pol,s,SI if n=="Junta" else (POM if n=="Termorretratil" else STEEL))
            assert s.common(ref).Volume<1e-6,(n,pol)
        add("Shunts_DC","Bobina_"+pol,coil(sign*N_Y,sign),CU)
    route_data=json.loads((SAIDA/"linhas_de_centro.json").read_text())
    tubes={}; data={}
    for name,edges in route_data.items():
        full=wire_from_data(edges)
        inp=name.startswith("IN_");pol=name[-1] if inp else name[0]
        if not inp:assert abs(full.Length-254)<1e-4
        # Último trecho junto da antena = transição de 3 mm; janela traseira de 4 mm nas entradas.
        trimmed=json.loads(json.dumps(edges));end=vec(trimmed[-1][-1]);stop=3 if not inp else 4
        trimmed[-1][-1][2]-=stop
        sh=tube(wire_from_data(trimmed),R_CABO)
        add("Cabos_"+pol,("Entrada_" if inp else "UT141_")+name,sh,CU)
        def ring(z,r,inside,height):
            return cz(end.x,end.y,z,r,height).cut(cz(end.x,end.y,z-.01,inside,height+.02))
        term=Part.makeCompound([ring(end.z-3,R_CABO,1.515,2),ring(end.z-1,R_CABO,.835,.25),
                                ring(end.z-.75,1.2704,.835,.75),cz(end.x,end.y,end.z-3,.45975,2),
                                cz(end.x,end.y,end.z-1,.362981,1+CORE)])
        if inp:
            # Pino de entrada, dois filetes/orelhas aterradas preservando a janela lateral da bobina.
            term=Part.makeCompound([cz(end.x,end.y,end.z-4,.45975,4+1.52),bx(end.x-1.75,end.y-.32,end.z-4,.35,.64,4),bx(end.x-.3,end.y+1.45,end.z-4,.6,.35,4)])
        add("Cabos_"+pol,"Terminal_"+name,term,STEEL)
        tubes[name]=sh
        data[name]={"eixo_mm":round(full.Length,4),"traseira_z_mm":round(sh.BoundBox.ZMin,4)}
    violations=[]
    for name,sh in tubes.items():
        for other,solid in obstacles:
            if sh.BoundBox.intersect(solid.BoundBox) and sh.common(solid).Volume>1e-4:violations.append((name,other))
    assert not violations,violations
    for key,cable in tubes.items():
        for other,sh in tubes.items():
            if other<key and sh.BoundBox.intersect(cable.BoundBox):
                assert cable.common(sh).Volume<1e-5,(key,other)
    target=save(d,"03_Antena_montada")
    pieces=SAIDA/"componentes";pieces.mkdir(exist_ok=True)
    for name,shape in [("P01_Berco",support(0)),("P02_Batente",support(0,True)),("P03_Trilho_E",rail(DIV_RAIL[0],-1)),("P04_Trilho_D",rail(DIV_RAIL[1],1)),("P05_Passa_duplo",make_capsule_grommet(0))]:
        bb=shape.BoundBox;shape.translate(V(-bb.XMin,-bb.YMin,-bb.ZMin));shape.exportStep(str(pieces/(name+".step")))
    (SAIDA/"verificacao.json").write_text(json.dumps({"cabos":data,"volume_dobrado_mm3":ref.Volume,"largura_face_mm":36,"passagens_duplas":10,"parafusos":18,"interferencias_cabos_com_chapa_bercos_trilhos_e_entre_si":violations},indent=2),encoding="utf8")
    (FONTE/"cores.json").write_text(json.dumps(paints),encoding="utf8")
    App.closeDocument(d.Name);d=App.openDocument(str(target));assert len(d.Cabos_A.Group)==22 and len(d.Cabos_B.Group)==22
    App.closeDocument(d.Name)
def main():
    volume=flat();ref=folded()
    bend_width=2*MEIA_BASE+2*sum(b-a for a,b in TRECHOS)
    # No sólido nominal o arco geométrico médio é R+t/2. O corte usa a fibra neutra R+K*t.
    expected=T*(math.pi/2)*(0.5-K)*T*bend_width
    assert abs((ref.Volume-volume)-expected)<1e-4,(ref.Volume-volume,expected)
    assembly(ref)
    print("MECANICA_OK",ref.BoundBox,ref.Volume,volume)
if __name__=="__main__":main()
