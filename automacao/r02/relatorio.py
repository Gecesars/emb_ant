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
    text(c,419,802,"R01–R03     "+day,8.4,False,MUTED)
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
    cases={name:band(name) for name in ("R01","R02","R02-S","R03")}
    complete=all(cases.values())
    count=5+int(bool(cases["R01"] or cases["R02"]))+int(bool(cases["R02-S"]))+int(bool(cases["R03"]))
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
        else:
            folder="r02_separadas" if name=="R02-S" else name.lower()
            center=repo/"resultados"/folder/"metricas_Centro.csv"
            if center.exists():
                r=rows(center)[0]
                parcial="Reprova no centro" if "False" in (r["atende_H"],r["atende_ganho"]) else "Centro aprovado"
                data.append([name,br(r["ganho_frontal_dBi"])+" dBi (centro)",br(r["H_graus"])+"° (centro)",parcial])
            else:data.append([name,"Em qualificação","Em qualificação","Pendente"])
    text(c,46,689,"Ganho e cobertura com o painel montado",14,True,TEAL)
    table(c,674,[56,142,160,145],["Painel","Ganho frontal¹","Abertura horizontal¹","H e ganho na meta"],data,9.6,23)
    if complete:
        verdict="A tabela resume a aprovação conjunta de ganho e abertura horizontal por frequência. A página de dados identifica os pontos e as aberturas verticais."
    else:
        verdict="¹ O centro corresponde a 5,17 GHz. Quando há 17 pontos, a tabela mostra o menor ganho e a faixa de H. Um ponto fora do critério já reprova a exigência de atender toda a banda. A R01 apresentou 6,19° na vertical no centro."
    para(c,547,verdict)
    text(c,46,487,"O que mudou no chicote",14,True,TEAL)
    para(c,467,"Uma placa distribui A e B aos cinco elementos inferiores e outra atende os cinco superiores. Na R02 compacta, os vinte ramais têm 130 mm. Na R03 alongada, as saídas ficam sob os radiadores e cada ramal reto tem 26,61 mm. A R02-S usa dez PCBs individuais em guias de POM e a mesma alimentação da R02.")
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

    begin(c,4,count,"Divisores compactos ou alongados","Duas placas para os dez radiadores   •   entrada central de cada grupo e polarização")
    with Image.open(repo/"freecad/mecanica_R03/Verso_R03.png") as source:
        art=source.convert("RGB");bounds=ImageChops.difference(art,Image.new("RGB",art.size,"white")).getbbox()
        c.drawImage(ImageReader(art.crop(bounds)),46,614,503,90,preserveAspectRatio=True,mask="auto")
    text(c,46,595,"Verso da R03, com os dois conectores N na base à esquerda.",8.9,False,MUTED)
    table(c,575,[190,150,163],["Por painel ou caminho","R02 compacta","R03 alongada"],[
        ["Coaxial total","3,672 m (26 peças)","0,674 m (22 peças)"],
        ["Coaxial por N–radiador","533,792 mm","97,718 mm"],
        ["Microstrip por N–radiador","≈ 30,4 mm","≈ 494,2 mm"],
        ["Três PCBs por conjunto¹","R$ 364,56","R$ 403,00"]],9.5,23)
    text(c,46,442,"Perda prevista a 5,17 GHz com as vinte saídas em 50 Ω",13,True,TEAL)
    materialrows=rows(repo/"resultados/r03/comparacao_linhas.csv")
    nominal={(r["material"],r["geometria"]):br(r["perda_excedente_dB"],3) for r in materialrows if r["MHz"]=="5170"}
    table(c,426,[136,112,123,132],["PTFE de 1,52 mm","Dk / Df","Compacta (dB)","Alongada (dB)"],[
        [k,v,nominal[k,"compacta"],nominal[k,"alongada"]] for k,v in [
        ("ZYF300CA-C","2,94 / 0,0016"),("ZYF300CA-P","3,00 / 0,0018"),
        ("ZYF265D","2,65 / 0,0019"),("ZYF255DA","2,55 / 0,0018")]],9.5,22)
    para(c,299,"Cálculo nominal de linhas com perdas e junções ideais. Em ZYF300CA-C, o ensaio independente com as matrizes HFSS dos dois estágios compactos deu 0,849 dB. Na alongada, C e ZYF255DA ficam a 0,011 dB um do outro no modelo de linhas. A comparação física exige incluir as curvas, as emendas e os lançamentos. O banho de níquel do ENIG pode acrescentar perda.")
    para(c,194,"¹ A JLCPCB reconheceu as alongadas de 260,15 × 82 e 229,35 × 82 mm. Os lotes de cinco custaram R$ 688,85 e R$ 670,50. Com o radiador contínuo RO4350B de 0,76 mm, são R$ 2.014,99 para cinco conjuntos de três placas, antes de frete, tributos e montagem.")
    text(c,46,98,"Arquivos KiCad, FreeCAD, DXFs, dados e comprovantes",9.7,True,TEAL)
    c.linkURL("https://github.com/Gecesars/emb_ant/tree/main/resultados/r03",(46,92,420,111))
    c.showPage()

    begin(c,5,count,"Perda de linha nos quatro PTFE","Cupons HFSS de 20 e 120 mm   •   dezessete frequências e dois passes convergidos")
    tests=rows(repo/"resultados/r03/cupons_hfss.csv")
    adjusted=rows(repo/"resultados/r03/comparacao_com_cupons.csv")
    data=[]
    for material in ["ZYF300CA-C","ZYF300CA-P","ZYF265D","ZYF255DA"]:
        series=[r for r in tests if r["material"]==material]
        assert len(series)==17 and all(r["criterio_completo"]=="True" for r in series)
        alpha=[float(r["atenuacao_dB_m"]) for r in series]
        pred=next(r for r in adjusted if r["MHz"]=="5170" and r["material"]==material and r["geometria"]=="alongada")
        data.append([material,br(alpha[8],3),br(min(alpha),3)+"–"+br(max(alpha),3),br(pred["perda_excedente_dB"],3)])
    table(c,693,[137,122,130,114],["Laminado","5,17 GHz (dB/m)","Banda (dB/m)","R03 prevista (dB)"],data,9.4,24)
    text(c,46,541,"A linha ZYF255DA apresentou a menor perda nominal",13,True,TEAL)
    para(c,519,"A extração usa os autovalores da matriz de transferência formada por uma linha de 120 mm e a inversa de uma linha de 20 mm, com lançamentos iguais. A diferença é de 100 mm. A análise confere passividade, reciprocidade, as 17 frequências e a continuidade de fase. Cada modelo atingiu ΔS de até 0,003 em dois passes consecutivos.")
    para(c,413,"A última coluna aplica a propagação extraída apenas aos trechos de 50 Ω da R03. Os transformadores de impedância e as junções conservam o modelo por linhas. As curvas e emendas estão incluídas no modelo de rede física em qualificação. A perda do painel requer também bobinas, N, casamento dos radiadores e acoplamento.")
    text(c,46,306,"Premissas da comparação",13,True,TEAL)
    para(c,283,"Núcleo de 1,52 mm, cobre de 35 µm, rugosidade de 0,5 µm e Dk/Df constantes nos cupons. O ENIG da cotação inclui níquel sob o ouro. O modelo atual usa cobre finito e as perdas dielétricas nominais. A camada de níquel-fósforo, as tolerâncias do laminado e a execução das soldas acrescentam incerteza à fabricação.")
    para(c,175,"Os divisores alongados em ZYF300CA-C foram escolhidos como referência geométrica e de custo para o painel, antes do resultado dos cupons. O ganho e as aberturas finais continuam condicionados à solução convergida do conjunto montado.")
    c.showPage()

    if cases["R01"] or cases["R02"]:
        begin(c,6,count,"Diagrama e ganho por frequência","Ganho realizado frontal em dBi   •   H e V a −3 dB em graus")
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
        begin(c,count-int(bool(cases["R03"])),count,"Uma placa ou dez radiadores","R02 e R02-S com a mesma rede de alimentação, refletor de 2 mm e comprimento dos cabos")
        data=[]
        for i,r in enumerate(cases["R02-S"]):
            ccont=cases["R02"][i] if cases["R02"] else None
            diff=br(float(r["ganho_frontal_dBi"])-float(ccont["ganho_frontal_dBi"])) if ccont else "—"
            data.append([br(float(r["MHz"])/1000),br(r["ganho_frontal_dBi"]),br(r["H_graus"]),br(r["V_graus"]),diff])
        table(c,695,[64,118,100,90,131],["GHz","R02-S ganho (dBi)","R02-S H (°)","R02-S V (°)","Δ ganho vs. R02 (dB)"],data,9.6,23)
        text(c,46,246,"Comparação montada no mesmo refletor",12,True,TEAL)
        para(c,226,"As dez PCBs quadradas têm 28,3125 mm de lado. O cobre, as soldas, o posicionamento, os divisores e os planos de referência são os mesmos da placa contínua. Na R02-S, duas guias de POM com alojamentos mantêm os radiadores nas coordenadas nominais. A comparação inclui o efeito desse apoio e da retirada de laminado entre os elementos.")
        c.showPage()
    if cases["R03"]:
        begin(c,count,count,"Painel com divisores alongados","Cortes do painel completo R03, referidos às duas entradas N")
        table(c,695,[73,112,104,92,122],["GHz","Ganho (dBi)","H (°)","V (°)","H e ganho"],[
            [br(int(r["MHz"])/1000),br(r["ganho_frontal_dBi"]),br(r["H_graus"]),br(r["V_graus"]),
             "Atende" if r["atende_H"]==r["atende_ganho"]=="True" else "Reprova"] for r in cases["R03"]],9.7,23)
        c.showPage()
    c.save()


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf",type=Path)
    generate(parser.parse_args().pdf)
