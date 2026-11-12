"""Relatorio nominal R11: exige exportacao/auditoria, nunca substitui resultado RF."""
from pathlib import Path
import os,json,hashlib,datetime
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

ROOT=Path(os.environ['P2S13_ROOT']);BASE=ROOT.parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=read(ROOT/'resultado.json');cfg=read(ROOT/'configuracao.json')
assert read(ROOT/'qualificacao.json')['estado']=='SOLVE_EXPORTADO_AGUARDA_AUDITORIA'
assert r['fontes_sha256']['centro.s2p']==sha(ROOT/'centro.s2p')
div=Path(cfg['fonte_divisor']);dfm=read(div/'kicad/verificacao.json')
cadcheck=read(div/'kicad/conferencia_cad_hfss.json')
hist=read(ROOT/'historico_passes.json');pwr=read(ROOT/'potencia_conferida.json') if (ROOT/'potencia_conferida.json').exists() else None
pdfmetrics.registerFont(TTFont('Arial','C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialB','C:/Windows/Fonts/arialbd.ttf'))
out=ROOT/'Relatorio_R11_C08_Radome.pdf'
W,H=A4;M=38;CW=W-2*M
c=canvas.Canvas(str(out),pagesize=A4)
c.setTitle('P2S13 R11 — C08 fabricavel e radome FR-4 de 2 mm')
c.setAuthor('Engenharia — estudo HFSS nominal')
normal=ParagraphStyle('p',fontName='Arial',fontSize=9.4,leading=13.5,textColor=colors.HexColor('#243746'),spaceAfter=7)
small=ParagraphStyle('s',parent=normal,fontSize=8.2,leading=11.4)
page=0;y=0
def start(title):
    global y,page
    if page:c.showPage()
    page+=1
    c.setFillColor(colors.HexColor('#123b51'));c.rect(0,H-82,W,82,fill=1,stroke=0)
    c.setFillColor(colors.white);c.setFont('ArialB',17);c.drawString(M,H-37,title)
    c.setFont('Arial',9);c.drawString(M,H-58,'P2S13 • R11 • 5,17 GHz • duas entradas 0,5 W / 0°')
    c.setFillColor(colors.HexColor('#546574'));c.setFont('Arial',8)
    c.drawString(M,22,'Simulação nominal — '+('metas atendidas' if r['validacao_nominal'] else 'não qualificado para liberação RF'))
    c.drawRightString(W-M,22,str(page));y=H-101
def para(t,style=normal):
    global y
    p=Paragraph(t,style);_,hh=p.wrap(CW,650)
    assert y-hh>40,('Pagina excedida',page,t[:90],y,hh)
    p.drawOn(c,M,y-hh);y-=hh+8
def table(rows,widths=None):
    global y
    cells=[[Paragraph(escape(str(v)),small) for v in row] for row in rows]
    t=Table(cells,colWidths=widths or [CW/len(rows[0])]*len(rows[0]),hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5eef2')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#cad5dc'))]))
    _,hh=t.wrap(CW,650);assert y-hh>40,('Tabela excedida',page,y,hh);t.drawOn(c,M,y-hh);y-=hh+12
def picture(path,maxh,caption):
    global y
    im=ImageReader(str(path));iw,ih=im.getSize();scale=min(CW/iw,maxh/ih)
    ww,hh=iw*scale,ih*scale;assert y-hh>65
    c.drawImage(im,M+(CW-ww)/2,y-hh,ww,hh,mask='auto');y-=hh+4;para(caption,small)
def num(x,n=3):return f'{x:.{n}f}'.replace('.',',')
def ok(v):return 'Atende' if v else 'Não atende'

start('Resultado do conjunto completo')
para('<b>'+('METAS NOMINAIS ATENDIDAS' if r['validacao_nominal'] else 'ESTUDO NÃO QUALIFICADO')+'</b> — antena de seis níveis, três PCBs idênticas de dois elementos, divisor duplo 1:3 corrigido, seis cabos físicos de 50 mm e radome FR-4 de 2 mm.')
if not r['resultados_fisicamente_consistentes']:
    para('<font color="#a52020"><b>SOLUÇÃO NUMERICAMENTE INVÁLIDA.</b> Os números e diagramas abaixo são exportações para diagnóstico, sem validade como previsão física. O solver matricial falhou e o balanço de potência foi reprovado.</font>')
table([
 ['Grandeza','Resultado','Critério'],
 ['Ganho frontal realizado total',num(r['cortes']['H']['ganho_frontal_dBi'])+' dBi','≥12 dBi — '+(ok(r['metas']['ganho']) if r['resultados_fisicamente_consistentes'] else 'não validado')],
 ['VSWR ativo A / B',' / '.join(num(x) for x in r['VSWR_ativo']),'≤1,25 — '+ok(r['metas']['VSWR_ativo'])],
 ['VSWR outra entrada em 50 Ω',' / '.join(num(x) for x in r['VSWR_outra_casada']),'Verificação adicional'],
 ['Abertura H / V',' / '.join(num(r['cortes'][k]['abertura_graus'],2)+'°' for k in 'HV'),'Largura a −3 dB'],
 ['Máximo V / assimetria',num(r['vertical_fino']['pico_interpolado_graus'],4)+'° / '+num(r['vertical_fino']['assimetria_max_dB'])+' dB','±0,5° / ≤0,2 dB'],
 ['Passes / ΔS',str(r['passes'])+' / '+num(r['delta_s'],6),'Máximo 6 / ≤0,05 × 2']
 ],[CW*.36,CW*.34,CW*.30])
para('Convergência: <b>'+('atendida' if r['convergiu'] else 'não atendida')+'</b>. O limite de passes é respeitado; encerrar no limite não comprova convergência. Ganho é normalizado a 1 W incidente total, com as duas entradas simultaneamente em fase.')
picture(ROOT/'imagens/montagem.png',160,'Vista do CAD físico usado na montagem. Radome oculto para mostrar as três PCBs, o refletor e as conexões.')

start('Divisor corrigido para fabricação')
para('A C07 histórica foi preservada. A revisão C08 usa as mesmas rotas de sinal e corrige a tecnologia dos furos e a distância do cobre à borda. A alteração exige nova avaliação RF, pois muda a capacitância das transições.')
picture(div/'kicad/preview/gerbers_conferidos.png',265,'Vista dos Gerbers conferidos contra o KiCad e as faces de cobre do CAD enviado ao HFSS.')
table([
 ['Característica','C08'],['Placa / dielétrico','220 × 64 mm; ZYF300CA-C 1,52 mm'],
 ['Cobre / acabamento','35 µm; ENIG nominal Au 0,0254 µm / NiP 4,5 µm'],
 ['Oito furos metalizados','Ø acabado 1,10 mm; metalização nominal 18 µm'],
 ['Ilhas / anel / antipads','Ø1,80 mm / 0,35 mm / Ø3,03 mm'],
 ['Terra / máscara','Recuo 0,30 mm; máscara totalmente aberta'],
 ['DRC',f"{dfm['DRC_erros']} erros; {dfm['DRC_desconectados']} desconectados; {dfm['DRC_avisos']} avisos de máscara aberta"],
 ['Conferência CAM','KiCad, Gerber, Excellon e faces CAD conferidos; oito PTH, zero NPTH']
 ],[CW*.36,CW*.64])
para('Os 5 nm usados na comparação numérica de contornos são tolerância de discretização dos arquivos; não são precisão de fabricação. Esta entrega não inclui compra nem liberação RF de uma placa reprovada. Capacidades JLCPCB consultadas em 11/11/2026.',small)

start('Montagem e radome de referência')
picture(ROOT/'imagens/radome.png',220,'Envelope de 314 × 84 × 84 mm; parede uniforme de 2 mm. Vista técnica a partir do CAD.')
picture(ROOT/'imagens/traseira.png',180,'Vista traseira: divisor duplo, cabos de 50 mm e contatos das três placas radiantes.')
para('<b>FR-4 Isola 370HR sem cobre:</b> εr=3,92 e tanδ=0,025, valores típicos da ficha a 5 GHz aplicados em 5,17 GHz. Modelo homogêneo/isotrópico. Folga frontal aproximada de 19,2 mm; lateral de 15 mm às PCBs e 7,5 mm ao envelope do refletor.')
para('Antenas em RO4350B 0,76 mm, εr=3,66 e tanδ=0,0037. Divisor em ZYF300CA-C 1,52 mm, εr=2,94 e tanδ=0,0016. Cobre, ENIG, solda SAC305, PTFE dos cabos e alumínio do refletor estão no modelo físico.')
para('Fonte do FR-4: <link href="https://isola-group.com/wp-content/uploads/data-sheets/370hr.pdf" color="#135783">ficha Isola 370HR</link>. O grau é uma referência autorizada, não certificação de lote nem alegação de estoque na JLCPCB.',small)

start('Diagramas e simetria vertical')
picture(ROOT/'polar_HV.png',310,'Diagramas normalizados em E/Emax, ambos com as duas entradas de 0,5 W / 0°. A normalização angular não altera o ganho absoluto da página 1.')
picture(ROOT/'simetria_vertical.png',240,'Comparação V(θ) e V(−θ). Grade fina de 0,01° e interpolação parabólica local do máximo.')
para('Máximos dos cortes H / V: '+num(r['cortes']['H']['pico_graus'],2)+'° / '+num(r['vertical_fino']['pico_interpolado_graus'],4)+'°. A assimetria é medida no intervalo de meia potência comum em torno de 0°. O limite de 0,2 dB é um critério de auditoria de engenharia; a tolerância angular ±0,5° foi aceita anteriormente pelo usuário.',small)

start('Convergência, auditoria e limites')
table([['Passe','Tetraedros','ΔS']]+[[q['passe'],f"{q['tetraedros']:,}".replace(',','.'),'—' if q['delta_s'] is None else num(q['delta_s'],6)] for q in hist],[CW*.2,CW*.4,CW*.4])
para('HFSS 2024 R2, 14 núcleos em todos os passes, Classic automático, base de ordem 2, residual iterativo configurado em 0,00001, sem operações locais de malha ou varredura. Últimas variações máximas das nove sondas de campo: '+', '.join('sem dado' if x is None else num(x,5)+' dB' for x in r['estabilidade_campos_ultimos_dB'])+'.')
for warning in r['solver_matricial']['avisos']:
    para('<b>Falha matricial no passe '+str(warning['passe'])+':</b> atingiu o limite interno de iterações sem convergir. Residual máximo '+num(warning['residuo_maximo'],5)+' e médio '+num(warning['residuo_medio'],5)+'. Este residual é distinto do ΔS entre passes.',small)
table([
 ['Auditoria','Resultado'],['Reparos Major / Minor',str(r['malha_major'])+' / '+str(r['malha_minor'])],
 ['Passividade σmáx / reciprocidade',num(r['passividade_sigma_max'],6)+' / '+f"{r['reciprocidade_erro']:.3e}"],
 ['Recomposição de campos H / V',' / '.join(f'{x:.3e}' for x in r['recomposicao_erro'].values())],
 ['Balanço de potência', 'Confere' if r['potencia_balanco_aprovado'] else 'Reprovado — potência radiada não física'],
 ],[CW*.47,CW*.53])
if pwr:
    b=pwr['balanco_S'];para('Potências: incidente 1 W; refletida '+num(b['refletida_W'],5)+' W; aceita '+num(b['aceita_W'],5)+' W; radiada '+num(b['radiada_W'],5)+' W; dissipada '+num(b['dissipada_W'],5)+' W.')
para('<b>Escopo:</b> inclui as perdas nos seis cabos e nos materiais, a radiação direta do divisor e seu acoplamento espacial. A C07 anterior combinava S8 e S6 e não somava a radiação do divisor; não se deve atribuir toda diferença de ganho apenas ao radome.')
para('<b>Limites:</b> somente um ponto de frequência, materiais nominais, duas referências de porta ideais internas. Não caracteriza conectores N externos, perfurações de passagem, vedações, adesivos, juntas, suportes, tolerâncias de lote, ambiente climático ou medições de protótipo. Os arquivos Gerber desta revisão são do divisor; não substituem os Gerbers das placas radiantes históricas.')
para('Os nativos, S2, campos distantes, verificações e configurações identificam a solução. Malhas e campos volumétricos ficam locais. O nativo sem a pasta de resultados não restaura a solução volumétrica.',small)
c.save()
manifest={'arquivo':str(out),'sha256':sha(out),'paginas':page,'resultado_sha256':sha(ROOT/'resultado.json'),'revisao_visual':'PENDENTE','gerado':datetime.datetime.now().isoformat()}
(ROOT/'relatorio_manifesto.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps(manifest,indent=2,ensure_ascii=False))
