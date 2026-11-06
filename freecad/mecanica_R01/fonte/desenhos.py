"""Pranchas de fabricação. Vista em mm derivada dos mesmos perfis usados no sólido e no DXF."""
import json, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon, Circle, Rectangle, FancyArrowPatch
from matplotlib.lines import Line2D
from dimensoes import *
from formar_cabos import sample,lengths

INK="#192c37";TEAL="#126866"; RED="#a64732"; PALE="#e9f0ee"; GREY="#677780"; CU="#af683d"; PAPER="#ffffff"
plt.rcParams.update({"font.family":"DejaVu Sans","pdf.fonttype":42,"text.color":INK,"font.size":9})
def page(n,title,sub):
    f=plt.figure(figsize=(420/25.4,297/25.4),facecolor=PAPER)
    f.text(.045,.946,title,size=24,weight="bold");f.text(.046,.909,sub,size=11,color=GREY)
    f.add_artist(Line2D([.045,.955],[.887,.887],transform=f.transFigure,color=TEAL,lw=1.5))
    f.add_artist(Line2D([.045,.955],[.065,.065],transform=f.transFigure,color="#acbcb9",lw=.7))
    f.text(.045,.040,"P1H  /  MECÂNICA DO PAINEL   •   R01   •   06 NOV 2026",size=9,color=TEAL,weight="bold")
    f.text(.955,.040,f"A3   /   COTAS EM mm   /   VISTAS SEM ESCALA   /   {n} DE 4",ha="right",size=9,color=GREY)
    return f
def axes(f,rect,xlim,ylim):
    a=f.add_axes(rect,aspect="equal");a.set_xlim(*xlim);a.set_ylim(*ylim);a.axis("off");return a
def title(f,x,y,t):f.text(x,y,t,size=13,color=TEAL,weight="bold")
def line(a,x1,y1,x2,y2,**kw):a.plot([x1,x2],[y1,y2],color=kw.pop("color",INK),lw=kw.pop("lw",.8),**kw)
def poly(a,pts,face=PALE,edge=INK,lw=.9):a.add_patch(Polygon(pts,closed=True,facecolor=face,edgecolor=edge,lw=lw))
def rect(a,x,y,w,h,col=PALE,ec=INK):a.add_patch(Rectangle((x,y),w,h,facecolor=col,edgecolor=ec,lw=.8))
def cir(a,x,y,r,col="white",ec=INK):a.add_patch(Circle((x,y),r,facecolor=col,edgecolor=ec,lw=.65))
def dim(a,p,q,txt,ofs=(0,0),size=8):
    p=np.array(p);q=np.array(q);d=np.array(ofs);a.annotate("",q+d,p+d,arrowprops={"arrowstyle":"<->","color":GREY,"shrinkA":0,"shrinkB":0,"lw":.75})
    for v in (p,q):line(a,*v,*(v+d),color=GREY,lw=.45)
    m=(p+q)/2+d;rot=90 if abs(q[1]-p[1])>abs(q[0]-p[0]) else 0
    a.text(*m,txt,fontsize=size,rotation=rot,ha="center",va="center",bbox=dict(fc="white",ec="none",pad=1.5))
def outline(vertices):
    arr=[]
    for a,b in zip(vertices,vertices[1:]+vertices[:1]):
        p,q=np.array(a[:2],float),np.array(b[:2],float); bulge=a[2] if len(a)>2 else 0
        arr.append(p)
        if not bulge:continue
        chord=q-p;center=(q+p)/2+np.array([-chord[1],chord[0]])*(1-bulge**2)/(4*bulge)
        start=math.atan2(*(p-center)[::-1]);theta=4*math.atan(bulge)
        arr.extend(center+np.linalg.norm(p-center)*np.array([math.cos(t),math.sin(t)]) for t in np.linspace(start,start+theta,31)[1:-1])
    return arr
def table(f,box,headers,rows,widths,fs=9):
    a=f.add_axes(box);a.axis("off")
    t=a.table(cellText=rows,colLabels=headers,colWidths=widths,loc="upper left",bbox=(0,0,1,1),cellLoc="left",colLoc="left")
    t.auto_set_font_size(False);t.set_fontsize(fs)
    for (r,c),cell in t.get_celld().items():
        cell.set_edgecolor("white");cell.PAD=.035
        cell.set_facecolor(TEAL if not r else (PALE if r%2 else "#f6f8f7"))
        if not r:cell.set_text_props(color="white",weight="bold")
def notes(f,x,y,lines,spacing=.032):
    for i,t in enumerate(lines):f.text(x,y-i*spacing,t,fontsize=10,va="top",linespacing=1.35)
def panel(a):
    poly(a,face_ext())
    for x in CENTROS:poly(a,outline(slot(x,0,R_PASSA,PIN)),PAPER)
    for x,y in ref_bolts():cir(a,x,y,1.4)
def sheet1(pdf):
    f=page(1,"Refletor  /  corte da chapa","Alumínio 5052-H32 proposto, espessura 2,00 mm. Origem no centro da coluna. X positivo da base para o topo.")
    a=axes(f,[.035,.57,.93,.30],(-348,276),(-63,63));poly(a,contorno_plano())
    for x in CENTROS:poly(a,outline(slot(x,0,R_PASSA,PIN)),PAPER)
    for x,y in ref_bolts():cir(a,x,y,1.4)
    for y in (-N_Y,N_Y):poly(a,outline(duplo_d(N_FLAT,y)),PAPER)
    for a0,a1 in TRECHOS:
        for sy in [-1,1]:line(a,a0,sy*(18+BA/2),a1,sy*(18+BA/2),color=RED,ls="--")
    line(a,BASE-BA/2,-41,BASE-BA/2,41,color=RED,ls="--");line(a,-325,0,260,0,color=GREY,ls="-.",lw=.4)
    dim(a,(FIM_FLAT,41),(258,41),"585,398",(0,12));dim(a,(FIM_FLAT,-41),(FIM_FLAT,41),"82",(-10,0))
    a.text(-309,-48,"BASE",ha="center",weight="bold",size=8,color=TEAL)
    title(f,.045,.53,"Passagens e fixações");title(f,.60,.53,"Furos dos conectores N")
    b=axes(f,[.04,.315,.22,.20],(-12,12),(-10,10));poly(b,outline(slot(0,0,R_PASSA,PIN)),PAPER)
    dim(b,(-3.5,0),(3.5,0),"7,00",(0,-8));dim(b,(0,-PIN-3.5),(0,PIN+3.5),"12,018",(7.3,0))
    notes(f,.258,.461,["10 rasgos oblongos, eixo maior em Y.","Centros das semicircunferências a","5,018 mm. Raio das pontas 3,50.","Passagens A e B no mesmo rasgo."],.029)
    c=axes(f,[.575,.314,.16,.19],(-13,13),(-12,12));poly(c,outline(duplo_d(0,0)),PAPER)
    dim(c,(-8.25,0),(8.25,0),"Ø16,50",(0,-10));dim(c,(0,-7),(0,7),"14,00",(10,0))
    notes(f,.738,.461,["2 recortes com dois planos.","Centros Y = ±19,25.","Assento metálico plano e liso.","Rebarbar as duas faces."],.029)
    table(f,[.045,.096,.91,.207],["Elemento","Coordenada X no plano","Coordenada Y","Quantidade / operação"],[
        ["Cabos dos radiadores","−234,191 até +239,209 em passos de 52,60","0","10 rasgos"],
        ["Berços e batentes","0; ±105,20; ±210,40; ±253,90","±11,00","14 × Ø2,80 passantes"],
        ["Trilhos do divisor","−18,991 e +24,009","±11,00","4 × Ø2,80 passantes"],
        ["Conectores N","−302,398","±19,25","2 recortes duplo D"],
        ["Perfil externo","Extremos −327,398 e +258,000","±41 na base","DXF de corte 1:1, contornos fechados"]],[.23,.36,.14,.27])
    pdf.savefig(f);plt.close(f)
def sheet2(pdf):
    f=page(2,"Refletor  /  conformação","Todas as abas dobram para o verso (−Z). A frente plana dos radiadores define Z = 0.")
    title(f,.045,.844,"Vista frontal • furação após as dobras")
    a=axes(f,[.04,.595,.92,.23],(-298,277),(-50,49));panel(a)
    for a0,a1 in TRECHOS:
        for s in (-1,1):rect(a,a0,18*s-(4 if s<0 else 0),a1-a0,4,"#a5bcb8")
    dim(a,(-275,0),(258,0),"533,00  •  altura externa",(0,36));line(a,-274,-42,-274,42,color=TEAL,lw=2)
    title(f,.045,.555,"A–A   •   base dobrada");title(f,.54,.555,"B–B   •   nervuras traseiras")
    b=axes(f,[.045,.275,.425,.26],(-289,-211),(-66,12))
    # Vista XZ: a seção da base se prolonga pela alma.
    bend=[(0,0,-math.tan(math.pi/8)),(RO,-RO,0),(RO,-PROF_BASE,0),(RI,-PROF_BASE,0),(RI,-RO,math.tan(math.pi/8)),(0,-T,0)]
    poly(b,[(BASE-x,z) for x,z in outline(bend)]);rect(b,BASE,-2,50,2)
    dim(b,(BASE-4,0),(BASE-4,-56),"56,00",(-7,0))
    line(b,-280,-31,-263,-31,color=RED,ls="-.");dim(b,(-259,0),(-259,-31),"31,00",(4,0))
    b.text(-252,-48,"N aponta para −X\n(base da antena)",size=9,color=TEAL)
    c=axes(f,[.548,.33,.39,.17],(-34,34),(-20,10));rect(c,-18,-2,36,2)
    for s in (-1,1):
        data=[(0,0,-math.tan(math.pi/8)),(RO,-RO,0),(RO,-8,0),(RI,-8,0),(RI,-RO,math.tan(math.pi/8)),(0,-2,0)]
        poly(c,[(s*(18+x),z) for x,z in outline(data)])
    dim(c,(-18,0),(18,0),"36,00  •  face plana",(0,5));dim(c,(-22,-8),(22,-8),"44,00  •  exterior",(0,-7));dim(c,(22,0),(22,-8),"8,00",(5,0))
    notes(f,.54,.295,["Dobra inferior de 82 mm. Quatro segmentos laterais","de 220 e 226 mm deixam livre a montagem do divisor."],.029)
    table(f,[.045,.101,.91,.13],["Dobra","Eixo na chapa plana","Extensão","Ferramental e conferência"],[
        ["Base","X = −273,199","Y = −41 a +41","90° para trás • raio interno 2,00"],
        ["Nervuras","Y = ±20,199","X = −248 a −28 e +32 a +258","90° para trás • mesma ferramenta"],
        ["Desenvolvimento","BA = 4,398 por dobra","K adotado 0,40","Conferir raio e K com corpo de prova antes do corte do lote"]],[.16,.22,.29,.33])
    pdf.savefig(f);plt.close(f)
def sheet3(pdf):
    f=page(3,"Montagem  /  suportes e distribuição","A placa de antenas entra nos berços pelas extremidades. Montar o conjunto na face frontal e colocar os batentes por último.")
    title(f,.045,.842,"Frente • cinco apoios entre radiadores")
    a=axes(f,[.045,.675,.91,.14],(-285,270),(-38,38));panel(a);rect(a,-250.85625,-14.15625,501.7125,28.3125,"#cfdfce")
    for x in CENTROS:
        cir(a,x,-PIN,1.,CU);cir(a,x,PIN,1.,CU)
    for x in SUP_X+BAT_X:rect(a,x-2.5,-16,5,32,"#738487")
    title(f,.045,.638,"Berço frontal • seção YZ");title(f,.535,.638,"Divisor • retenção pelas bordas")
    b=axes(f,[.039,.365,.46,.25],(-25,25),(-4,24))
    cross=[(-18,0),(18,0),(18,19.6),(12.70,19.6),(12.70,17.62),(14.50,17.62),(14.50,16.61),(-14.50,16.61),(-14.50,17.62),(-12.70,17.62),(-12.70,19.6),(-18,19.6)]
    poly(b,cross,"#9baca9");rect(b,-14.15625,16.61,28.3125,.76,"#e4a967");rect(b,-18,-2,36,2)
    dim(b,(-18,0),(-18,16.61),"16,61",(-4,0));dim(b,(-12.7,19.6),(12.7,19.6),"25,40",(0,3.0))
    for x in [-11,11]:line(b,x,0,x,8,lw=1.7,color="#52666b")
    c=axes(f,[.525,.355,.415,.265],(-32,35),(-50,48))
    rect(c,-19.5,-39,39,78,"#d8e7d6")
    for q in cabos():cir(c,float(q["x_placa_mm"]),float(q["y_placa_mm"]),1.3,CU)
    for x in (-21.5,21.5):
        rect(c,x-4,-41,8,82,"#85999a")
        for y in (-11,11):cir(c,x,y,1.4)
    dim(c,(-19.5,-39),(19.5,-39),"39,00",(0,-6));dim(c,(19.5,-39),(19.5,39),"78,00",(9,0))
    table(f,[.045,.102,.91,.214],["Componente","Qtd.","Usinagem e montagem"],[
        ["P01  •  berço em POM-C natural","5","Chapa 5 × 36 × 19,60. Canal 29,00 × 1,01 a Z = 16,61. Dois roscados M2,5 por baixo."],
        ["P02  •  batente em POM-C","2","5 × 31 × 19,60. Entre faces internas 502,80 para PCB de 501,7125. Folga nominal 0,54 em cada ponta."],
        ["P03 / P04  •  trilhos do divisor","1 + 1","POM 8 × 82 × 8. Canal 78,60 × 1,75. Cabos Ø5,20. Flange do passa-cabos: R4,90 × 1,45 de profundidade."],
        ["Fixação dos perfis","18","M2,5 × 8 + arruela 0,50. Pré-furo Ø2,05. Berços/batentes: profundidade 8. Trilhos: 6,75. Rosquear antes de montar."],
        ["P05  •  passa-cabos duplo","10","Silicone flexível. Pescoço 6,98 no rasgo de 7; lábios 9,30 de largura × 1,20; duas passagens Ø3,63 a 5,018."]],[.26,.065,.675],8.6)
    pdf.savefig(f);plt.close(f)
def sheet4(pdf):
    f=page(4,"Alimentação  /  chicote, entradas e curto em CC","Duas entradas N fêmea de 50 Ω. J1 alimenta A e J12 alimenta B. Cada polarização tem dez saídas.")
    routes=json.loads((SAIDA/"linhas_de_centro.json").read_text())
    title(f,.045,.843,"Vista de lado • caminhos dos cabos em XZ")
    a=axes(f,[.04,.565,.915,.25],(-292,268),(-126,26))
    rect(a,BASE,-2,529,2);rect(a,BASE-4,-56,2,52);rect(a,-250.856,16.61,501.712,.76,"#739975")
    for n,edges in routes.items():
        pp=sample(edges,1.5);pa="A" in n; a.plot(pp[:,0],pp[:,2],color=("#a55732" if pa else "#397b80"),lw=1.2,alpha=.88)
    a.text(194,-108,"A   /   B",color=TEAL,fontsize=9);dim(a,(230,0),(230,-113),"≈ 113",(17,0))
    title(f,.045,.535,"Conector e vedação");title(f,.538,.535,"Bobina em derivação • uma por entrada")
    notes(f,.045,.493,["Amphenol 082-6784, RG-402 / UT-141C. Inserir pelo lado externo.",
        "Junta de silicone sob o flange; arruela de trava e porca no lado",
        "interno. Entre eixos 38,50. Chave 22. Aperto 3,39 N·m.",
        "Passar o termorretrátil fornecido antes de soldar e retrair após a união.",
        "Assento limpo e sem rebarba. Acoplar par ou tampa com vedação."],.030)
    b=axes(f,[.54,.347,.405,.136],(-1,14),(-.75,4));line(b,0,2.6,13,2.6,lw=1.5)
    b.text(0,3.05,"N / coaxial",fontsize=8);b.text(13,3.05,"J1 ou J12",ha="right",fontsize=8)
    line(b,6,2.6,6,2.1);t=np.linspace(0,1,100);b.plot(6+.34*np.sin(4*np.pi*t),2.1-1.25*t,color=CU,lw=1.6)
    line(b,6,.85,6,.25);line(b,5.1,.25,6.9,.25,lw=1.2);line(b,5.4,0,6.6,0);b.text(7.2,.2,"blindagem / GND",size=8)
    notes(f,.538,.343,["Na janela de 4 mm junto a cada entrada do divisor, soldar uma",
        "ponta ao condutor central e outra à capa do mesmo coaxial.",
        "Desesmaltar e estanhar as pontas. As duas malhas ligam ao GND."],.029)
    table(f,[.045,.097,.91,.135],["Item","Especificação da montagem","Conferência"],[
        ["20 saídas UT-141C","254,00 de linha de centro até a placa, incluindo 3,00 da transição","Formar em gabarito; conferir referência de corte e comprimento elétrico."],
        ["2 entradas UT-141C","306,64 de linha de centro entre planos do CAD por entrada","Acrescentar inserção/decapagem conforme conector e junta."],
        ["2 bobinas de fio esmaltado","Reserva geométrica: fio Ø0,30; Ø médio 1,80; 2 espiras; passo 0,73","Verificar continuidade pino–carcaça em cada N; geometria RF a qualificar."]],[.175,.425,.40],8.5)
    pdf.savefig(f);plt.close(f)
if __name__=="__main__":
    with PdfPages(SAIDA/"06_Desenho_de_fabricacao.pdf") as out:
        for sheet in (sheet1,sheet2,sheet3,sheet4):sheet(out)
