"""Relatório de engenharia da placa contínua com alimentação central ou dividida."""
import argparse
import csv
import json
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph
from PIL import Image, ImageChops

repo=Path(__file__).resolve().parents[2]
INK="#15333D";TEAL="#006B68";MUTED="#46616D";PALE="#E7F2F0";WARN="#86401D"
W,H=A4


def rows(path):
    with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))


def br(value,dec=2):
    return f"{float(value):.{dec}f}".replace(".",",")


def text(c,x,y,s,size=10,bold=False,color=INK):
    c.setFillColor(colors.HexColor(color));c.setFont("P1H-bold" if bold else "P1H",size);c.drawString(x,y,s)


def para(c,top,s,size=10.3,width=503,x=46):
    style=ParagraphStyle("p",fontName="P1H",fontSize=size,leading=size*1.46,textColor=colors.HexColor(INK))
    node=Paragraph(escape(s),style)
    _,h=node.wrap(width,900);node.drawOn(c,x,top-h)
    return top-h


def table(c,top,widths,labels,data,size=9.7,rh=25):
    assert sum(widths)<=504 and all(len(row)==len(widths) for row in data)
    for n,row in enumerate([labels]+data):
        y=top-(n+1)*rh
        color=TEAL if n==0 else ("#F1F5F5" if n%2 else "#FFFFFF")
        c.setFillColor(colors.HexColor(color));c.rect(46,y,sum(widths),rh,stroke=0,fill=1)
        x=46
        for cell,w in zip(row,widths):
            font="P1H-bold" if n==0 else "P1H"
            assert pdfmetrics.stringWidth(str(cell),font,size)<w-9,(cell,w)
            text(c,x+6,y+(rh-size)/2+1,str(cell),size,n==0,"#FFFFFF" if n==0 else INK)
            x+=w
    return y


def begin(c,n,total,title,sub):
    day=date.today().strftime("%d/%m/%Y")
    text(c,46,802,"P1H   /   ENGENHARIA DE ANTENAS",9,True,TEAL)
    text(c,429,802,"R01  /  R02     "+day,8.4,False,MUTED)
    c.setStrokeColor(colors.HexColor(TEAL));c.setLineWidth(1);c.line(46,788,549,788)
    text(c,46,751,title,22,True);text(c,46,730,sub,10,False,MUTED)
    c.setStrokeColor(colors.HexColor("#CEDCDE"));c.line(46,48,549,48)
    text(c,46,30,"Dez elementos  •  duas polarizações  •  passo de 52,6 mm",8.3,False,MUTED)
    text(c,514,30,f"{n} / {total}",8.3,False,MUTED)


def band(tag):
    folder=repo/"resultados"/("r02_separadas" if tag=="R02-S" else tag.lower())
    source=folder/"metricas_Discreta.csv"
    if not source.exists():return []
    audit=json.loads((folder/"verificacao_Discreta.json").read_text())
    data=rows(source)
    assert audit["pontos"]==17 and [int(r["MHz"]) for r in data]==list(range(5090,5251,10))
    return data


def generate(path):
    for name,file in [("P1H","segoeui.ttf"),("P1H-bold","segoeuib.ttf")]:
        pdfmetrics.registerFont(TTFont(name,str(Path("C:/Windows/Fonts")/file)))
    cases={name:band(name) for name in ("R01","R02","R02-S")}
    complete=all(cases.values())
    count=3+int(bool(cases["R01"] or cases["R02"]))+int(bool(cases["R02-S"]))
    c=Canvas(str(path),pagesize=A4,pageCompression=1)
    c.setTitle("P1H | Distribuição inferior e superior, mecânica, RF e cotação")
    c.setAuthor("Projeto P1H")
    begin(c,1,count,"Distribuição por metade da coluna","Placa contínua em RO4350B de 0,76 mm   •   5,09 a 5,25 GHz")
    data=[]
    for name,rr in cases.items():
        if rr:
            passing=sum(r["atende_H"]=="True" and r["atende_ganho"]=="True" for r in rr)
            lo=min(float(r["ganho_frontal_dBi"]) for r in rr)
            vals=[float(r["H_graus"]) for r in rr]
            data.append([name,br(lo)+" dBi",br(min(vals))+"–"+br(max(vals))+"°",f"{passing}/17"])
        else:data.append([name,"Em qualificação","Em qualificação","Pendente"])
    text(c,46,689,"Ganho e cobertura com o painel montado",14,True,TEAL)
    table(c,674,[56,142,160,145],["Painel","Menor ganho frontal","Faixa de abertura H","H e ganho na meta"],data)
    if complete:
        verdict="A tabela resume a aprovação conjunta de ganho e abertura horizontal por frequência. A página de dados identifica os pontos e as aberturas verticais."
    else:
        verdict="Relatório parcial. A validação de ganho e cobertura aguarda os campos convergidos do painel nas 17 frequências. Os resultados de rede da página seguinte já passaram pela verificação independente."
    para(c,555,verdict)
    text(c,46,487,"O que mudou no chicote",14,True,TEAL)
    para(c,467,"A R02 mantém duas entradas N. Uma placa distribui as polarizações A e B aos cinco elementos inferiores e a outra atende aos cinco superiores. Os vinte ramais passaram de 254 para 130 mm. Cada percurso N–radiador passou de 560,64 para 533,79 mm de coaxial. A R02-S usa as mesmas redes e dez PCBs individuais em guias de POM.")
    with Image.open(repo/"freecad/mecanica_R02/Verso_R02.png") as source:
        art=source.convert("RGB")
        bounds=ImageChops.difference(art,Image.new("RGB",art.size,"white")).getbbox()
        c.drawImage(ImageReader(art.crop(bounds)),46,251,503,132,preserveAspectRatio=True,mask="auto")
    text(c,46,230,"Vista do verso em FreeCAD. Os dois conectores N estão na base, à esquerda.",8.8,False,MUTED)
    text(c,46,191,"Condição de aceitação",12.4,True)
    para(c,173,"Com 0,5 W a 0° em cada conector, medir ganho realizado em +Z de pelo menos 16 dBi e abertura horizontal de 81° a 99°. A vertical pode ser mais estreita que 7°. O corte YZ é horizontal e o XZ é vertical. A largura usa os dois cruzamentos de −3 dB do lóbulo principal.")
    c.showPage()

    begin(c,2,count,"Alimentação em cargas de 50 Ω","Matrizes HFSS dos divisores, propagação nos coaxiais e reflexões entre os estágios")
    record=rows(repo/"resultados/r02/rede/rede_cargas_50ohm.csv")
    feed={(int(r["MHz"]),r["rede"]):r for r in record}
    data=[]
    for f in range(5090,5251,10):
        a,b=feed[f,"R01"],feed[f,"R02"]
        data.append([br(f/1000),br(a["perda_excedente_dB"],3),br(b["perda_excedente_dB"],3),
                     br(100*float(b["potencia_saidas_W"])),br(b["fase_pico_a_pico_graus"],3)])
    table(c,697,[63,104,106,111,119],["GHz","R01 perda (dB)","R02 perda (dB)","R02 às cargas (%)","R02 fase p-p (°)"],data,9.5,21)
    text(c,46,288,"A R02 entregou 82,25% às cargas a 5,17 GHz",13,True,TEAL)
    para(c,265,"Na R01, foram 75,99%. A R02 ganhou 0,344 dB no centro e 0,153 a 0,440 dB nos 17 pontos. A economia de coaxial em cada caminho responde por apenas 0,025 dB de atenuação de ida. O restante depende da distribuição em microstrip e do casamento entre os estágios.")
    para(c,183,"O primeiro estágio 1:2 convergiu em sete passes e o 1:5 em nove. Duas montagens matemáticas independentes reproduziram a matriz de 22 portas com diferença máxima de 7,1 × 10⁻¹⁵. As cargas são casadas nos planos terminais dos vinte cabos. A potência em cargas e a fase de saída descrevem a alimentação. O ganho frontal requer o campo radiado e a referência nos conectores N.")
    c.showPage()

    begin(c,3,count,"Montagem e custo das PCBs","Chapa, cabos e materiais   •   preços web da JLCPCB consultados em 06/11/2026")
    table(c,696,[156,66,89,91,101],["Trecho de UT-141C","Qtd. R02","R02 (mm)","Qtd. R01","R01 (mm)"],[
      ["Entrada N → primeira divisão","2","271,792","2","306,639"],["Primeira divisão → grupo","4","132,000","—","—"],
      ["Grupo → radiador","20","130,000","20","254,000"],["Total por percurso","","533,792","","560,639"]],9.5,24)
    para(c,552,"O conjunto usa 3,672 m de coaxial, ante 5,693 m na R01. Na geometria compacta estudada, o limite geométrico de ramal é 129,395 mm. A folga mínima medida entre capas foi 0,646 mm. Os 26 comprimentos são de eixo entre interfaces. Corrigir corte bruto e conferir atraso após soldar.")
    para(c,470,"O refletor dobrado de alumínio tem 2 mm. Há oito novos furos Ø 2,8 mm, seis trilhos traseiros e alojamentos no suporte inferior para liberar as cabeças dos parafusos. Os berços de poliacetal têm 5 mm. As bobinas de curto em CC das duas entradas têm duas espiras de fio de 0,30 mm, Ø médio 1,80 mm e passo 0,73 mm. Conferir continuidade e vedação no protótipo.")
    text(c,46,375,"Cotação para cinco conjuntos da R02",13,True,TEAL)
    table(c,359,[166,140,87,110],["Placa","Material e núcleo","Dimensões (mm)","Lote de 5"],[
      ["Dez radiadores","RO4350B / 0,76 mm","501,71 × 28,31","R$ 655,64"],
      ["Divisor inferior com 1:2","ZYF300CA-C / 1,52 mm","170,5 × 78","R$ 630,65"],
      ["Divisor superior","ZYF300CA-C / 1,52 mm","39 × 78","R$ 536,50"]],9,23)
    text(c,46,240,"R$ 1.822,79 por cinco conjuntos de três PCBs",14,True,TEAL)
    para(c,218,"Equivale a R$ 364,56 por conjunto, frente a R$ 238,43 na R01. A opção com 50 radiadores separados e os mesmos lotes de divisores soma R$ 1.868,68. Os valores cobrem as placas nuas, cobre de 1 oz e ENIG de 1 µin. Frete, tributos, mecânica, cabos e montagem são adicionais. O frete indicativo individual por DHL Express foi de R$ 221,61.")
    text(c,46,110,"Repositório do projeto e arquivos nativos",10.5,True)
    text(c,46,89,"github.com/Gecesars/emb_ant",10,True,TEAL)
    c.linkURL("https://github.com/Gecesars/emb_ant",(46,84,285,105))
    c.showPage()

    if cases["R01"] or cases["R02"]:
        begin(c,4,count,"Diagrama e ganho por frequência","Ganho realizado frontal em dBi   •   H e V a −3 dB em graus")
        data=[]
        for i,f in enumerate(range(5090,5251,10)):
            line=[br(f/1000)]
            for key in ("R01","R02"):
                rr=cases[key]
                line.extend([br(rr[i][v]) for v in ("ganho_frontal_dBi","H_graus","V_graus")] if rr else ["—"]*3)
            data.append(line)
        table(c,695,[63,89,65,67,89,65,65],["GHz","R01 ganho","R01 H","R01 V","R02 ganho","R02 H","R02 V"],data,9.7,23)
        text(c,46,247,"Referência dos números",12,True,TEAL)
        para(c,226,"As duas entradas N representam 1 W incidente total. O painel incorpora o espaçamento de 52,6 mm, o acoplamento entre os dez radiadores, as perdas e os caminhos dos coaxiais, soldas, curto em CC e estrutura. Cada corte tem passo angular de 0,25°. Os valores de banda referem-se às frequências calculadas.")
        para(c,140,"O interior dos conectores N, os polímeros mecânicos e as soldas usam propriedades nominais. Confirmar diagrama, potência refletida, continuidade e estanqueidade no protótipo físico.")
        c.showPage()
    if cases["R02-S"]:
        begin(c,count,count,"Uma placa ou dez radiadores","R02 e R02-S com a mesma rede de alimentação, refletor de 2 mm e comprimento dos cabos")
        data=[]
        for i,r in enumerate(cases["R02-S"]):
            ccont=cases["R02"][i] if cases["R02"] else None
            diff=br(float(r["ganho_frontal_dBi"])-float(ccont["ganho_frontal_dBi"])) if ccont else "—"
            data.append([br(float(r["MHz"])/1000),br(r["ganho_frontal_dBi"]),br(r["H_graus"]),br(r["V_graus"]),diff])
        table(c,695,[64,118,100,90,131],["GHz","R02-S ganho (dBi)","R02-S H (°)","R02-S V (°)","Δ ganho vs. R02 (dB)"],data,9.6,23)
        text(c,46,246,"Comparação montada no mesmo refletor",12,True,TEAL)
        para(c,226,"As dez PCBs quadradas têm 28,3125 mm de lado. O cobre, as soldas, o posicionamento, os divisores e os planos de referência são os mesmos da placa contínua. Na R02-S, duas guias de POM com alojamentos mantêm os radiadores nas coordenadas nominais. A comparação inclui o efeito desse apoio e da retirada de laminado entre os elementos.")
        c.showPage()
    c.save()


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf",type=Path)
    generate(parser.parse_args().pdf)
