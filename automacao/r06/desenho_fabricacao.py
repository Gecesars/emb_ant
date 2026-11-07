"""Pranchas R06 derivadas do perfil parametrizado e do chicote validado."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D

repo=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(repo/'freecad/mecanica_R01/fonte'))
import dimensoes as dim
old_bolts=dim.ref_bolts()
dim.ref_bolts=lambda:old_bolts+[(dim.PIN+c+o,y) for c in (-131.5,131.5) for o in (-21.5,21.5) for y in (-6.5,6.5)]
dim.MEIA_FACE=20
dim.LADO_FLAT=20+dim.BA+dim.PROF_NERV-dim.RO
import desenhos as draw
from formar_cabos import sample

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path)
root=parser.parse_args().root;out=root/'mecanica'
meta=json.loads((out/'rastreabilidade.json').read_text(encoding='utf8'))
inp,trunk,branch=meta['comprimentos_mm']
def num(x,n=3):return ('%.*f'%(n,x)).replace('.',',')

def page(number,title,subtitle):
    f=plt.figure(figsize=(420/25.4,297/25.4),facecolor='white')
    f.text(.045,.946,title,size=23,weight='bold')
    f.text(.045,.91,subtitle,size=10.5,color=draw.GREY)
    for y in [.887,.065]:
        f.add_artist(Line2D([.045,.955],[y,y],transform=f.transFigure,color=draw.TEAL,lw=.8))
    f.text(.045,.039,'P1H  /  MECÂNICA R06  /  07 NOV 2026  /  GEOMETRIA DE MONTAGEM — CONSULTAR RELATÓRIO RF',size=8.5,color=draw.TEAL)
    f.text(.955,.039,f'A3  /  mm  /  VISTAS SEM ESCALA  /  {number} DE 3',ha='right',size=8.5)
    return f

def sheet(pdf):
    f=page(1,'Refletor  /  corte e dobra','Alumínio 5052-H32 proposto • espessura 2,00 • raio interno 2,00 • K = 0,40 • abas para o verso (−Z)')
    a=draw.axes(f,[.035,.585,.93,.28],(-350,280),(-65,65))
    draw.poly(a,dim.contorno_plano())
    for x in dim.CENTROS:draw.poly(a,draw.outline(dim.slot(x,0,dim.R_PASSA,dim.PIN)),draw.PAPER)
    for x,y in dim.ref_bolts():draw.cir(a,x,y,1.4)
    for y in [-dim.N_Y,dim.N_Y]:draw.poly(a,draw.outline(dim.duplo_d(dim.N_FLAT,y)),draw.PAPER)
    for x0,x1 in dim.TRECHOS:
        for s in [-1,1]:draw.line(a,x0,s*(20+dim.BA/2),x1,s*(20+dim.BA/2),color=draw.RED,ls='--')
    draw.line(a,dim.BASE-dim.BA/2,-41,dim.BASE-dim.BA/2,41,color=draw.RED,ls='--')
    draw.dim(a,(dim.FIM_FLAT,41),(258,41),'585,398',(0,12))
    draw.dim(a,(dim.FIM_FLAT,-41),(dim.FIM_FLAT,41),'82,000',(-12,0))
    draw.title(f,.045,.55,'Seção da alma e das nervuras • vista YZ')
    b=draw.axes(f,[.045,.345,.31,.18],(-34,34),(-20,10))
    draw.rect(b,-20,-2,40,2)
    for s in [-1,1]:
        profile=[(0,0,-np.tan(np.pi/8)),(4,-4,0),(4,-8,0),(2,-8,0),(2,-4,np.tan(np.pi/8)),(0,-2,0)]
        draw.poly(b,[(s*(20+x),z) for x,z in draw.outline(profile)])
    draw.dim(b,(-20,0),(20,0),'40,00 • face plana',(0,6))
    draw.dim(b,(-24,-8),(24,-8),'48,00 • exterior',(0,-7))
    draw.title(f,.395,.55,'Base e furação')
    draw.notes(f,.395,.51,[
        'Altura externa dobrada 533,00. Aba inferior de 82,00 × 56,00.',
        'Dois N: centros Y = ±19,25 e Z = −31,00. Duplo D: Ø16,50 / planos 14,00.',
        'Dez rasgos 7,00 × 12,018; pontas R3,50. Centros X = −234,191 + n × 52,60.',
        'As 26 fixações de Ø2,80 preservam os apoios e as duas PCBs da R02.',
        'Rebarbar e manter plano o assento das juntas. Conferir K e raio com corpo de prova.'
    ],.032)
    draw.table(f,[.045,.105,.91,.20],['Operação','Localização / especificação','Arquivo de referência'],[
        ['Nervuras, 90°','Y = ±22,199 no plano; X = −248 a −28 e +32 a +258','05_Refletor_marcacao_dobras.dxf'],
        ['Base, 90°','X = −273,199 no plano; Y = −41 a +41','01_Refletor_dobrado.FCStd / .step'],
        ['Corte, escala 1:1','39 contornos fechados; unidades mm','04_Refletor_CORTE_1a1.dxf'],
        ['Planificação','Volume e área conferidos; diferença CAD/RF = 0','02_Refletor_planificado.FCStd']
    ],[.17,.48,.35],fs=9)
    pdf.savefig(f);plt.close(f)

def assembly(pdf):
    f=page(2,'Montagem  /  placa contínua e dois divisores','E01 junto aos conectores N; E10 no topo. Cada PCB distribuidora atende às duas polarizações de cinco elementos.')
    a=f.add_axes([.035,.085,.255,.79]);a.imshow(np.rot90(plt.imread(out/'traseira.png')));a.axis('off')
    draw.title(f,.32,.845,'Interfaces preservadas da montagem R02')
    draw.notes(f,.32,.805,[
        'PCB de radiadores: 501,7125 × 28,3125; RO4350B de 0,76 mm.',
        'Face inferior da PCB a Z = 16,61. Dez elementos com passo 52,60.',
        'Cinco berços POM-C de 5 mm e dois batentes. Não comprimir o laminado.',
        'Divisores: ZYF300CA-C de 1,52 mm; inferior 170,5 × 78, superior 39 × 78.',
        'Dois divisores 1:2 integrados na extensão da placa inferior, ao centro da antena.',
        'Alívios dos trilhos e do berço 2 seguem os STEPs da montagem R02.'
    ],.036)
    draw.title(f,.32,.555,'Chicote UT-141C • comprimentos ao eixo')
    draw.table(f,[.32,.36,.63,.16],['Trecho','Quantidade','Comprimento unitário'],[
        ['N até a primeira divisão','2',num(inp)+' mm'],
        ['Primeira divisão até o grupo','4',num(trunk)+' mm'],
        ['Divisor do grupo até o radiador','20',num(branch)+' mm']
    ],[.48,.18,.34],fs=10)
    draw.notes(f,.32,.315,[
        'Total de coaxial: '+num(meta['total_coax_mm'],0)+' mm. Cada caminho N–radiador: '+num(meta['percurso_por_radiador_mm'],0)+' mm.',
        'Curvas com raio ao eixo de 4,40. Folga mínima entre capas: '+num(meta['folga_minima_mm'])+' mm.',
        'Envelope dos cabos até Z = '+num(meta['envelope_zmin_mm'])+'. Conservar a posição dos lançamentos.',
        'Comprimentos entre interfaces do CAD: ajustar corte bruto por inserção e decapagem.',
        'Formar em gabarito e parear os atrasos elétricos depois da solda.',
        'Identificação e pontos 3D: chicote_26_cabos.csv, caminhos.json e enlaces.json.'
    ],.033)
    pdf.savefig(f);plt.close(f)

def coil(pdf):
    f=page(3,'Entradas  /  curto para corrente contínua','Duas entradas independentes. Uma bobina entre alma e blindagem de cada coaxial, junto à primeira divisão.')
    a=draw.axes(f,[.045,.405,.48,.43],(-1.1,5.5),(-5.4,1.0))
    # Corte axial XZ. Z=0 é o plano local da entrada do divisor.
    for s in [-1,1]:
        draw.rect(a,s*1.515 if s>0 else -1.7905,-5, .2755,5.4,'#a5b0b6')
    draw.rect(a,-.45975,-5,.9195,5.4,draw.CU)
    draw.rect(a,.45975,-5,1.05525,5.4,'#edf0ef')
    draw.rect(a,-1.515,-5,1.05525,5.4,'#edf0ef')
    draw.rect(a,.45975,-3.3,1.9,1.0,'white','white')
    draw.line(a,0,-2.8,2.2,-2.8,color=draw.CU,lw=4)
    t=np.linspace(0,4*np.pi,301)
    a.plot(2.2+.73*t/(2*np.pi),-1.9-.9*np.cos(t),color=draw.CU,lw=3)
    draw.line(a,3.66,-2.8,1.70,-4.3,color=draw.CU,lw=3)
    draw.dim(a,(2.2,-1),(3.66,-1),'1,46 axial',(0,.65))
    draw.dim(a,(3.66,-2.8),(3.66,-1),'Ø médio 1,80',(1.1,0))
    a.text(-.4,.7,'PCB / GND: plano local Z = 0',size=9)
    a.text(-1,-5.25,'Corte ilustrativo • esmalte não representado',size=8,color=draw.GREY)
    draw.title(f,.56,.83,'Dimensões e sequência')
    draw.notes(f,.56,.785,[
        'Fio de cobre Ø0,30; duas espiras; passo 0,73.',
        'Raio médio 0,90. Eixo da bobina paralelo a +X.',
        'Início do eixo helicoidal em X local = 2,20.',
        'Abertura radial Ø1,00, centro Z local = −2,80.',
        'Preservar blindagem e PTFE fora dessa abertura.',
        'Retorno à blindagem: X = 1,70; Z = −4,30.',
        'Desesmaltar apenas as pontas e soldar sem fechar a janela.',
        'As duas bobinas devem ter a mesma geometria.'
    ],.041)
    draw.table(f,[.045,.115,.91,.22],['Verificação','Critério / referência'],[
        ['Continuidade DC','Medir pino–carcaça em cada N; registrar resistência descontando as pontas de prova.'],
        ['Geometria de RF','A bobina foi calculada como cobre sem película de esmalte; qualificar o fio efetivamente comprado.'],
        ['Vedação dos N','Amphenol 082-6784: junta, arruela, porca e termorretrátil conforme desenho do fabricante.'],
        ['Montagem final','Conferir folgas, ausência de contato com reflector, soldas e atraso relativo de A/B.'],
        ['Liberação de RF','O resultado de cupom não aprova o painel; aplicar os critérios no plano das duas entradas N.']
    ],[.2,.8],fs=9.1)
    pdf.savefig(f);plt.close(f)

if __name__=='__main__':
    with PdfPages(out/'06_Desenho_de_fabricacao_R06.pdf') as pdf:
        for make in [sheet,assembly,coil]:make(pdf)
