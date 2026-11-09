"""Planejamento geometrico de quatro elementos verticais; nao executa HFSS.

Dois divisores 1:4, cada um feito por uma raiz 1:2 e duas etapas locais 1:2.
O cobre local parte da v05. Portas coaxiais intermediarias sao removidas.
"""
from pathlib import Path
import json, hashlib, math
import numpy as np
from shapely.geometry import shape, Polygon, Point, LineString, mapping
from shapely.affinity import translate
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath

REPO=Path(__file__).resolve().parents[3]
SRC=REPO/'projetos/P2M21/dois_verticais_divisor/variantes/v05_B_longo_inferior_15/geometria.json'
OUT=REPO/'projetos/P2M21/planejamento/4_elementos'
OUT.mkdir(parents=True,exist_ok=True)
g=json.loads(SRC.read_text(encoding='utf-8'))
lands=[];vias=[];roots=[];branches=[]
for module,dx in enumerate([-48.,48.]):
    for l in g['lands']:
        p=shape(l['geometry']);net=l['net']
        if net.startswith('E'):
            index=int(net[1:net.index('_')])+2*module
            net='E'+str(index)+net[net.index('_'):]
        if l['layer']=='B':
            for ip in g['inputs']:
                region=Point(ip['x'],ip['y']).buffer(1.516,quad_segs=96)
                if net==ip['sig']:
                    p=p.difference(region)  # remove pad B.Cu do antigo coax
                if net==ip['ret']:
                    p=p.union(region)       # retorno continuo sob a nova juncao
        if not p.is_empty:lands.append(dict(layer=l['layer'],net=net,shape=translate(p,dx,0)))
    vias.extend([[x+dx,y] for x,y in g['vias']])
    for tr in g['traces']:
        branches.append(dict(polarizacao=tr['polarizacao'],elemento=tr['elemento']+2*module,
            comprimento_local_mm=tr['comprimento_mm'],comprimento_raiz_mm=62.,
            comprimento_total_nominal_mm=tr['comprimento_mm']+62.))

lines=g['lines'];w50=lines['50']['w_mm'];w70=lines[str(50*math.sqrt(2))]['w_mm'];l70=lines[str(50*math.sqrt(2))]['l90_mm']
xroot=g['inputs'][0]['x']
inputs=[]
for pol,sign_y in [('A',-1),('B',1)]:
    yroot=sign_y*32.;ylocal=sign_y*18.
    signal=[Point(xroot,yroot).buffer(.95,quad_segs=64)]
    ground=[Point(xroot,yroot).buffer(2.65,quad_segs=64)]
    for dx in [-48.,48.]:
        sign=1 if dx>0 else -1
        pts70=[(xroot,yroot),(xroot+sign*l70,yroot)]
        pts50=[pts70[-1],(xroot+dx,yroot),(xroot+dx,ylocal)]
        signal.extend([LineString(pts70).buffer(w70/2,cap_style='square',join_style='mitre'),
            LineString(pts50).buffer(w50/2,cap_style='square',join_style='mitre')])
        full=pts70+pts50[1:]
        ground.append(LineString(full).buffer(1.8,join_style='mitre',quad_segs=32))
        assert abs(LineString(full).length-62)<1e-10
        roots.append(dict(polarizacao=pol,grupo='superior' if dx>0 else 'inferior',
            linha70=pts70,linha50=pts50,comprimento_mm=LineString(full).length,
            entrada_local=[xroot+dx,ylocal]))
    copper_ground=unary_union(ground).difference(Point(xroot,yroot).buffer(1.516,quad_segs=96))
    lands.extend([dict(layer='F',net='SIG_'+pol,shape=unary_union(signal)),
        dict(layer='B',net='RET_'+pol,shape=copper_ground),
        dict(layer='B',net='SIG_'+pol,shape=Point(xroot,yroot).buffer(.8,quad_segs=64).difference(Point(xroot,yroot).buffer(.55,quad_segs=64)))])
    inputs.append(dict(name=pol,x=xroot,y=yroot,drill_mm=1.1))

merged=[]
for layer,net in sorted({(x['layer'],x['net']) for x in lands}):
    p=unary_union([l['shape'] for l in lands if l['layer']==layer and l['net']==net])
    merged.append(dict(layer=layer,net=net,shape=p))
outline=[[-86.8,-35],[92,-35],[92,35],[-86.8,35]]
clear=100.;shorts=[]
for i,a in enumerate(merged):
    assert a['shape'].is_valid and Polygon(outline).contains(a['shape'])
    for b in merged[i+1:]:
        if a['layer']!=b['layer'] or a['net']==b['net']:continue
        clear=min(clear,a['shape'].distance(b['shape']))
        if a['shape'].intersection(b['shape']).area>1e-9:shorts.append([a['layer'],a['net'],b['net']])
assert not shorts and clear>=.15,(clear,shorts)
result=dict(estado='PLANEJAMENTO_GEOMETRICO_NAO_SIMULADO',fonte=str(SRC.relative_to(REPO)),
    fonte_sha256=hashlib.sha256(SRC.read_bytes()).hexdigest(),
    radiadores=4,colunas=1,polarizacoes=2,entradas_externas=2,passo_vertical_mm=48,
    centros_HFSS_X_mm=[-72,-24,24,72],outline=outline,placa_largura_altura_mm=[70,178.8],
    nucleo_mm=.76,material='RO4350B',cobre_mm=.035,acabamento='ENIG',mascara='sem mascara RF',
    topologia='Um 1:4 por polarizacao: 1:2 raiz + dois 1:2 locais; sem resistores de isolamento',
    entradas=inputs,raizes=roots,ramos=branches,vias=vias,lines=lines,
    refletor_planejado_mm=[90,194.8,2],face_inferior_nucleo_z_mm=16.61,
    folga_planar_minima_mm=clear,shorts=shorts,
    lands=[dict(layer=l['layer'],net=l['net'],geometry=mapping(l['shape'])) for l in merged],
    limites=['Removidas as quatro interfaces coaxiais internas: juncoes impressas e retorno continuo.',
        'Compensacoes de comprimento da v05 sao somente ponto de partida; nao comprovam fase uniforme nos quatro radiadores.',
        'Sem simulacao HFSS, validacao de ganho, diagrama, VSWR ou nova cotacao.',
        'As linhas sao valores iniciais do stackup v05; juncoes, dobras e cargas requerem verificacao EM.'])
(OUT/'planejamento.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def patch(p,ax,color):
    if p.geom_type=='MultiPolygon':
        for item in p.geoms:patch(item,ax,color)
        return
    p=orient(p,sign=1);verts=[];codes=[]
    for ring in [p.exterior]+list(p.interiors):
        a=np.asarray(ring.coords);verts.extend(a[:,[1,0]])
        codes.extend([MPath.MOVETO]+[MPath.LINETO]*(len(a)-2)+[MPath.CLOSEPOLY])
    ax.add_patch(PathPatch(MPath(verts,codes),fc=color,ec='none'))

fig,axs=plt.subplots(1,2,figsize=(9,11))
for ax,layer in zip(axs,['F','B']):
    ax.add_patch(plt.Rectangle((-35,-86.8),70,178.8,fc='#f0f4f5',ec='#333333',lw=1))
    for l in merged:
        if l['layer']!=layer:continue
        color='#176a9b' if l['net']=='SIG_A' else '#d17b26' if l['net']=='SIG_B' else '#6c8589'
        patch(l['shape'],ax,color)
    for p in inputs:
        ax.add_patch(plt.Circle((p['y'],p['x']),.55,fc='white',ec='black',lw=.4))
        ax.text(p['y'],p['x']+5,p['name'],ha='center',va='bottom',fontsize=10,fontweight='bold')
    for i,cx in enumerate(result['centros_HFSS_X_mm'],1):
        ax.text(0,cx+14,'E'+str(i),ha='center',fontsize=9)
    ax.set_xlim(-40,40);ax.set_ylim(-93,98);ax.set_aspect('equal')
    ax.set_xlabel('Y horizontal (mm)');ax.set_ylabel('X vertical (mm)')
    ax.set_title(layer+'.Cu — proposta inicial',fontsize=11)
fig.suptitle('Planejamento: quatro elementos verticais\nDuas entradas centrais | um divisor 1:4 por polarização\n70 × 178,8 mm | passo 48 mm | ainda não simulado',fontsize=13)
fig.text(.5,.015,'Raiz 1:2 em X = +2,509 mm; etapas locais em X = −45,491 e +50,509 mm.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.075,1,.91))
fig.savefig(OUT/'disposicao_inicial.png',dpi=170);plt.close(fig)

rows=[]
for br in branches:
    rows.append(f"| {br['polarizacao']} | E{br['elemento']} | {br['comprimento_raiz_mm']:.3f} | {br['comprimento_local_mm']:.3f} | {br['comprimento_total_nominal_mm']:.3f} |")
md='''# Planejamento de quatro elementos em uma placa

Proposta de 9/11/2026, derivada da placa **2_elementos / v05**. Considera quatro radiadores **verticais, em uma coluna**, com duas polarizações. É um planejamento geométrico, ainda sem simulação do novo conjunto.

## Configuração inicial

| Item | Proposta |
|---|---|
| Radiadores | E1…E4 em X = −72, −24, +24 e +72 mm; Y = 0 |
| Passo vertical inicial | 48 mm, herdado do módulo de dois elementos |
| PCB contínua | 70 × 178,8 mm; RO4350B, núcleo 0,76 mm; Cu 35 µm e ENIG |
| Entradas | Duas: A em (X,Y) = (+2,509; −32) mm; B em (+2,509; +32) mm |
| Divisores | Um 1:4 por polarização, implementado por três junções 1:2 em dois estágios |
| Raiz | Um 1:2 junto a cada entrada central |
| Estágios locais | Dois 1:2 por polarização, próximos aos centros dos pares E1/E2 e E3/E4 |
| Cabos externos | Dois, com mesmo comprimento; referência inicial de ensaio: 50 mm, como no módulo |
| Refletor inicial | 90 × 194,8 × 2 mm; alumínio; face inferior do núcleo a Z = 16,61 mm |

Os troncos impressos seguem duas faixas externas, em Y = ±32 mm, chegando aos divisores locais em Y = ±18 mm. Isso permite evitar cruzamentos com os ramos dos radiadores. A largura passa de 49 para 70 mm para acomodar essas duas faixas e seus retornos; o comprimento cresce de 82,8 para 178,8 mm. Essas dimensões são a primeira proposta, não um mínimo otimizado.

Cada polarização usa a árvore abaixo. As duas árvores têm entradas e redes separadas.

```mermaid
flowchart TD
    P[Entrada da polarização] --> R[Raiz 1:2 central]
    R --> L[1:2 inferior]
    R --> U[1:2 superior]
    L --> E1
    L --> E2
    U --> E3
    U --> E4
```

Os quatro pontos que seriam entradas coaxiais dos dois módulos v05 passam a ser junções impressas. Seus pads de sinal na face inferior, furos PTH e aberturas de retorno para o coaxial foram removidos no planejamento. O retorno fica contínuo nesses nós. Permanecem somente as duas conexões externas A/B e as oito vias dos radiadores.

## Comprimentos iniciais

Cada tronco novo mede 62 mm de linha central: 48 mm longitudinais e 14 mm transversais. Os dois troncos de uma polarização têm o mesmo comprimento geométrico. Nas quatro saídas, os ajustes locais da v05 foram preservados como ponto de partida:

| Polarização | Saída | Tronco novo mm | Ramo local mm | Total nominal mm |
|---|---|---:|---:|---:|
'''+ '\n'.join(rows)+'''

A seção inicial de cada divisão usa 70,71 Ω, largura inicial de 0,8604 mm e comprimento de quarto de onda de 8,8163 mm; as ligações restantes usam 50 Ω, largura de 1,6234 mm. São dimensões de partida do mesmo stackup, sujeitas ao ajuste eletromagnético das junções e das cargas.

Os ramos locais têm comprimentos diferentes por causa da compensação encontrada na v05. **Não há comprovação de amplitude ou fase uniforme nos quatro radiadores.** Igualar os dois troncos por grupo não elimina o efeito das impedâncias ativas, dos retornos ou do acoplamento. A divisão nominal 1:4 corresponde a −6,02 dB por saída antes das perdas e dos descasamentos, sob cargas e divisão ideais; não é uma perda medida deste conjunto. Esta árvore não é Wilkinson e não inclui resistores de isolamento.

## Próxima etapa de engenharia

1. Rever as transições entre a raiz e os dois estágios locais, incluindo o retorno contínuo nos antigos pontos de coaxial.
2. Criar o HFSS do módulo completo de quatro elementos com o novo refletor e as duas entradas; manter o ensaio inicial em 5,17 GHz, 14 núcleos e até seis passes.
3. Alimentar A e B com 0,5 W / 0° e conferir ganho frontal, máximos H/V, aberturas, VSWR ativo e VSWR individual com a outra entrada casada. Registrar o ΔS atingido e os passes consecutivos.
4. Ajustar comprimentos e junções usando as fases elétricas efetivas. Confirmar que a melhora de apontamento não piorou o casamento ou o ganho.
5. Após essa comparação, criar a revisão KiCad de quatro elementos e seu pacote de fabricação.

O planejamento foi verificado em 2D: sem sobreposição entre redes diferentes, cobre dentro do contorno e folga mínima de '''+f'{clear:.6f}'+''' mm. Isso não substitui a verificação de continuidade por vias, o DRC do futuro KiCad ou a simulação EM. Não houve novo solve nesta etapa, nem qualificação de banda ou do painel 16×2.

![Disposição proposta](disposicao_inicial.png)

Geometria e premissas em [planejamento.json](planejamento.json). Script reproduzível: [quatro_elementos_planejar.py](../../automacao/quatro_elementos_planejar.py).
'''
(OUT/'README.md').write_text(md,encoding='utf-8')
print(json.dumps({k:result[k] for k in ['estado','placa_largura_altura_mm','folga_planar_minima_mm','shorts']},indent=2))
