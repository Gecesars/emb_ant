"""Relatorio tecnico R06 com dados rastreaveis e vistas CAD; PDF/A nao solicitado."""
import argparse,json
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak
from PIL import Image as PILImage

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);parser.add_argument('--rascunho',action='store_true');args=parser.parse_args()
root=args.root;repo=Path(__file__).resolve().parents[2];out=root/'relatorio';out.mkdir(exist_ok=True)
draft=args.rascunho
def load(path,default=None):return json.loads(path.read_text(encoding='utf8')) if path.exists() else default
data=load(root/'circuito/resultado.json',{})
result=data.get('corrigida',{})
conv=load(root/'antena/auditoria_convergencia.json',{})
native=load(root/'circuito/verificacao_nexxim.json',{})
divs=load(root/'circuito/divisores.json',{})
mesh_check=load(root/'circuito/comparacao_malhas.json',{})
fabrication=load(root/'fabricacao/verificacao.json',{})
config=load(root/'configuracao_circuito.json',{})
mechanics=load(root/'mecanica/rastreabilidade.json',{})
input_mm,trunk_mm,branch_mm=config.get('comprimentos_mm',[290,132,133])
def fmt(value,dec=2):return ('%.*f'%(dec,value)).replace('.',',')
if not draft:
    assert result.get('criterios_numericos_atendidos') and conv.get('convergencia_aprovada')
    assert native.get('matriz_s_independente_conferida') and len(divs)==2
    assert mesh_check.get('estabilidade_local_aprovada') and fabrication
    assert mesh_check.get('pasta_referencia')=='antena_estrita21'
    assert tuple(result['comprimentos_fisicos_mm'])==tuple(config['comprimentos_mm'])==tuple(mechanics['comprimentos_mm'])
pdfmetrics.registerFont(TTFont('Arial','C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Bold','C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold')
navy=colors.HexColor('#13374B');blue=colors.HexColor('#176E93');light=colors.HexColor('#EEF4F7');gray=colors.HexColor('#52606B')
width=178*mm
styles={
 'body':ParagraphStyle('body',fontName='Arial',fontSize=9.2,leading=13.3,spaceAfter=8,textColor=navy),
 'h1':ParagraphStyle('h1',fontName='Arial-Bold',fontSize=19,leading=23,spaceAfter=12,textColor=navy),
 'h2':ParagraphStyle('h2',fontName='Arial-Bold',fontSize=12,leading=16,spaceBefore=8,spaceAfter=7,textColor=blue),
 'caption':ParagraphStyle('caption',fontName='Arial',fontSize=8,leading=10.5,spaceAfter=8,textColor=gray),
 'cell':ParagraphStyle('cell',fontName='Arial',fontSize=8.4,leading=11,textColor=navy),
 'head':ParagraphStyle('head',fontName='Arial-Bold',fontSize=8.4,leading=11,textColor=colors.white),
}
story=[]
def p(text,style='body'):return Paragraph(text,styles[style])
def add(text,style='body'):story.append(p(text,style))
def page(title):
    if story:story.append(PageBreak())
    add(title,'h1')
def table(rows,widths):
    tt=Table([[p(str(c),'head' if i==0 else 'cell') for c in row] for i,row in enumerate(rows)],colWidths=[w*mm for w in widths],hAlign='LEFT')
    tt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),navy),('VALIGN',(0,0),(-1,-1),'TOP'),
      ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,light]),('LEFTPADDING',(0,0),(-1,-1),7),
      ('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    story.extend([tt,Spacer(1,8)])
def img(name,w=178,maxh=100):
    path=root/'imagens'/name
    if not path.exists():
        assert draft,path
        return p('Figura de resultados pendente: '+name,'caption')
    with PILImage.open(path) as im:iw,ih=im.size
    scale=min(w*mm/iw,maxh*mm/ih)
    return Image(str(path),width=iw*scale,height=ih*scale,hAlign='CENTER')
def fig(name,caption,w=178,maxh=100):story.extend([img(name,w,maxh),p(caption,'caption')])
def pair(a,b,captions,maxh=94):
    t=Table([[img(a,86,maxh),img(b,86,maxh)],[p(captions[0],'caption'),p(captions[1],'caption')]],colWidths=[89*mm,89*mm])
    t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),5)]));story.append(t)
def number(key,unit='',dec=2):
    v=result.get(key)
    return (('%.*f'%(dec,v)).replace('.',',')+' '+unit).strip() if v is not None else 'Pendente'
def vs(key):
    v=result.get(key);return ' / '.join(('%.3f'%x).replace('.',',') for x in v) if v else 'Pendente'

page('P1H R06 | Painel de dez elementos')
add('RELATÓRIO EM PREPARAÇÃO — RF AINDA NÃO QUALIFICADO' if draft else 'QUALIFICAÇÃO NUMÉRICA EM 5,17 GHz','h2')
add('PCB contínua de duas polarizações, divisores compactos em duas placas e montagem em refletor de alumínio. Revisão da análise conforme a orientação de 7 de novembro de 2026: antena e distribuidoras resolvidas separadamente no HFSS; cabos representados no circuito somente por fase.')
fig('montagem_frontal.png','Vista frontal da montagem FreeCAD. A direção longa X da geometria corresponde à vertical da antena instalada.',maxh=65)
table([['Métrica em 5,17 GHz','Resultado','Critério'],
 ['Ganho frontal realizado total',number('ganho_frontal_realizado_dBi','dBi'),'≥ 16 dBi'],
 ['Abertura horizontal a −3 dB',number('abertura_H_graus','°'),'81° a 99°'],
 ['Abertura vertical a −3 dB',number('abertura_V_graus','°'),'Feixe mais estreito permitido'],
 ['VSWR ativo A / B',vs('VSWR_ativo_AB'),'Cada entrada &lt; 1,5'],
 ['VSWR com outra entrada casada',vs('VSWR_outro_porto_casado_AB'),'Cada entrada &lt; 1,5']], [77,52,49])
add('<b>Condição de referência:</b> duas entradas de 0,5 W a 0°, 1 W total incidente, normalização em 50 Ω. O ganho inclui descasamento, perdas das PCBs e da bobina; a atenuação das linhas de cabo é zero. Os N são interfaces ideais no circuito.')
add('<b>Alcance:</b> o aceite solicitado é no centro da banda. A varredura dos divisores abrange 5,09–5,25 GHz. Um resultado da PCB em 5,17 GHz não qualifica o ganho nem o VSWR do painel nos outros pontos da banda.')
add('Entregas: projetos HFSS, Touchstone, circuito Nexxim, KiCad/Gerbers, montagem FreeCAD, chapa dobrada e planificada e desenhos A3. Repositório: <link href="https://github.com/Gecesars/emb_ant">github.com/Gecesars/emb_ant</link>.','caption')

page('Método e fronteiras da análise')
table([['Bloco','Representação','Incluído'],
 ['PCB da antena','HFSS completo, 20 portas','Dez radiadores, acoplamento mútuo, refletor, apoios e fixações frontais.'],
 ['Distribuidora inferior','HFSS completo, 18 portas','Duas divisões 1:2 e duas 1:5 no mesmo substrato.'],
 ['Distribuidora superior','HFSS completo, 12 portas','Duas divisões 1:5 no mesmo substrato.'],
 ['Interligações','Circuito de parâmetros S','Linhas recíprocas, casadas em 50 Ω, fase pelo comprimento elétrico; nenhuma atenuação.'],
 ['Curto em DC','Cupom HFSS de duas portas','Duas espiras de fio de cobre, janela na blindagem e terminais locais.']],[38,54,86])
add('A extração de cada distribuidora usa as outras portas terminadas em 50 Ω. No circuito final, essas cargas são substituídas pelas matrizes complexas das demais placas. O cálculo resolve as reflexões múltiplas e o acoplamento entre todas as portas; não soma apenas perdas em dB.')
add('Os vinte campos embutidos da PCB são recombinados coerentemente com as amplitudes e fases calculadas pelo circuito. Cada campo foi exportado com 1 W incidente em uma porta e as demais casadas. A recomposição uniforme é conferida contra o diagrama exportado diretamente pelo HFSS.')
table([['Percurso físico no CAD','Ajuste entre planos HFSS'],
 [f'Entrada: {input_mm:g} mm',f'Com bobina: {fmt(input_mm-8,0)} mm até o cupom e −4,18 mm de deslocamento da saída até o plano da distribuidora.'],
 [f'Quatro enlaces: {trunk_mm:g} mm',f'{fmt(trunk_mm-.36)} mm de linha ideal; os 0,18 mm de terminal em cada PCB já estão no HFSS.'],
 [f'Vinte ramais: {branch_mm:g} mm',f'{fmt(branch_mm-1.18)} mm de coaxial ideal + 0,965 mm de trecho em ar até a terminação da PCB.']],[63,115])
add('Velocidade de fase do coaxial: 1 / (50 × 95,2 pF/m). Comprimentos negativos representam deslocamento matemático de referência, não cabos físicos negativos. A entrada comum mantém a mesma fase entre polarizações.')
add('A análise separada não inclui radiação ou acoplamento direto dos trajetos de cabo com o painel, nem acoplamento eletromagnético entre as distribuidoras e a antena. Essa delimitação segue o método solicitado. A montagem 3D mantém os cabos para fabricação.','caption')

page('Circuito e distribuição de potência')
fig('circuito_funcional.png','Topologia funcional com os comprimentos físicos do chicote. Cada seta reúne caminhos independentes A/B.',maxh=151)
add('As funções 1:2 e 1:5 desenhadas dentro da placa inferior pertencem a uma única matriz S18 obtida da placa completa. A matriz conserva o acoplamento entre essas redes. O mesmo vale para as duas polarizações da distribuidora superior e para os vinte terminais da PCB contínua.')
add('As duas bobinas são blocos S2 separados. Os percursos físicos recebem a correção dos planos de referência indicada na página anterior. Todos os enlaces ideais têm |S21| = 1 e S11 = 0. O modelo de circuito é resolvido no Ansys Circuit/Nexxim e comparado à solução matricial independente.')
add('Na extração HFSS, portas não excitadas estão casadas. No circuito final, as interligações fecham essas portas nas cargas reais das outras matrizes; o VSWR final inclui as reflexões múltiplas. A separação em blocos não descarta o acoplamento já contido em cada matriz.','caption')

page('PCB contínua | RO4350B de 0,76 mm')
add('Uma única placa de 501,7125 × 28,3125 mm contém dez elementos, com passo de 52,6 mm. O substrato de 0,76 mm é preservado conforme o modelo aceito pelo usuário e a opção disponível na JLCPCB.')
fig('pcb_continua_superior.png','Face superior: redes locais de alimentação A/B. Cores usadas para distinguir materiais, sem indicar acabamento real.',maxh=56)
fig('pcb_continua_inferior.png','Face inferior: os dez radiadores e cruzamentos de alimentação. Vista espelhada pela observação do verso.',maxh=56)
pair('elemento_superior.png','elemento_inferior.png',['Detalhe de um elemento: face superior.','Detalhe de um elemento: face inferior.'],80)
table([['Parâmetro','Modelo'],['Dielétrico','RO4350B, 0,76 mm, εr de projeto 3,66; tanδ = 0,0037.'],['Metalização','Cobre físico de 35 µm; modelo de rugosidade equivalente de 0,5 µm.'],['Acabamento','ENIG unilateral nas superfícies expostas: Au 0,0254 µm; NiP 4,5 µm nominal.'],['Excitação local','20 portas de 50 Ω no plano de terminação; pino e solda locais, sem trajeto de cabo.']],[45,133])
add('A JLCPCB informa Dk de ensaio 3,48 no seletor; o modelo usa Dk de projeto 3,66. Não são substituídos silenciosamente. A espessura de 0,76 mm é do dielétrico: o configurador informa espessura acabada de 0,9 ± 0,1 mm.','caption')

page('Distribuidora inferior | 18 portas')
fig('divisor_inferior_superior.png','Face de sinal: dois divisores 1:5 à esquerda e duas primeiras divisões 1:2 à direita. A união de substrato mantém uma só PCB.',maxh=88)
fig('divisor_inferior_inferior.png','Verso de massa e ilhas isoladas dos terminais de sinal.',maxh=88)
table([['Característica','Especificação'],['Contorno','170,5 × 78 mm; geometria compacta R02 preservada.'],['Material','ZYF300CA-C, PTFE, 1,52 mm, εr = 2,94; tanδ = 0,0016.'],['Portas externas da análise','RA_IN/RA1/RA2, RB_IN/RB1/RB2 e A_IN/A1…A5, B_IN/B1…B5.'],['Conexão funcional','RA/RB dividem cada polarização entre metades inferior e superior. A1…A5 e B1…B5 atendem E01…E05.']],[47,131])
add('Toda a placa é resolvida de uma vez para preservar o acoplamento entre as redes presentes no mesmo substrato. As ligações físicas entre estágios são fechadas no circuito. Cobre de 35 µm e ENIG seguem as hipóteses declaradas para a revisão.','caption')

page('Distribuidora superior | 12 portas')
pair('divisor_superior_superior.png','divisor_superior_inferior.png',['Face de sinal: cinco saídas por polarização.','Face de massa e terminais isolados.'],138)
table([['Característica','Especificação'],['Contorno','39 × 78 mm.'],['Material','ZYF300CA-C, PTFE, 1,52 mm, εr = 2,94; tanδ = 0,0016.'],['Portas','A_IN/A1…A5 e B_IN/B1…B5, todas normalizadas em 50 Ω.'],['Conexão funcional','Recebe as saídas RA2/RB2 da placa inferior; distribui aos elementos E06…E10.']],[47,131])
add('Os terminais de solda e a pequena seção de acesso de 0,18 mm fazem parte do modelo local da PCB. Os percursos do chicote ficam fora do volume eletromagnético. A espessura acabada indicada pela JLCPCB para este dielétrico é 1,65 mm ±10%.')

page('Resultados e convergência')
fig('diagramas.png','Cortes H (φ = 90°) e V (φ = 0°), referidos à potência incidente nas duas entradas do circuito.',maxh=77)
fig('convergencia.png','Histórico adaptativo da PCB: ΔS e maior variação de ganho entre as nove direções do cache.',maxh=72)
hist=conv.get('historico',[])
last=hist[-1] if hist else {}
table([['Verificação','Evidência'],['Malha final da PCB',str(last.get('tetraedros','Pendente'))+' tetraedros; passe '+str(last.get('passe','—'))],
 ['Convergência de S','ΔS ≤ '+fmt(conv.get('criterio_s_usado',.004),3)+' em dois passes consecutivos.'],['Convergência de campo','Variação ≤ '+fmt(conv.get('criterio_campo_dB_usado',.02),2)+' dB em nove direções, em dois passes consecutivos.'],
 ['Circuito independente / Nexxim','Erro máximo em S: '+str(native.get('erro_absoluto_max','Pendente'))],
 ['Conservação de potência','Potência incidente = refletida + aceita na antena + perdas nos blocos. Linhas ideais dissipam zero.']],[60,118])
add('As nove direções de auditoria são θ = 0°, ±40°, ±50°, ±60° em φ = 90°, e θ = ±3° em φ = 0°. Encerrar por limite de passes não atende ao critério. A revisão de malha e as hipóteses são registradas com os resultados.','caption')

page('Conferência local da malha')
add('A primeira malha indicou um reparo de superfície no pequeno fragmento Ant08_Feed_A_Cu1, próximo à solda. O sólido CAD tem volume de 0,00794 mm³ e foi validado geometricamente. O aviso motivou uma verificação adicional, sem alterar a geometria nominal da PCB.')
add('O refinamento local usa desvio superficial de 0,0005 mm / 5° no cobre e nas soldas e comprimento de 0,06 mm nos fragmentos. Convergiu em 11 passes, mas H mudou 0,830°. A continuação com ΔS ≤ 0,004 e campo ≤ 0,02 dB convergiu em 21 passes; H mudou mais 1,569°. A conferência adicional com crescimento de 15% falhou por falta de memória. A retomada usa crescimento de 5% por passe, mantendo geometria, critérios de erro e tolerâncias de estabilidade. A tabela compara os 21 passes com a verificação final.')
rows=[['Comparação em 5,17 GHz','Estrita, 21 passes','Verificação final']]
for key,label,unit in [('ganho_frontal_realizado_dBi','Ganho com rede','dBi'),('abertura_H_graus','Abertura horizontal','°'),('abertura_V_graus','Abertura vertical','°')]:
    row=[label]
    for stage in ['inicial','refinada']:
        value=mesh_check.get(stage,{}).get(key)
        row.append(('%.4f %s'%(value,unit)).replace('.',',') if value is not None else 'Pendente')
    rows.append(row)
for i,pol in enumerate('AB'):
    rows.append(['VSWR ativo '+pol]+[('%.4f'%mesh_check[stage]['VSWR_ativo_AB'][i]).replace('.',',') if stage in mesh_check else 'Pendente' for stage in ['inicial','refinada']])
table(rows,[78,50,50])
add('A comparação usa exatamente os mesmos divisores, bobinas e linhas ideais. Assim, a diferença decorre da discretização da PCB. Limites desta conferência: 0,05 dB em ganho, 0,5° na horizontal, 0,1° na vertical e 0,05 em VSWR. A análise final também exige ausência de reparos classificados como Major.')
add('O arquivo g3derr agrega avisos de várias execuções. O Major do corpo 4550 tem TimeStamp de 16:49:21, da malha inicial. O filtro auditável usa o início do refinamento, 18:36:29 de 7/11, e preserva as contagens históricas. A superfície refinada de 18:38:17 tem dois corpos Minor e nenhum Major.','caption')
table([['Controle','Evidência'],['Reparos Major na malha final',str(mesh_check.get('reparo_major_final','Pendente'))],
 ['Variação de S nos dois passes finais',' / '.join('%.7f'%r['delta_s'] for r in hist[-2:]) if hist else 'Pendente'],
 ['Variação máxima de campo nos dois passes finais',' / '.join('%.6f dB'%r['delta_campo_max_dB'] for r in hist[-2:]) if hist else 'Pendente'],
 ['Circuito Nexxim','Matriz de duas portas comparada ao cálculo matricial independente.'],
 ['Recomposição dos campos','Alimentação uniforme recomposta comparada ao diagrama exportado diretamente pelo HFSS, tolerância de 0,005 dB.']],[72,106])
add('Os arquivos de evidência preservam os dois resultados, a identificação dos avisos de malha e os parâmetros S. Triângulos, tetraedros e campos volumétricos não acompanham o repositório.','caption')

page('Perdas e casamento da rede')
fig('perdas_divisores.png','Potência entregue às saídas previstas, com excitação uniforme das duas polarizações e demais portas casadas.',maxh=83)
table([['Grandeza do circuito em 5,17 GHz','Valor'],['Potência incidente','1 W'],['Potência refletida',number('refletida_W','W',6)],['Potência aceita pela antena',number('aceita_antena_W','W',6)],['Dispersão de amplitude nas 20 portas',number('excitacoes_antena_amplitude_pp_dB','dB',3)],['Dispersão de fase nas 20 portas',number('excitacoes_antena_fase_pp_graus','°',3)],['VSWR ativo A / B',vs('VSWR_ativo_AB')],['VSWR com outra entrada casada',vs('VSWR_outro_porto_casado_AB')]],[112,66])
add('O VSWR ativo usa a reflexão resultante das duas entradas simultâneas, ambas de 0,5 W a 0°. O VSWR convencional é calculado com a outra entrada casada. As duas grandezas são apresentadas para evitar que a interação entre polarizações fique oculta.')
add('A bobina foi caracterizada em um cupom de 12 mm. A versão principal remove a atenuação de dois acessos iguais usando o cupom reto de controle, preservando a fase. No centro, a correção é de aproximadamente 0,01279 dB. A matriz corrigida é verificada quanto à passividade. O caso bruto, com a pequena perda desses acessos, também é mantido como comparação.')
rows=[['Bobina no circuito','Ganho frontal','VSWR ativo A / B']]
for tag,label in [('corrigida','Acessos sem atenuação'),('bruta','Cupom bruto'),('sem','Sem bobina')]:
    r=data.get(tag,{})
    rows.append([label,('%.3f dBi'%r['ganho_frontal_realizado_dBi']) if r else 'Pendente',
      ' / '.join('%.3f'%v for v in r['VSWR_ativo_AB']) if r else 'Pendente'])
table(rows,[71,47,60])

page('Montagem e chicote')
fig('montagem_frontal.png','Vista frontal: PCB contínua, cinco berços, dois batentes e refletor.',maxh=66)
fig('montagem_traseira.png','Vista traseira: duas distribuidoras, dois N fêmea na base e 26 segmentos de cabo.',maxh=79)
table([['Grupo','Quantidade','Comprimento ao eixo'],
 ['Entrada N → distribuição central','2',f'{input_mm:g} mm'],
 ['Divisão central → redes 1:5','4',f'{trunk_mm:g} mm'],
 ['Distribuidoras → radiadores','20',f'{branch_mm:g} mm'],
 ['Total de coaxial no CAD','26',fmt(mechanics.get('total_coax_mm',2*input_mm+4*trunk_mm+20*branch_mm),0)+' mm'],
 ['Percurso por radiador','10 por polarização',fmt(input_mm+trunk_mm+branch_mm,0)+' mm']],[87,35,56])
add('Os comprimentos da tabela são entre interfaces geométricas e não comprimentos brutos de corte. Compensar as inserções e decapagens da junta soldada na preparação do chicote. Os percursos equivalentes são mantidos iguais para preservar fase.')
add(f"A revisão mecânica registra folga mínima de {fmt(mechanics.get('folga_minima_mm',.761075489),5)} mm entre capas e ausência de interseções volumétricas dos cabos. O envelope traseiro atinge Z = {fmt(mechanics.get('envelope_zmin_mm',-51.663580469),5)} mm, obtido do CAD sem depender da triangulação de visualização. As curvas usam raio de 4,4 mm ao eixo.",'caption')
add('O ajuste dos vinte ramais de 135 para 133 mm preserva a igualdade dos caminhos. Com a primeira malha da PCB, o comprimento anterior produziu VSWR convencional de 1,531 na entrada B. A seleção usa as reflexões múltiplas do circuito; não altera as trilhas, os Gerbers nem a chapa. O aceite deste relatório usa a malha refinada e os comprimentos atualizados.','caption')

page('Apoios, passagem de cabos e fixações')
pair('suporte_pom_5mm.png','apoio_passagem.png',['Berço de poliacetal de 5 mm sustentando a PCB.','Passagens pelo refletor com proteção local.'],100)
fig('fixacao_divisor.png','Fixação traseira da distribuidora superior e soldagem dos cabos. O substrato e o plano de massa permanecem afastados do refletor.',maxh=98)
add('O apoio frontal posiciona a face inferior do dielétrico em Z = 16,61 mm. Cinco berços de 5 mm e dois batentes de extremidade sustentam a coluna contínua. A chapa mantém dez rasgos de passagem dos pares de alimentação.')
add('Preservar os alívios mecânicos, o acesso de soldagem e os isolantes indicados no conjunto. As vistas são do CAD de montagem; dimensões de corte e dobra constam dos arquivos e pranchas específicos.','caption')

page('Base, conectores e curto em DC')
pair('base_conectores.png','bobina_dc.png',['Base dobrada com dois conectores N fêmea e juntas.','Cupom da bobina de curto: janela radial na capa, fio e ligação à massa.'],114)
table([['Item','Definição'],['Base','Parte inferior do refletor dobrada; 82 × 56 mm no envelope definido.'],['Conectores','Duas entradas N fêmea, uma por polarização; juntas e alívio local no CAD.'],['Bobina','Duas espiras, raio médio 0,90 mm, fio de cobre Ø0,30 mm, passo 0,73 mm.'],['Acesso ao sinal','Janela radial Ø1 mm; preservar o restante da blindagem coaxial.'],['Inspeção de montagem','Conferir continuidade DC pino–carcaça nos dois N e ausência de curto indevido nas trilhas.']],[50,128])
add('A simulação da bobina usa cobre condutor. O estudo auxiliar de esmalte de 20 µm é uma hipótese de sensibilidade, com efeito calculado inferior a 0,0024 dB na rede anterior; não identifica a composição do fio comercial.')
add('O modelo de conector N obtido no Drive é referência mecânica de um sólido único, sem contato e isolante separados. Não demonstra equivalência RF ao conector de compra. Nesta qualificação, o N é uma interface ideal, sem perda. A vedação desenhada não equivale a ensaio de grau IP.','caption')

page('Refletor de alumínio de 2 mm')
fig('refletor_dobrado.png','Chapa no formato final, com base de conectores, dobras laterais e passagens.',maxh=69)
fig('refletor_planificado.png','Planificação para corte: contorno, furos, rasgos e recortes dos conectores.',maxh=69)
table([['Parâmetro','Valor / entrega'],['Material e espessura','Alumínio 5052 nominal, 2 mm.'],['Face plana do refletor','40 mm.'],['Dobra','Raio interno 2 mm; fator K = 0,4.'],['Contornos DXF','39: externo + 26 fixações + dez rasgos + dois recortes dos N.'],['Nativos','01_Refletor_dobrado.FCStd e 02_Refletor_planificado.FCStd.'],['Fabricação','04_Refletor_CORTE_1a1.dxf, 05_Refletor_marcacao_dobras.dxf e PDF A3 com três pranchas.']],[48,130])
add('A geometria dobrada foi comparada com o refletor do modelo, com diferença simétrica de volume nula. O fator K e o raio devem acompanhar o ferramental de dobra da oficina. O DXF de corte é em milímetros e escala 1:1.','caption')

page('Fabricação e cotação JLCPCB')
add('Cotação instantânea atualizada em 7 de novembro de 2026 pela extensão do Chrome. Os três Gerbers foram enviados e suas dimensões reconhecidas. Cada preço corresponde a cinco PCBs nuas; não houve compra.')
table([['Placa / lote de 5','Material / dielétrico','Web Price'],['Contínua de dez elementos','RO4350B / 0,76 mm','R$ 657,83'],['Distribuidora inferior','ZYF300CA-C / 1,52 mm','R$ 632,75'],['Distribuidora superior','ZYF300CA-C / 1,52 mm','R$ 538,28'],['Cinco conjuntos de três PCBs','Total de fabricação','R$ 1.828,86']],[70,70,38])
add('Equivalente a R$ 365,77 em PCBs por conjunto. Duas camadas, cobre externo de 1 oz e ENIG de 1 µin. Fabricação indicada de 4–5 dias; frete exibido por cotação: DHL Express R$ 223,08, com trânsito de 4–6 dias úteis. O frete consolidado e os tributos não estão incluídos no total.')
q=root/'cotacao/continua.jpg'
if q.exists():
    with PILImage.open(q) as im:iw,ih=im.size
    story.append(Image(str(q),width=width,height=width*ih/iw))
    add('Evidência da coluna contínua: material, espessura e preço. As capturas dos dois divisores acompanham o pacote.','caption')
add('Arquivos de fabricação preservados: Gerber_P1H_Coluna_10.zip, Gerber_R02_Inferior.zip e Gerber_R02_Superior.zip. Seus hashes SHA-256 são registrados com a cotação. As cores dos renders CAD são didáticas; o acabamento contratado é definido pelos Gerbers e pelas opções de fabricação.')
add('DRC repetido no KiCad 10.0.5 em 7/11: zero erros e zero itens desconectados nas três placas. A coluna apresenta 203 avisos de ponte de máscara devido às aberturas amplas sobre os radiadores RF; os divisores não apresentam avisos. Os avisos foram preservados no relatório DRC, sem alterar os Gerbers.','caption')

page('Rastreabilidade e reprodução')
table([['Conteúdo','Local no repositório / pacote'],['PCBs editáveis','kicad/P1H_Coluna_10, kicad/R02_Inferior e kicad/R02_Superior.'],['Gerbers','fabricacao/gerbers; mesmos pacotes da revisão R02, hashes conferidos.'],['Mecânica','freecad/mecanica_R06: montagem, chapa, planificação, desenhos, listas do chicote e verificações. R05 permanece como histórico.'],['Simulação separada R06','hfss/antenas e hfss/alimentacao: nativos e fontes correspondentes, sem malhas no Git.'],['Circuito e evidências R06','resultados/r06: matrizes S, cortes, convergência, comparações e cotação.'],['Reprodução','automacao/r06: CAD separado, setup, extração de campos, circuito, auditoria, gráficos e relatório.']],[49,129])
add('<b>Materiais:</b> RO4350B e ZYF300CA-C seguem os valores nominais declarados. O NiP usa 4,5 µm e 1,5 MS/m como hipótese nominal; ouro de 1 µin. POM e aço têm propriedades nominais, não certificados de lote. A relação entre o modelo e o stackup deve permanecer registrada na fabricação.')
add('<b>Validação numérica:</b> convergência de S e campos, passividade/reciprocidade das matrizes, recomposição coerente dos campos, balanço de potência e comparação com Nexxim. Resultados da malha intermediária e tentativas descartadas não são usados para o aceite.')
add('<b>Validação física ainda distinta:</b> a qualificação no centro da banda não substitui medição de ganho e diagrama, VSWR do conjunto real, inspeção da bobina nem ensaio de vedação. As perdas reais dos cabos foram excluídas por orientação do usuário.')
add('O cálculo integral anterior com cabos foi encerrado após a mudança de método. Seus resultados incompletos não são empregados como prova de desempenho desta revisão. A documentação anterior permanece como histórico, identificada pela revisão.','caption')

filename=out/('P1H_R06_RASCUNHO.pdf' if draft else 'P1H_R06_Relatorio.pdf')
def decor(canvas,doc):
    canvas.saveState();canvas.setFillColor(navy);canvas.rect(16*mm,A4[1]-14*mm,width,1.2*mm,fill=1,stroke=0)
    canvas.setFont('Arial',7.5);canvas.setFillColor(gray)
    canvas.drawString(16*mm,11*mm,'P1H R06 · '+('Rascunho — aguardando RF' if draft else 'Qualificação numérica · 5,17 GHz'))
    canvas.drawRightString(A4[0]-16*mm,11*mm,str(doc.page));canvas.restoreState()
doc=SimpleDocTemplate(str(filename),pagesize=A4,rightMargin=16*mm,leftMargin=16*mm,topMargin=20*mm,bottomMargin=20*mm,
    title='P1H R06 — PCB contínua, divisores e montagem',author='Projeto P1H',subject='Simulação separada das PCBs e circuito sem perda de cabos')
doc.build(story,onFirstPage=decor,onLaterPages=decor)
print(filename)
