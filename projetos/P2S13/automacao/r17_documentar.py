"""Documentacao dimensional R17: PDFs, DXFs e BOM. Nao executa HFSS."""
from pathlib import Path
import json, math, csv, hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import ezdxf, fitz
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
ROOT=Path('D:/dev/EMBRAER/P2S13/R17_Flanges_Refletor');M=ROOT/'mecanica';OUT=ROOT/'documentacao';OUT.mkdir(exist_ok=True)
p=json.loads((M/'dimensoes.json').read_text());cad=json.loads((M/'verificacao_cad.json').read_text())
old=json.loads(Path('D:/dev/EMBRAER/P2S13/R16_Tubo_PVC/dn100_c02/circuito/resultado.json').read_text())
new=json.loads((ROOT/'plano90/circuito/resultado.json').read_text())
assert cad['validos'] and not cad['intersecoes']
font='ArialR17';bold='ArialR17Bold';pdfmetrics.registerFont(TTFont(font,'C:/Windows/Fonts/arial.ttf'));pdfmetrics.registerFont(TTFont(bold,'C:/Windows/Fonts/arialbd.ttf'))
style=ParagraphStyle('p',fontName=font,fontSize=9.3,leading=13,textColor=colors.HexColor('#273646'))
tiny=ParagraphStyle('tiny',parent=style,fontSize=7.5,leading=10)
def para(c,text,x,y,w,small=False):
    item=Paragraph(text,tiny if small else style);aw,ah=item.wrap(w*mm,900);item.drawOn(c,x*mm,y*mm-ah);return y-ah/mm
def text(c,x,y,s,size=9,b=False):c.setFont(bold if b else font,size);c.drawString(x*mm,y*mm,s)
def img(c,path,x,y,w,h):
    if Path(path).exists():c.drawImage(str(path),x*mm,y*mm,w*mm,h*mm,preserveAspectRatio=True,anchor='c',mask='auto')
def header(c,title,num,a3=False):
    W,H=(420,297) if a3 else (210,297)
    c.setFillColor(colors.HexColor('#102f47'));c.rect(0,(H-26)*mm,W*mm,26*mm,fill=1,stroke=0)
    c.setFillColor(colors.white);text(c,12,H-13,title,15,True);text(c,12,H-21,'P2S13 • R17 • DN100 • PRELIMINAR • 12/11/2026',8)
    c.setFillColor(colors.HexColor('#273646'));text(c,12,9,'Dimensões em mm. Escalas indicadas para impressão a 100%.',7)
    c.setFont(font,7);c.drawRightString((W-12)*mm,9*mm,str(num));c.setStrokeColor(colors.HexColor('#b1bac0'));c.line(12*mm,15*mm,(W-12)*mm,15*mm)
    c.setStrokeColor(colors.HexColor('#283745'));c.setLineWidth(.65)
def table(c,rows,x,y,widths):
    data=[[Paragraph(str(v),tiny) for v in row] for row in rows]
    t=Table(data,colWidths=[w*mm for w in widths],repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dce7ef')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#b6c1ca')),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    _,h=t.wrap(1000,2000);t.drawOn(c,x*mm,y*mm-h);return y-h/mm
def fmt(x,n=3):return f'{x:.{n}f}'.replace('.',',')

# Diagramas comparativos, sempre dados exportados e circuito real de cada caso.
fig,axs=plt.subplots(1,2,subplot_kw={'projection':'polar'},figsize=(11.8,5.3))
for ax,cut in zip(axs,['H','V']):
    for label,folder,color in [('Abas 150°',Path('D:/dev/EMBRAER/P2S13/R16_Tubo_PVC/dn100_c02/circuito'),'#22649a'),('Plano 90 mm',ROOT/'plano90/circuito','#d67623')]:
        arr=np.genfromtxt(folder/f'diagrama_{cut}.csv',delimiter=',',names=True)
        ang=arr[arr.dtype.names[0]];g=arr[arr.dtype.names[1]]
        # Arquivo explicitamente armazena theta/ganho: nao normalizar por colunas de amplitude.
        ax.plot(np.deg2rad(ang),np.maximum(10**((g-g.max())/20),0),label=label,color=color,lw=1.6)
    ax.set_theta_zero_location('N');ax.set_theta_direction(-1);ax.set_ylim(0,1);ax.set_yticks([.25,.5,.75,1]);ax.set_title(cut+' • E/Emax',pad=18);ax.grid(alpha=.5)
axs[0].legend(loc='lower left',bbox_to_anchor=(-.12,-.16),ncol=2);fig.suptitle('5,17 GHz • duas entradas 0,5 W / 0° • resultados preliminares',y=.99)
fig.tight_layout();fig.savefig(OUT/'comparacao_polar_HV.png',dpi=180,bbox_inches='tight');plt.close(fig)

# BOM: componentes de RF preservados; ferragens nominais sem rosca helicoidal no CAD.
bom=[
 ['01',1,'Tubo PVC Tigre esgoto Série Normal DN100','OD101,6 / ID98 / e1,8; cortar L350; sem bolsa'],
 ['02',1,'Flange inferior, Al6061-T6 nominal','Ø110 ×4,76; canal2,5×2,5; 2 recortes N e 2 furosØ3,4'],
 ['03',1,'Flange superior, Al6061-T6 nominal','Ø110 ×4,76; canal2,5×2,5; 2 furosØ3,4'],
 ['04',1,'Refletor, Al5052-H32 nominal','Chapa2; desenvolvido296×90; abas150° a±28,5; 2 linguetas20 a90°'],
 ['05',3,'PCB radiante 2_elementos simétrica','88×50; RO4350B0,76; Cu35µm; ENIG; R16 preservada'],
 ['06',1,'Divisor duplo1:3 C02','36×78; ZYF300CA-C1,52; Cu35µm; ENIG; R16 preservado'],
 ['07',12,'Grampo de PCB em POM natural','Usinado; largura5; apoio14,949; folga superior0,05'],
 ['08',4,'Grampo do divisor em POM natural','Usinado; largura5; apoio33,196 a partir do verso da chapa'],
 ['09',12,'Parafuso cabeça cilíndrica M2×25','InoxA2; rosca simplificada no CAD'],
 ['10',4,'Parafuso cabeça cilíndrica M2×45','InoxA2; rosca simplificada no CAD'],
 ['11',32,'Arruela lisa M2','InoxA2; nominalØ4 ×0,5'],
 ['12',16,'Porca M2','InoxA2; nominal altura1,6'],
 ['13',4,'Parafuso cabeça cilíndrica M3×12','InoxA2; fixa linguetas aos flanges'],
 ['14',4,'Arruela de vedação M3','Inox/EPDM; nominalØ7 ×0,5; confirmar peça comercial'],
 ['15',4,'Arruela lisa M3 + porca M3','Um par por fixação; nominal arruela0,5 / porca2,4'],
 ['16',2,'Junta anular EPDM60ShA nominal','DI98 / DE101,6; livre0,5; montada0,3; compressão40% a ensaiar'],
 ['17',2,'Amphenol082-6784 N fêmea bulkhead','Inclui porca, arruela, junta e termorretrátil; STEP disponível'],
 ['18',6,'Coaxial Micro-Coax UT-141C de saída','Comprimento físico134; trecho RF133,82; manter seis iguais'],
 ['19',2,'Coaxial Micro-Coax UT-141C de entrada',f'Percurso CAD{fmt(p["cabos_entrada"][0]["comprimento_eixo_entre_planos"])}; acrescentar preparo/encaixe N'],
 ['20','q.s.','Consumíveis','Solda, fluxo e selante compatível PVC/EPDM/Al; selecionar processo de oficina']]
with (OUT/'BOM_R17.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.writer(f,delimiter=';');w.writerow(['Item','Qtd','Descrição','Especificação']);w.writerows(bom)

# DXFs em unidades mm: camadas separadas de corte, usinagem e dobra.
def dxfnew():
    doc=ezdxf.new('R2010');doc.units=4
    for n,color in [('CORTE',7),('CANAL_2P5',3),('DOBRA',1),('CENTRO',4)]:doc.layers.new(n,dxfattribs={'color':color})
    return doc,doc.modelspace()
def dhole(m,x,y):
    r=8.25;a=math.degrees(math.acos(7/r));v=math.sqrt(r*r-49)
    for sa,ea in [(a,180-a),(180+a,360-a)]:m.add_arc((x,y),r,sa,ea,dxfattribs={'layer':'CORTE'})
    for s in [-1,1]:m.add_line((x+s*7,y-v),(x+s*7,y+v),dxfattribs={'layer':'CORTE'})
for label in ['Inferior','Superior']:
    dx,m=dxfnew();m.add_circle((0,0),55,dxfattribs={'layer':'CORTE'})
    for r in [48.65,51.15]:m.add_circle((0,0),r,dxfattribs={'layer':'CANAL_2P5'})
    for y in [-5,5]:m.add_circle((y,-.859),1.7,dxfattribs={'layer':'CORTE'})
    if label=='Inferior':
        for y in [-22,22]:dhole(m,y,-14.859)
    dx.saveas(OUT/f'Flange_{label}.dxf')
BA=p['chapa']['BA_extremidade'];end=168.8+BA+14
outline=[(-end,-10),(-148,-10),(-148,-45),(148,-45),(148,-10),(end,-10),(end,10),(148,10),(148,45),(-148,45),(-148,10),(-end,10)]
holes=[(x+2.50916841304063,y,2.1) for x in [-96,0,96] for y in [-18,18]]
holes += [(v['x'],v['y'],1.1) for v in p['fixacoes_radiantes']+p['fixacoes_divisor']]
holes += [(sx*(168.8+BA+7),y,1.7) for sx in [-1,1] for y in [-5,5]]
dx,m=dxfnew();m.add_lwpolyline(outline,close=True,dxfattribs={'layer':'CORTE'})
for x,y,r in holes:m.add_circle((x,y),r,dxfattribs={'layer':'CORTE'})
for sx in [-1,1]:m.add_line((sx*(168.8+BA/2),-10),(sx*(168.8+BA/2),10),dxfattribs={'layer':'DOBRA'})
if p['refletor']!='plano90':
    for sy in [-1,1]:m.add_line((-148,sy*(28.5+math.radians(150)*2.8/2)),(148,sy*(28.5+math.radians(150)*2.8/2)),dxfattribs={'layer':'DOBRA'})
dx.saveas(OUT/'Refletor_planificado.dxf')

# Relatorio A4 ilustrado, paginas fixas para revisao.
c=canvas.Canvas(str(OUT/'Relatorio_R17_PRELIMINAR.pdf'),pagesize=(210*mm,297*mm));c.setTitle('P2S13 R17 — montagem DN100 e comparacao de refletores — PRELIMINAR')
header(c,'Antena DN100 • conjunto completo',1)
img(c,M/'imagens/montagem_transparente.png',12,87,186,179)
table(c,[['Envelope nominal','Valor'],['Flanges','Ø110 ×4,76 mm; duas peças'],['Tubo','OD101,6 / ID98 / comprimento350 mm'],['Comprimento entre faces externas','355,12 mm; com N e cabeças: envelope371,72 ×110 ×110 mm'],['Radiantes / alimentação','3 placas de2elementos; divisor duplo1:3; duas entradas N em fase']],12,85,[79,107])
c.showPage();header(c,'Diagramas e decisão sobre as abas',2)
rows=[['5,17 GHz • 0,5 W / 0° em A/B','Abas150°','Plano90']]
for title,fun,nd in [('Ganho frontal (dBi)',lambda r:r['cortes']['H']['ganho_frontal_dBi'],3),('Abertura H (°)',lambda r:r['cortes']['H']['abertura_graus'],2),('Abertura V (°)',lambda r:r['cortes']['V']['abertura_graus'],2),('VSWR ativo A',lambda r:r['VSWR_ativo'][0],3),('VSWR ativo B',lambda r:r['VSWR_ativo'][1],3),('Máximo H (°)',lambda r:r['cortes']['H']['pico_graus'],2),('Máximo V fino (°)',lambda r:r['pico_V_fino_graus'],3),('ΔS antena / 6passes',lambda r:r['convergencia']['antena']['delta_s'],4)]:rows.append([title,fmt(fun(old),nd),fmt(fun(new),nd)])
table(c,rows,12,261,[94,46,46]);img(c,OUT/'comparacao_polar_HV.png',10,69,190,96)
y=para(c,(ROOT/'decisao_refletor.txt').read_text(encoding='utf-8'),12,68,186)
para(c,'Os dois ensaios comparam somente a dobra lateral. Flanges, linguetas, fixadores e novos cabos de entrada ainda não estão nesta qualificação RF. Ganho com rede inclui o divisor e os seis cabos de saída RLGC; não inclui as perdas dos novos trechos N–divisor. PVC: propriedades nominais, não medidas no tubo comercial.',12,y-3,186,True)
c.showPage();header(c,'Montagem interna e interfaces',3)
img(c,M/'imagens/interno_frente.png',10,151,190,111);img(c,M/'imagens/interno_verso.png',10,42,190,110)
para(c,'12 grampos seguram as radiantes; 4 seguram a C02. As PCBs permanecem sem novos furos. Dois conectores N atravessam o flange inferior. Seis saídas de134mm foram preservadas; duas novas entradas têm percursos iguais. Verificação CAD: zero interferências volumétricas entre os itens novos e o conjunto.',12,40,186,True)
c.showPage();header(c,'Lista de materiais',4)
table(c,[['Item','Qtd.','Componente / especificação']]+[[a,str(b),name+'<br/>'+spec] for a,b,name,spec in bom[:11]],12,262,[12,12,162])
c.showPage();header(c,'Lista de materiais • continuação',5)
y=table(c,[['Item','Qtd.','Componente / especificação']]+[[a,str(b),name+'<br/>'+spec] for a,b,name,spec in bom[11:]],12,262,[12,12,162])
para(c,'Seleções de materiais mecânicos e dimensões de ferragens são nominais de projeto. Confirmar peças comerciais, dureza/compatibilidade das juntas e espessura real da chapa. A junta comprimida e as arruelas de vedação precisam de ensaio de estanqueidade; não se declara grau IP para o conjunto.',12,y-5,186,True)
c.showPage();header(c,'Conectores e comprimentos dos cabos',6)
img(c,M/'imagens/flange_inferior.png',12,145,186,117)
y=para(c,'<b>N fêmea Amphenol082-6784:</b> recorteØ16,5 com duas faces planas a14mm. Painel permitido1,0–6,75mm; flange4,76mm. Torque de catálogo30in·lbf (3,39N·m). Porca, arruela, junta e termorretrátil integram o kit; não comprar em duplicidade.',12,143,186)
y=para(c,'<b>UT-141C:</b> OD3,581mm, vivoØ0,9195mm, PTFE,50Ω. Raio interno mínimo do catálogo1,905mm. As novas entradas usam raio no eixo6mm, equivalente a4,2095mm interno. Percurso de cada entrada entre planos mecânicos: <b>'+fmt(p['cabos_entrada'][0]['comprimento_eixo_entre_planos'])+'mm</b>. Somar encaixe no conector e preparo de solda; esse valor não é uma ordem de corte final.',12,y-4,186)
y=para(c,'<b>Preparo do conector:</b> desenho do fabricante indica6,05mm de vivo total além da blindagem e4,10mm de vivo além do dielétrico (dielétrico exposto1,95mm). Inserir até o batente e soldar conforme o fabricante. O encaixe interno não está cotado como comprimento de corte no STEP; montar uma amostra antes de liberar o chicote.',12,y-4,186)
para(c,'Seis saídas existentes:134mm físicos,133,82mm nos planos RF. Entradas A/B e ramais correspondentes devem conservar os mesmos comprimentos e posições. O modelo STEP do conector é uma referência mecânica; não fornece materiais internos nem parâmetros S.',12,y-4,186,True)
c.showPage();header(c,'Montagem, inspeção e rastreabilidade',7)
steps=[
 'Usinar flanges e recortes conforme DXF e pranchas. Remover rebarbas dos canais; proteger as faces de vedação. Medir OD, ovalização e parede do lote do tubo antes de cortar os anéis.',
 'Cortar a chapa e executar dobras de extremidade90°, Ri2. A planificação usaK=0,4 como hipótese de oficina; calibrar uma amostra e confirmar a distância entre faces externas das linguetas345,6mm.',
 'Montar os grampos POM e as três placas preservadas. Apoio das radiantes a14,949mm da face frontal do refletor; não pressionar trilhas de RF nem empenar a PCB. Fixar a C02 pelo contorno.',
 'Instalar N no flange inferior com as juntas do kit. Soldar as duas entradas iguais e os seis ramais iguais; limpar resíduos de fluxo. Conferir continuidade, ausência de curto indevido e alívio mecânico das soldas.',
 'Montar flange inferior, tubo e juntas anulares. Fechar com flange superior e quatro M3. Conferir inserção nominal2,2mm por ponta; não usar o aperto para corrigir tubo ou chapa fora de medida.',
 'Inspecionar folgas e vedação, testar variação térmica e retenção mecânica. Confirmar VSWR e diagramas com fechamento completo e PVC do lote antes de liberar fabricação em série.'
]
y=260
for i,s in enumerate(steps,1):y=para(c,f'<b>{i}.</b> '+s,12,y,186)-7
y=para(c,'<b>Escopo:</b> montagem detalhada, não análise estrutural nem certificação IP. Tolerâncias propostas: usinagem do canal±0,05mm; Øexterno±0,10mm; centros de furos±0,10mm; cortar tubo350±0,10mm após aferir esquadro. Espessuras comerciais e expansão térmica devem ser verificadas no protótipo.',12,y,186)-5
para(c,'<b>Fontes:</b><br/>Tigre Série Normal DN100: www.tigre.com.br/produto/tubo-serie-normal-6m<br/>Amphenol: desenho82-6784,revA; STEP local82-6784.stp; www.amphenolrf.com/en-us/assets/file/4069129560/<br/>Micro-Coax UT-141C: www.micro-coax.com/wp-content/uploads/2024/12/micro-coax-ut-141c-datasheet.pdf<br/>PVC elétrico nominal: iemsl.engr.tamu.edu/services/material-characterization-services/material-characterization-examples/ (filme10,2–52,2GHz; extrapolação assumida em5,17GHz).',12,y,186,True)
c.save()

# Pranchas A3 vetoriais, cotas derivadas do mesmo JSON/CAD.
c=canvas.Canvas(str(OUT/'Desenhos_R17_A3_PRELIMINAR.pdf'),pagesize=(420*mm,297*mm));c.setTitle('P2S13 R17 — desenhos A3 — PRELIMINAR')
def line(x1,y1,x2,y2):c.line(x1*mm,y1*mm,x2*mm,y2*mm)
def dimx(x1,x2,y,label):
    c.setLineWidth(.45);line(x1,y,x2,y)
    for x in [x1,x2]:line(x-1.5,y-1.5,x+1.5,y+1.5)
    c.setFont(font,8);c.drawCentredString((x1+x2)/2*mm,(y+2)*mm,label)
def dimy(x,y1,y2,label):
    line(x,y1,x,y2)
    for y in [y1,y2]:line(x-1.5,y-1.5,x+1.5,y+1.5)
    c.saveState();c.translate((x-2)*mm,(y1+y2)/2*mm);c.rotate(90);c.setFont(font,8);c.drawCentredString(0,0,label);c.restoreState()
def pathpoly(points,origin=(0,0),scale=1,close=True):
    q=c.beginPath();q.moveTo((origin[0]+points[0][0]*scale)*mm,(origin[1]+points[0][1]*scale)*mm)
    for x,y in points[1:]:q.lineTo((origin[0]+x*scale)*mm,(origin[1]+y*scale)*mm)
    if close:q.close()
    c.drawPath(q)
def flangeview(ox,oy,lower):
    for r in [55,48.65,51.15]:c.circle(ox*mm,oy*mm,r*mm)
    c.setDash(3,2);line(ox-59,oy,ox+59,oy);line(ox,oy-59,ox,oy+59);c.setDash()
    for y in [-5,5]:c.circle((ox+y)*mm,(oy-.859)*mm,1.7*mm)
    if lower:
        for y in [-22,22]:
            a=math.acos(7/8.25);pts=[(8.25*math.cos(v)+y,8.25*math.sin(v)-14.859) for v in np.linspace(a,math.pi-a,40)]
            pts += [(8.25*math.cos(v)+y,8.25*math.sin(v)-14.859) for v in np.linspace(math.pi+a,2*math.pi-a,40)]
            pathpoly(pts,(ox,oy))
    dimx(ox-55,ox+55,oy-65,'Ø110');text(c,ox-38,oy+61,'INFERIOR' if lower else 'SUPERIOR',10,True)
header(c,'01 • Flanges e canal de vedação',1,True);flangeview(78,180,True);flangeview(207,180,False)
text(c,284,244,'Corte radial do canal • escala4:1',10,True)
ox,oy=292,194;s=4
pathpoly([(0,0),(6.35,0),(6.35,4.76),(2.5,4.76),(2.5,2.26),(0,2.26)],(ox,oy),s)
dimy(ox+32,oy,oy+4.76*s,'4,76');dimx(ox,ox+2.5*s,oy+28,'2,50');dimy(ox-6,oy+2.26*s,oy+4.76*s,'2,50')
text(c,284,180,'Canal ID97,30 / OD102,30',9);text(c,284,173,'Fundo residual2,26; parede externa3,85',9)
table(c,[['Referência a partir do centro do flange','Y','Z relativo','Forma'],['Conector A','−22','−14,859','Ø16,5; faces14'],['Conector B','+22','−14,859','Ø16,5; faces14'],['Lingueta esquerda','−5','−0,859','Ø3,4 passante'],['Lingueta direita','+5','−0,859','Ø3,4 passante']],20,99,[132,34,34,70])
para(c,'Al6061-T6 nominal; 4,76mm. Dois flanges, canal voltado para o tubo. Recortes N somente no inferior. Escala1:1 nas faces. Canal±0,05; centros±0,10mm. Fazer ensaio de encaixe e vedação com o lote real de PVC. DXF distingue corte e usinagem do canal.',20,42,375,True)
c.showPage();header(c,'02 • Refletor planificado e furação',2,True)
pathpoly(outline,(210,169));
for x,y,r in holes:c.circle((210+x)*mm,(169+y)*mm,r*mm)
c.setDash(3,2)
for sx in [-1,1]:line(210+sx*(168.8+BA/2),159,210+sx*(168.8+BA/2),179)
if p['refletor']!='plano90':
    for sy in [-1,1]:line(62,169+sy*(28.5+math.radians(150)*2.8/2),358,169+sy*(28.5+math.radians(150)*2.8/2))
c.setDash();dimx(210-end,210+end,232,fmt(2*end)+' total');dimx(62,358,222,'296 face principal');dimy(48,124,214,'90');dimy(405,159,179,'20 lingueta')
table(c,[['Grupo de furos','X (origem no centro da chapa)','Y','Ø / quantidade'],['Passagem de cabos','−93,490832; +2,509168; +98,509168','±18','4,2 / 6'],['Grampos radiantes','−141,5; −50,5; −45,5; +45,5; +50,5; +141,5','±14','2,2 / 12'],['Grampos divisor','−12,159855; +26,840145','±12','2,2 / 4'],['Fixação aos flanges','±'+fmt(168.8+BA+7,6),'±5','3,4 / 4']],20,107,[51,192,40,77])
para(c,'Al5052-H32, espessura2. Duas dobras finais90° para trás; Ri2; K0,4 nominal; BA='+fmt(BA,6)+'mm por dobra. Tangência em X±168,8; fim da curva planificada em X±'+fmt(168.8+BA,6)+'. Calibrar K no ferramental e conferir dimensão dobrada345,6mm entre faces externas das abas. Escala1:1.',20,45,375,True)
if p['refletor']!='plano90':para(c,'Abas laterais: giro150° para trás a partir da chapa plana (ângulo interno30°), tangênciaY±28,5. BA7,330383; reta9,169617; centro de dobra planificadoY±32,165191. Alívios conforme contorno. Pontilhados: centro da dobra.',20,27,375,True)
c.showPage();header(c,'03 • Extremidades dobradas e fechamento',3,True)
ox,oy=32,174;s=3
# Secao local tangencia +X, tubo junto ao flange separado em diagrama inferior.
pts=[(-20,0),(0,0)]+[(4*math.sin(a),-4+4*math.cos(a)) for a in np.linspace(0,math.pi/2,30)]+[(4,-18),(2,-18),(2,-4)]+[(2*math.sin(a),-4+2*math.cos(a)) for a in np.linspace(math.pi/2,0,30)]+[(-20,-2)]
pathpoly(pts,(ox+62,oy),s);text(c,22,244,'Detalhe da aba +X • escala3:1',11,True)
dimy(117,120,162,'14 reto');dimy(125,120,174,'18 total');dimx(100,106,112,'2');text(c,22,101,'Ri2 / Rexterno4; largura da lingueta20',9)
text(c,22,92,'Furos: Y±5; Z−11; Ø3,4.',9);text(c,22,84,'Contato com flange na face X+172,8.',9)
if p['refletor']!='plano90':
    a=math.radians(150);tail=45-28.5-a*2.8
    yz=[(-28.5,0),(28.5,0)]+[(28.5+4*math.sin(v),-4+4*math.cos(v)) for v in np.linspace(0,a,35)]
    yz += [(28.5+4*math.sin(a)+tail*math.cos(a),-4+4*math.cos(a)-tail*math.sin(a)),(28.5+2*math.sin(a)+tail*math.cos(a),-4+2*math.cos(a)-tail*math.sin(a))]
    yz += [(28.5+2*math.sin(v),-4+2*math.cos(v)) for v in np.linspace(a,0,35)]+[(-28.5,-2)]
    # Perfil direito com centro plano; a outra aba e simetrica no CAD.
    pathpoly(yz,(65,72),.9,False);text(c,20,57,'Seção lateral: Ri2; dobra150°; centro plano57.',8)
img(c,M/'imagens/detalhe_lingueta.png',148,119,252,135)
table(c,[['Fechamento axial (X)','Inferior','Superior'],['Extremidade do PVC','−175,00','+175,00'],['Face interna do flange','−172,80','+172,80'],['Fundo do canal','−175,30','+175,30'],['Face externa do flange','−177,56','+177,56'],['Junta nominal','0,50 livre →0,30 montada','Compressão40% a ensaiar']],150,111,[116,63,63])
para(c,'M3×12 com arruela externa de vedação, flange4,76, aba2, arruela interna0,5 e porca2,4. Duas fixações em cada extremidade. O tubo entra2,2mm no canal de2,5mm. Não há ensaio estrutural ou térmico; o comprimento do tubo e as juntas precisam ser aferidos no protótipo.',20,51,375)
c.showPage();header(c,'04 • Grampos usinados de poliacetal',4,True)
def clipview(ox,oy,seat,lip,top,label):
    s=3;pts=[(-4,0),(3,0),(3,top),(-2,top),(-2,lip),(0,lip),(0,seat),(-4,seat)]
    pathpoly(pts,(ox,oy),s);c.setDash(2,2);line(ox+1.5*s,oy-5,ox+1.5*s,oy+top*s+5);c.setDash()
    dimx(ox-12,ox+9,oy-9,'7');dimy(ox+20,oy,oy+seat*s,fmt(seat));dimy(ox+30,oy,oy+top*s,fmt(top));text(c,ox-35,oy+top*s+12,label,10,True)
clipview(64,121,14.949,15.759,17.759,'Radiantes • 12 peças');clipview(222,111,33.196,34.836,36.836,'Divisor • 4 peças')
para(c,'<b>Perfil local de ambos os grampos</b><br/>Origem X0 no bordo da PCB; Z0 no apoio contra a chapa.<br/>Base: X−4 a+3 (7mm).<br/>Montante externo: X0 a+3 (3mm).<br/>Lábio: X−2 a+3; avanço2mm sobre a PCB; espessura2mm.<br/>Largura: Y−2,5 a+2,5 (5mm).<br/>Furo passanteØ2,2 em X+1,5/Y0.<br/>Espelhar o perfil para o bordo oposto. Divisor: inverter no verso da chapa.<br/>Usinagem proposta±0,10mm; altura de assentamento±0,05mm; confirmar com as PCBs reais.',296,240,103)
text(c,20,86,'Perfis espelhados nos bordos opostos; largura fora do plano5mm.',10)
table(c,[['Característica','Radiante','Divisor'],['Apoio / folga','14,949 /0,05 acima da PCB','33,196 até o cobre de massa /0,05 abaixo do sinal'],['Passagem do parafuso','Ø2,2 no eixo a1,5 do bordo','Ø2,2 no eixo a1,5 do bordo'],['Parafuso / porca','M2×25; 2 arruelas + porca','M2×45; 2 arruelas + porca'],['Montagem','Frente do refletor; sem furar a PCB','Verso do refletor; perfil invertido']],20,77,[89,138,138])
para(c,'POM natural; peças usinadas. Cotas nominais de assentamento. Evitar aperto que deforme o laminado; validar folga e retenção no protótipo. Roscas e ferragens no CAD são simplificadas. Escala dos perfis3:1.',20,28,375,True)
c.showPage();header(c,'05 • Montagem geral e referências',5,True)
img(c,M/'imagens/montagem_corte.png',12,107,395,153)
table(c,[['Cota / posição no CAD','Valor nominal'],['Tubo / flanges / total fechado','Ø101,6×350 / Ø110×4,76 /355,12 entre faces externas'],['Eixo longitudinal do tubo','X; Y0; Z−10,141'],['Centros das PCBs (X,Y)','(−96,0); (0,0); (+96,0)'],['Altura do núcleo radiante / passo','Z14,949 até15,709; radiadores48; placas96'],['C02: contorno e níveis','X−10,659855 a25,340145; Y±39; núcleoZ−36,751 a−35,231'],['Conectores no flange inferior','Y±22; Z−25; entre centros44'],['Entradas / saídas UT-141C','2×'+fmt(p['cabos_entrada'][0]['comprimento_eixo_entre_planos'])+' entre planos; 6×134 físicos']],20,104,[124,250])
c.save()

# Render de TODAS as paginas para inspecao humana; nao autoaprova aspecto visual.
render=OUT/'revisao';render.mkdir(exist_ok=True)
audit=[]
for file in ['Relatorio_R17_PRELIMINAR.pdf','Desenhos_R17_A3_PRELIMINAR.pdf']:
    pdf=fitz.open(OUT/file);assert len(pdf)>0
    for i,page in enumerate(pdf):
        name=file.split('.')[0]+f'_{i+1:02d}.png';page.get_pixmap(matrix=fitz.Matrix(1.4,1.4)).save(render/name)
        assert page.get_text().strip();audit.append(dict(pdf=file,pagina=i+1,imagem=name,caracteres=len(page.get_text())))
(OUT/'auditoria_estrutural_pdf.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print('R17_DOCUMENTOS',len(audit),'paginas para revisar')
