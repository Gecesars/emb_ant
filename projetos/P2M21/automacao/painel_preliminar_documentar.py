"""Documentacao e BOM R18; utiliza imagens reais do FreeCAD e dados preservados."""
from pathlib import Path
import json,csv,math,hashlib,shutil
import ezdxf
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4,A3,landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from PIL import Image as PILImage

ROOT=Path('D:/dev/EMBRAER/P2M21/R18_Mecanica_Preliminar')
REPO=Path('D:/dev/EMBRAER/emb_ant')
DIM=json.loads((ROOT/'dimensoes.json').read_text())
CFG=json.loads((ROOT.parent/'R17_Dez_Celulas_78mm/configuracao.json').read_text())
OUT=ROOT/'imagens';OUT.mkdir(exist_ok=True)
pdfmetrics.registerFont(TTFont('Arial','C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialB','C:/Windows/Fonts/arialbd.ttf'))
N_URL='https://www.amphenolrf.com/en-us/assets/file/4069129560/'
C_URL='https://www.micro-coax.com/wp-content/uploads/2024/12/micro-coax-ut-141c-datasheet.pdf'
ROWS=[
 ('01','PCB 4_elementos / C12','10 un','RO4350B, núcleo 0,76 mm; 70 × 184 mm; Cu 35 µm/face, ENIG. Dois 1:4 por placa.','Geometria RF e KiCad preservada'),
 ('02','Refletor com base dobrada','1 un','Alumínio 5052, 2 mm. Face 968 × 162 mm; dobra a 90°, Ri 2 mm.','Têmpera, acabamento e K da dobra a confirmar'),
 ('03','Grampo isolante de borda','40 un','POM natural; largura 5 mm; apoio a 14,949 mm. Quatro por PCB, sem furar o laminado.','Usinagem proposta; ajustar folga à espessura real'),
 ('04','Parafuso M2 × 25','40 un','Inox A2; cabeça cilíndrica. Rosca simplificada no CAD.','Dimensões e aperto a confirmar no protótipo'),
 ('05','Porca M2','40 un','Inox A2; envelope de 1,6 mm de altura no CAD.','Selecionar catálogo antes da compra'),
 ('06','Arruela M2','80 un','Inox A2; referência geométrica Ø4 / Ø2,2 × 0,5 mm.','Duas por fixação'),
 ('07','N fêmea Amphenol 082-6784','2 kits','50 Ω, RG-402/0,141 pol. Kit com porca, arruela, junta e termorretrátil.','STEP fornecido pelo usuário; não comprar acessórios em duplicidade'),
 ('08','Micro-Coax UT-141C — ramais','20 × 50 mm','1,000 m geométrico; dois cabos retos por PCB.','São os cabos do ensaio RF, não o corte final do chicote'),
 ('09','Micro-Coax UT-141C — entradas','2 × 459,25 mm','0,9185 m entre interfaces propostas, N até região central.','Proposta mecânica; inserções e decapagens ainda não incluídas'),
 ('10','Distribuição externa A/B','2 redes 1:10','Duas entradas independentes para as vinte conexões das dez PCBs.','PENDENTE: reserva de espaço, sem cobre dimensionado'),
 ('11','Fixação ao mastro / fechamento','A definir','Quatro furos de interface Ø6,5 mm; radome, tampa e fixadores externos não definidos.','Fora da liberação desta revisão'),
 ('12','Curto DC das entradas','2, a definir','Integração das bobinas depende da rede externa e da terminação N.','Não instalado nem validado neste painel'),
]
with (ROOT/'lista_materiais_PRELIMINAR.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f,delimiter=';');w.writerow(['Item','Componente','Quantidade','Especificação','Estado']);w.writerows(ROWS)
(ROOT/'lista_materiais.json').write_text(json.dumps([dict(zip(['item','componente','quantidade','especificacao','estado'],r)) for r in ROWS],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# DXF de corte 1:1, distinto das linhas de dobra.
ba=DIM['dobra']['BA_mm'];xmin=-484-ba-66;holex=DIM['recortes_N']['x_plano']
def double_d(x,y):
 q=math.sqrt(8.25**2-7**2);b=math.tan((math.pi-2*math.acos(7/8.25))/4)
 return [(x-q,y-7,0),(x+q,y-7,b),(x+q,y+7,0),(x-q,y+7,b)]
cut=ezdxf.new('R2010');cut.units=4;cut.layers.new('CORTE',dxfattribs={'color':7});m=cut.modelspace()
m.add_lwpolyline([(xmin,-81),(484,-81),(484,81),(xmin,81)],close=True,dxfattribs={'layer':'CORTE'})
holes=[]
for i,p in enumerate(CFG['portas'],1):holes.append((p['name'],p['x'],p['y'],4.2,'Passagem coaxial, escarear rebarbas'))
for i,p in enumerate(DIM['fixacoes_pom'],1):holes.append(('M2_%02d'%i,p['x'],p['y'],2.2,'Grampo POM'))
for i,(x,y) in enumerate(DIM['montagem_mastro_interface'],1):holes.append(('IF_%02d'%i,x,y,6.5,'Interface mecanica; suporte externo pendente'))
for _,x,y,d,_ in holes:m.add_circle((x,y),d/2,dxfattribs={'layer':'CORTE'})
for y in [-24,24]:m.add_lwpolyline(double_d(holex,y),format='xyb',close=True,dxfattribs={'layer':'CORTE'})
cut.saveas(ROOT/'Refletor_CORTE_PRELIMINAR_1a1.dxf')
bend=ezdxf.new('R2010');bend.units=4;bend.layers.new('DOBRA',dxfattribs={'color':1});bm=bend.modelspace()
for x in [-484-ba,-484]:bm.add_line((x,-81),(x,81),dxfattribs={'layer':'DOBRA'})
bm.add_line((-484-ba/2,-81),(-484-ba/2,81),dxfattribs={'layer':'DOBRA'})
bend.saveas(ROOT/'Refletor_DOBRA_PRELIMINAR_1a1.dxf')
with (ROOT/'furacao_refletor_PRELIMINAR.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f,delimiter=';');w.writerow(['ID','X plano mm','Y mm','Diametro mm','Descricao']);w.writerows(holes)
 for tag,y in [('N_A',-24),('N_B',24)]:w.writerow([tag,holex,y,16.5,'Duplo D: 14 mm entre planos; eixo a Z=-40 na chapa dobrada'])
re=ezdxf.readfile(ROOT/'Refletor_CORTE_PRELIMINAR_1a1.dxf')
assert len(re.modelspace())==67 and len(re.modelspace().query('CIRCLE'))==64

fig,ax=plt.subplots(figsize=(14,4))
ax.plot([xmin,484,484,xmin,xmin],[-81,-81,81,81,-81],color='#444')
for _,x,y,d,_ in holes:ax.add_patch(plt.Circle((x,y),d/2,fill=False,color='#255a7c',lw=.6))
for y in [-24,24]:
 a=np.linspace(0,2*np.pi,200);x=holex+8.25*np.cos(a);yy=y+np.clip(8.25*np.sin(a),-7,7);ax.plot(x,yy,color='#ae542c')
ax.axvline(-484,c='#be3333',ls='--',lw=.8);ax.axvline(-484-ba,c='#be3333',ls='--',lw=.8)
ax.set_aspect('equal');ax.set(xlim=(xmin-25,510),ylim=(-115,125),xlabel='X planificado (mm)',ylabel='Y (mm)',title='Chapa plana — PRELIMINAR | %.3f × 162 × 2 mm | DXF em mm, 1:1'%DIM['chapa_plana_mm'][0]);ax.grid(alpha=.15)
fig.tight_layout();fig.savefig(OUT/'chapa_plana.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(7,4))
for r,col in [(1.7905,'#b88140'),(1.515,'#e8e8e0'),(.45975,'#c3b479')]:ax.add_patch(plt.Circle((0,0),r,color=col,ec='#444'))
ax.annotate('Ø3,581 mm — cobre',xy=(1.6,.8),xytext=(2.5,1.5),arrowprops={'arrowstyle':'-'})
ax.annotate('PTFE',xy=(.9,-.8),xytext=(2.5,-.5),arrowprops={'arrowstyle':'-'})
ax.annotate('Ø0,9195 mm\ncondutor prateado',xy=(0,0),xytext=(-4,1.2),arrowprops={'arrowstyle':'-'})
ax.set_aspect('equal');ax.set(xlim=(-4.3,5.5),ylim=(-2.2,2.2));ax.axis('off');fig.tight_layout();fig.savefig(OUT/'cabo_secao.png',dpi=180);plt.close(fig)

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Texto',fontName='Arial',fontSize=9.5,leading=13,spaceAfter=7,textColor=colors.HexColor('#263440')))
styles.add(ParagraphStyle(name='TituloR',fontName='ArialB',fontSize=20,leading=24,spaceAfter=16,textColor=colors.HexColor('#173c57')))
styles.add(ParagraphStyle(name='SubR',fontName='ArialB',fontSize=12,leading=16,spaceAfter=10,textColor=colors.HexColor('#173c57')))
styles.add(ParagraphStyle(name='Celula',fontName='Arial',fontSize=8,leading=10))
styles.add(ParagraphStyle(name='FonteR',fontName='Arial',fontSize=8,leading=11,spaceAfter=6,textColor=colors.HexColor('#485762')))
def p(s,style='Texto'):return Paragraph(s,styles[style])
def table(rows,widths):
 t=Table([[p(str(x),'Celula') for x in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dbe6ed')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#5a788c')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f6f8')]),('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6)]));return t
def photo(n,w=515,h=None):
 path=OUT/n
 if not path.exists():path=Path(n)
 im=PILImage.open(path);ratio=im.height/im.width
 return Image(str(path),width=w,height=w*ratio if h is None else h)
story=[]
def page(title):
 if story:story.append(PageBreak())
 story.append(p(title,'TituloR'))
def footer(c,doc):
 c.setFont('ArialB',9);c.setFillColor(colors.HexColor('#b24527'));c.drawString(38,A4[1]-24,'EFTX  |  P2M21 R18  |  PRELIMINAR')
 c.setFont('Arial',8);c.setFillColor(colors.HexColor('#5a6670'));c.drawString(38,22,'10/11/2026 • Sem liberação de fabricação ou qualificação RF da montagem R18')
 c.drawRightString(A4[0]-38,22,str(doc.page))

page('Painel de dez células radiantes')
story+=[p('Duas colunas • cinco PCBs por coluna • 40 radiadores','SubR'),photo('isometrica_frontal.png'),Spacer(1,12),
 p('Documentação mecânica preliminar baseada na última configuração preparada. A simulação de dez placas foi interrompida por solicitação do usuário durante o segundo passe. Não há ganho ou diagrama final qualificado para este conjunto.'),
 table([['Parâmetro','Configuração R18'],['Célula básica','4_elementos, revisão C12; duas polarizações e dois divisores 1:4 impressos'],['Arranjo','20 níveis de radiadores × 2 colunas; 48 mm na vertical e 78 mm entre colunas'],['Placas','10 × 70 × 184 mm; passo de 192 mm; folgas de 8 mm'],['Refletor','Face 968 × 162 mm; alumínio de 2 mm; base dobrada para os dois N'],['Alimentação final','2 entradas N; distribuição externa para 20 conexões ainda pendente']],[140,375]),
 p('As imagens são renderizações do arquivo FreeCAD entregue. Azul translúcido na traseira representa apenas reserva de espaço para a rede futura, não uma PCB projetada.','FonteR')]
page('Montagem frontal e traseira')
story+=[Table([[photo('frente.png',240),photo('traseira_reserva.png',240)]],colWidths=[257,257]),
 p('Frente: dez cópias do módulo C12, sem alterações no cobre. Traseira: vinte cabos de ensaio, duas entradas propostas e região reservada de 820 × 130 × 20 mm para a distribuição.'),
 p('Foram preservados os 410 objetos de PCB, vias, soldas e coaxiais das células. Dobra, fixações e conectores são acréscimos mecânicos; seus efeitos de RF não estão incluídos nos resultados anteriores.')]
page('PCB 4_elementos — geometria preservada')
story+=[photo('pcb_frente.png'),photo('pcb_verso.png'),
 table([['Item','Especificação da C12'],['Laminado / cobre','RO4350B: núcleo 0,76 mm; εr de projeto 3,66; tanδ nominal 0,0037; cobre 35 µm por face e ENIG'],['Rede impressa','Um divisor 1:4 por polarização; sinais e retornos independentes A/B'],['Furação elétrica','Duas entradas PTH Ø1,10 mm e oito vias PTH Ø0,40 mm; nenhum furo mecânico novo na PCB'],['Fabricação','Geometria do KiCad e Gerbers 4_elementos preservada; máscara RF aberta; não houve nova cotação']],[135,380]),
 p('A espessura nominal núcleo+cobre é 0,83 mm; tolerâncias do laminado e do acabamento devem ser confirmadas antes de definir o ajuste final dos grampos. Os arquivos Gerber existentes não foram alterados.','FonteR')]
page('Apoio em poliacetal e fixação')
story+=[Table([[photo('fixacao_pom.png',255),photo('grampo_isolado.png',240)]],colWidths=[265,250]),
 table([['Característica','Proposta mecânica'],['Quantidade / seção','40 grampos de POM; quatro por placa; largura de 5 mm'],['Altura','Face inferior do núcleo a 14,949 mm do refletor; cobre inferior a 14,914 mm'],['Retenção','Grampo de borda, com lábio superior; folga nominal de 0,05 mm acima do núcleo no CAD'],['Parafusos','40 M2 × 25, 40 porcas e 80 arruelas; furos de passagem Ø2,2 mm no refletor'],['Conferência','312 pares de interfaces novas verificados, sem interseções volumétricas; 581 objetos físicos válidos']],[140,375]),
 p('Os grampos usam as bordas sem cobre nas extremidades das placas. A espessura real da PCB acabada, a folga de montagem, o comportamento do POM e o aperto dos M2 precisam ser definidos por protótipo. O CAD não representa a hélice das roscas.'),
 p('Não foi feita análise de esforço, vento, fluência do POM ou variação térmica. Estas verificações pertencem à futura liberação mecânica.','FonteR')]
page('Refletor, dobra e planificação')
story+=[photo('refletor_dobrado.png'),photo('chapa_plana.png'),
 table([['Definição','Valor nominal'],['Chapa plana','%.3f × 162 × 2 mm'%DIM['chapa_plana_mm'][0]],['Dobra inferior','90°; raio interno 2 mm; K=0,4 assumido; desenvolvimento %.6f mm'%ba],['Recortes','20 passagens coaxiais Ø4,2; 40 fixações Ø2,2; 4 interfaces Ø6,5; 2 duplo-D dos N'],['Conectores N','Ø16,50 mm limitado por planos separados por 14 mm; centros Y=±24 mm e Z=−40 mm']],[140,375]),
 p('O DXF de CORTE contém 67 contornos fechados, em milímetros e escala 1:1. As três linhas de DOBRA são fornecidas em arquivo separado. Confirmar raio, fator K, ferramental, têmpera e tolerâncias antes de cortar a chapa.','FonteR')]
page('Conector N fêmea e vedação')
story+=[photo('conector_3d.png',300),
 table([['Produto','Amphenol 082-6784 (desenho 82-6784)'],['Interface','N fêmea, 50 Ω; para RG-402 / semirrígido ou conformável de 0,141 pol.'],['Montagem','Inserção pelo lado externo; junta sob o flange, porca e arruela no lado interno'],['Painel','Espessura indicada de 1,0 a 6,75 mm; esta chapa tem 2,0 mm'],['Referência elétrica','DC–18 GHz; VSWR de catálogo 1,12 até 6 GHz. Não é medição desta antena.'],['Aperto de painel','30 lbf·in, aproximadamente 3,39 N·m, conforme desenho do fabricante']],[140,375]),
 p('Foi usado o STEP 82-6784.stp fornecido pelo usuário. A porca/arruela foi separada por envelope geométrico e deslocada 4,25 mm da pose de catálogo para encostar na chapa de 2 mm; o original foi preservado. O STEP é referência mecânica, não modelo RF completo.'),
 p('O IP67 publicado aplica-se ao conector nas condições do fabricante. Não constitui classificação IP do painel, que ainda depende de radome, tampa e ensaio de vedação.'),
 p('<link href="'+N_URL+'" color="#155b8c">Fonte: desenho oficial Amphenol 082-6784</link>. O KLC CF-164 permanece alternativa de estudo; não substitui diretamente a fixação e a vedação adotadas.','FonteR')]
page('Cabos e interfaces de alimentação')
story+=[photo('cabo_secao.png'),
 table([['Produto','Micro-Coax UT-141C'],['Construção','Semirrígido de 50 Ω; blindagem em cobre, dielétrico PTFE, condutor central prateado'],['Diâmetros','Externo 3,581 mm; condutor central 0,9195 mm'],['Dobra','Raio interno mínimo de catálogo 1,905 mm; o roteamento mostrado é reto'],['Atenuação típica','27,6 dB/100 ft a 5 GHz, equivalente a aproximadamente 0,906 dB/m. Não é medição a 5,17 GHz.'],['Ramais das células','20 trechos de 50 mm, total 1,000 m: referência geométrica do ensaio'],['Entradas propostas','2 trechos iguais de 459,25 mm, total 0,9185 m, até a região central reservada']],[140,375]),
 p('Os 1,9185 m são apenas a soma dos segmentos representados. Não incluem o futuro chicote de distribuição, sobras, inserções, decapagens ou compensação de fase. Não utilizar esta soma como quantidade final de compra ou gabarito de corte.'),
 p('RG-402 identifica uma família dimensional, não garante o mesmo raio de dobra nem a mesma atenuação. O cabo alternativo deve ser conferido pelo código e datasheet antes da substituição.'),
 p('<link href="'+C_URL+'" color="#155b8c">Fonte: Micro-Coax UT-141C, ficha técnica oficial</link>. No modelo RF das células foram usados os parâmetros nominais documentados nos arquivos de origem.','FonteR')]
page('Lista de materiais — preliminar')
story+=[p('Quantidades para um painel de dez PCBs. Itens de catálogo e comprimentos propostos devem passar pela revisão de fabricação antes da compra.'),
 table([['Item / produto','Qtd.','Especificação e estado']]+[[r[0]+' — '+r[1],r[2],r[3]+' '+r[4]] for r in ROWS],[125,75,315]),
 p('A lista editável acompanha esta entrega em lista_materiais_PRELIMINAR.csv. Acessórios fornecidos nos kits dos N estão incluídos no item 07.','FonteR')]
page('Histórico RF e limites desta revisão')
r15=json.loads((ROOT.parent/'R15_Oito_Celulas_8passes/resultado.json').read_text());r16=json.loads((ROOT.parent/'R16_Oito_Celulas_78mm/resultado.json').read_text())
story+=[table([['Configuração','G frontal','H / V','ΔS / estado'],['8 placas, 72 mm, 8 passes','19,8469 dBi','24,351° / 3,748°','0,050015; não convergida'],['8 placas, 78 mm, 6 passes','19,4798 dBi','22,957° / 3,712°','0,103144; não convergida'],['10 placas, 78 mm','Sem resultado final','Sem diagramas finais','Interrompida pelo usuário no passe 2']],[150,95,120,150]),
 photo(str(ROOT.parent/'R15_Oito_Celulas_8passes/polar_HV.png')),
 p('Os 19,85 dBi da rodada de oito placas incluem as perdas dielétricas dos divisores impressos nas PCBs, as perdas dos condutores e dos cabos físicos de 50 mm, além do descasamento. Não incluem a rede externa de duas entradas para todas as placas.'),
 p('Todos os resultados da tabela referem-se a 5,17 GHz, com as entradas iguais e em fase, potência incidente total de 1 W. Não são ganhos de uma entrada MIMO independente e não qualificam a banda inteira. A dobra, os suportes e os N da R18 também não foram simulados.')]
page('Montagem, rastreabilidade e próxima etapa')
for text in [
 '1. Conferir chapa, rebarbas e recortes contra o DXF. Dobrar somente após confirmar Ri, fator K e ferramental; verificar esquadro da base.',
 '2. Montar os N com a junta do kit pelo lado externo. Ajustar porca e arruela à chapa real e aplicar o torque prescrito pelo fabricante. Proteger a interface N durante a montagem.',
 '3. Instalar os grampos de POM e conferir a altura de 14,949 mm. Colocar as PCBs sem furar ou retocar cobre. Verificar folgas e aperto dos M2 antes de fixar definitivamente.',
 '4. Identificar C1/C2 e níveis R1–R5. Preservar as conexões A/B e o passo de 192 mm entre PCBs. Não ligar saídas em paralelo sem a rede de impedâncias projetada.',
 '5. Usar os trechos coaxiais como referências de interface. A lista de corte definitiva e a igualdade de fase dependem da rede externa, das soldas e da preparação do conector.',
 '6. Na próxima etapa: projetar as duas distribuições 1:10, curto DC, chicote final, radome/tampa e fixação ao mastro. Depois, revisar interferências, resistência, vedação e RF do conjunto.'
]:story.append(p(text))
story += [Spacer(1,8),p('Arquivos e rastreabilidade','SubR'),
 table([['Entrega','Conteúdo'],['FreeCAD','Montagem completa, refletor dobrado, planificação e grampo individual'],['STEP / DXF','Chapa dobrada e plana, grampo, cortes 1:1 e marcação de dobra separada'],['Documentos','Este relatório, pranchas A3, BOM CSV/JSON, furação e dimensões JSON'],['Evidência','Comparação dos 410 objetos das células, 312 pares sem interferência, reabertura e hashes'],['Repositório','https://github.com/Gecesars/emb_ant — projetos/P2M21/mecanica_preliminar_R18']],[120,395]),
 p('Esta é uma montagem BREP posicionada, editável no FreeCAD e reproduzível pelos scripts. Não é uma montagem cinemática com juntas, nem um projeto liberado para produção. As fontes e hipóteses estão explicitadas para a próxima etapa.','FonteR')]
doc=SimpleDocTemplate(str(ROOT/'P2M21_R18_Documentacao_PRELIMINAR.pdf'),pagesize=A4,rightMargin=40,leftMargin=40,topMargin=46,bottomMargin=40,title='P2M21 R18 — documentação preliminar',author='EFTX / Engenharia')
doc.build(story,onFirstPage=footer,onLaterPages=footer)

# Tres pranchas A3: vistas, plano de corte e grampo/base.
c=canvas.Canvas(str(ROOT/'P2M21_R18_Desenhos_PRELIMINARES_A3.pdf'),pagesize=landscape(A3));W,H=landscape(A3)
def a3(title,page):
 c.setFont('ArialB',18);c.setFillColor(colors.HexColor('#173c57'));c.drawString(18*mm,H-20*mm,title)
 c.setFillColor(colors.HexColor('#b24527'));c.setFont('ArialB',12);c.drawRightString(W-18*mm,H-20*mm,'PRELIMINAR')
 c.setFont('Arial',9);c.setFillColor(colors.black);c.drawString(18*mm,14*mm,'P2M21 R18 • 10/11/2026 • mm • confirmar tolerâncias e ferramental antes de fabricar');c.drawRightString(W-18*mm,14*mm,'Prancha %s / 3'%page)
def image_box(path,x,y,w,h):c.drawImage(str(path),x,y,width=w,height=h,preserveAspectRatio=True,anchor='c',mask='auto')
a3('01 — Montagem do painel e interfaces',1)
image_box(OUT/'frente.png',18*mm,37*mm,85*mm,230*mm);image_box(OUT/'traseira_reserva.png',110*mm,37*mm,85*mm,230*mm)
texts=['Face refletora: 968 × 162 × 2','10 PCBs de 70 × 184; núcleo 0,76','Passo vertical dos radiadores: 48','Passo entre PCBs: 192','Passo entre colunas: 78','Folgas lateral / vertical: 8 / 8','Altura da face inferior do núcleo: 14,949','20 cabos de referência, 50 mm cada','40 grampos POM, seção de 5 mm','2 N Amphenol 082-6784','Rede externa: 2 × 1:10 PENDENTE','Fechamento e mastro: A DEFINIR']
c.setFont('Arial',12)
for i,t in enumerate(texts):c.drawString(215*mm,(248-i*13)*mm,t)
c.showPage();a3('02 — Chapa planificada / corte',2)
scale=mm/3;ox=30*mm-xmin*scale;oy=175*mm
c.setStrokeColor(colors.black);c.setLineWidth(.6);c.rect(30*mm,oy-81*scale,(484-xmin)*scale,162*scale)
for _,x,y,d,_ in holes:c.circle(ox+x*scale,oy+y*scale,d/2*scale,stroke=1,fill=0)
for y in [-24,24]:
 a=np.linspace(0,2*np.pi,201);path=c.beginPath()
 for j,ang in enumerate(a):
  xx=ox+(holex+8.25*math.cos(ang))*scale;yy=oy+(y+max(-7,min(7,8.25*math.sin(ang))))*scale
  (path.moveTo if j==0 else path.lineTo)(xx,yy)
 path.close();c.drawPath(path)
c.setDash(3,2);c.setStrokeColor(colors.HexColor('#b24527'))
for x in [-484-ba,-484]:c.line(ox+x*scale,oy-81*scale,ox+x*scale,oy+81*scale)
c.setDash();c.setFillColor(colors.black);c.setFont('ArialB',12)
c.drawString(30*mm,215*mm,'Comprimento %.3f • largura 162 • espessura 2 • vista em escala 1:3'%DIM['chapa_plana_mm'][0])
notes=['Material nominal: alumínio 5052; têmpera e acabamento pendentes.','Dobra 90°, Ri=2; K=0,4 assumido; BA=%.6f. Confirmar em oficina.'%ba,'DXF CORTE: 67 contornos, unidades mm, 1:1. DXF DOBRA separado.','Furação: 20 × Ø4,2 + 40 × Ø2,2 + 4 × Ø6,5 + 2 duplo-D Ø16,5 / planos 14.','Origem: centro da face plana do refletor. Base desenvolve no sentido X negativo.','Furos N: X plano=%.6f; Y=±24. Na peça dobrada: Z=−40.'%holex,'Coordenadas completas: furacao_refletor_PRELIMINAR.csv. Não aplicar compensação de corte duas vezes.']
c.setFont('Arial',11)
for i,t in enumerate(notes):c.drawString(30*mm,(125-i*11)*mm,t)
c.showPage();a3('03 — Grampo POM e base dos conectores',3)
image_box(OUT/'grampo_isolado.png',18*mm,98*mm,145*mm,155*mm);image_box(OUT/'base_conectores.png',185*mm,98*mm,215*mm,155*mm)
c.setFont('Arial',11)
for i,t in enumerate(['Grampo: 7 × 5 no plano; altura total 17,759.','Apoio no núcleo: Z14,949; lábio de 2 mm.','Furo Ø2,2; M2×25, duas arruelas e porca.','Folga superior nominal 0,05; rever com PCB acabada.']):c.drawString(18*mm,(85-i*12)*mm,t)
for i,t in enumerate(['Base a 90°; profundidade externa 70.','Centros dos N: Y=±24, Z=−40; distância 48.','Conector externo; junta do kit sob o flange.','Ajustar porca à chapa 2 mm; torque 3,39 N·m.']):c.drawString(210*mm,(85-i*12)*mm,t)
c.save()

readme='''# P2M21 R18 — mecânica PRELIMINAR

Dez placas C12 de quatro elementos, cinco por coluna: 20 níveis × 2 colunas, passo vertical 48 mm e horizontal 78 mm. Face refletora 968 × 162 mm, alumínio 5052 de 2 mm, base dobrada e dois conectores N Amphenol 082-6784, a partir do STEP fornecido pelo usuário. Os 410 objetos das células foram preservados.

**Simulações interrompidas por solicitação do usuário. Nenhuma qualificação RF da R18.** O último cálculo completo de oito placas/72 mm entregou 19,8469 dBi com ΔS 0,050015, sem convergência. O caso de oito placas/78 mm deu 19,4798 dBi e ΔS 0,103144, também preliminar. O ensaio de dez placas foi interrompido durante o segundo passe, sem resultado final.

- [Documentação ilustrada](P2M21_R18_Documentacao_PRELIMINAR.pdf)
- [Três pranchas A3](P2M21_R18_Desenhos_PRELIMINARES_A3.pdf)
- [Montagem FreeCAD](P2M21_R18_PRELIMINAR.FCStd)
- [Refletor dobrado](Refletor_dobrado_PRELIMINAR.FCStd) · [STEP](Refletor_dobrado_PRELIMINAR.step)
- [Planificação](Refletor_planificado_PRELIMINAR.FCStd) · [Corte DXF 1:1](Refletor_CORTE_PRELIMINAR_1a1.dxf) · [Dobras DXF](Refletor_DOBRA_PRELIMINAR_1a1.dxf)
- [Grampo POM](Grampo_POM_PRELIMINAR.FCStd) · [BOM CSV](lista_materiais_PRELIMINAR.csv) · [Furação](furacao_refletor_PRELIMINAR.csv)
- [Dimensões](dimensoes.json) · [Verificação CAD](verificacao_cad.json)

![Montagem frontal](imagens/isometrica_frontal.png)

Há quarenta grampos de POM de largura 5 mm, fixados com M2, sem perfurar as PCBs. O núcleo fica a 14,949 mm do refletor. A folga de retenção e as ferragens são propostas para protótipo, sem aprovação de resistência, vento ou tolerâncias. O desenvolvimento usa Ri=2 mm e K=0,4; confirmar na oficina antes de fabricar.

O cabo de referência é Micro-Coax UT-141C. Os vinte trechos de 50 mm são os do ensaio; as duas entradas retas de 459,25 mm são apenas propostas mecânicas. A soma de 1,9185 m não é a lista de corte ou compra final: faltam a distribuição externa, inserções e sobras. A região azul é **reserva de espaço**, sem placa ou rede RF fabricável. A topologia futura requer duas distribuições 1:10, vinte saídas no conjunto; a rede antiga de dez divisores 1:4 não foi reaproveitada como se atendesse esta configuração.

O Amphenol foi mantido por corresponder ao STEP disponível e à fixação documentada. Sua porca/arruela foi deslocada axialmente 4,25 mm da pose do STEP para a chapa de 2 mm. O original permanece em referencias. O CF-164 não é substituto direto: muda a fixação e exige conferir recorte e vedação. O IP67 de catálogo do N não qualifica o painel, cujo radome, tampa, suporte de mastro, bobinas de curto DC e chicote final ainda devem ser definidos.

O ganho realizado histórico inclui dielétrico das PCBs/divisores impressos, condutores, cabos físicos de 50 mm e descasamento; não inclui a futura rede externa. A R18 acrescenta dobra, suportes e conectores sem novo solve.

Esta montagem é BREP posicionado com scripts de reconstrução; não é um mecanismo com juntas cinemáticas. O Git contém nativos, documentação e evidências compactas, sem malhas ou campos volumétricos.

Fontes: [Amphenol 082-6784](https://www.amphenolrf.com/en-us/assets/file/4069129560/) e [UT-141C](https://www.micro-coax.com/wp-content/uploads/2024/12/micro-coax-ut-141c-datasheet.pdf), consultadas em 10/11/2026. Chat consultado: “Localizar conector N fêmea e cabo”.
'''
(ROOT/'README.md').write_text(readme,encoding='utf-8',newline='\n')
print('DOCUMENTACAO_GERADA_REQUER_REVISAO_VISUAL')
