"""Planejamento geométrico e elétrico da rede P2M19; não executa solver."""
from pathlib import Path
import csv, hashlib, itertools, json, math, random
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

REPO=Path(__file__).resolve().parents[3]
OUT=REPO/'projetos/P2M19/rede_R09_PLANEJAMENTO'
WORK=Path('D:/dev/EMBRAER/P2M19/R09_Mecanica_Rede/rede')
OUT.mkdir(parents=True,exist_ok=True); WORK.mkdir(parents=True,exist_ok=True)
SOURCE=REPO/'projetos/P2M19/continuacao_72mm_ref146_14passes/configuracao.json'
CFG=json.loads(SOURCE.read_text())
REF=REPO/'projetos/P2M21/hfss/divisor_1x4'
GEO=json.loads((REF/'geometria.json').read_text())
PORTS={p['name']:p for p in CFG['portas']}
Z=-12.035; R=10.; OD=3.581

def dump(name,data):
    s=json.dumps(data,indent=2,ensure_ascii=False)
    (OUT/name).write_text(s,encoding='utf-8'); (WORK/name).write_text(s,encoding='utf-8')

def rounded(points,r=R,sample=True):
    """Circular-filleted 3D polyline, exact analytical length plus sampled path."""
    pts=[np.array(p,dtype=float) for p in points]
    pts=[p for i,p in enumerate(pts) if i==0 or np.linalg.norm(p-pts[i-1])>1e-6]
    joints=[]
    for i in range(1,len(pts)-1):
        a,b,c=pts[i-1:i+2]; u=(b-a)/np.linalg.norm(b-a); v=(c-b)/np.linalg.norm(c-b)
        ang=math.acos(float(np.clip(u@v,-1,1)))
        if ang<1e-6: joints.append(None); continue
        t=r*math.tan(ang/2); joints.append((b-u*t,b+v*t,u,v,ang,t))
    for i in range(len(pts)-1):
        left=0 if i==0 or joints[i-1] is None else joints[i-1][-1]
        right=0 if i==len(pts)-2 or joints[i] is None else joints[i][-1]
        if left+right>np.linalg.norm(pts[i+1]-pts[i])+1e-6: raise ValueError('Raios não cabem no segmento')
    length=0.; sampled=[pts[0]]; previous=pts[0]
    for j in joints:
        if j is None: continue
        tin,tout,u,v,ang,t=j; length+=np.linalg.norm(tin-previous)
        n=np.cross(u,v); n/=np.linalg.norm(n); inward=np.cross(n,u)
        cen=tin+r*inward; vec=tin-cen
        sampled.append(tin)
        if sample:
            for theta in np.linspace(0,ang,max(7,int(ang*30)))[1:]:
                q=cen+vec*math.cos(theta)+np.cross(n,vec)*math.sin(theta)+n*(n@vec)*(1-math.cos(theta))
                sampled.append(q)
        length+=r*ang; previous=tout
    length+=np.linalg.norm(pts[-1]-previous); sampled.append(pts[-1])
    return float(length),[p.tolist() for p in sampled]

def equal_route(start,end,target,plane,kind='vertical',prefer=1):
    a=np.array(start,float); b=np.array(end,float)
    if kind=='input':
        def proposal(d):
            return [a.tolist(),[a[0]+20,a[1],a[2]],[a[0]+38,a[1],plane],[(a[0]+b[0])/2,(a[1]+b[1])/2+prefer*d,plane],[b[0],b[1],plane],b.tolist()]
    else:
        direction=b[:2]-a[:2]; normal=np.array([-direction[1],direction[0]])/np.linalg.norm(direction)
        def proposal(d):
            midpoint=(a[:2]+b[:2])/2+prefer*d*normal
            return [a.tolist(),[a[0],a[1],plane],[*midpoint,plane],[b[0],b[1],plane],b.tolist()]
    candidates=[]
    for d in np.linspace(0.01,140,150):
        try:
            length,pts=rounded(proposal(d),sample=False)
        except ValueError: continue
        candidates.append((d,length,pts))
        if length>=target:
            if len(candidates)<2: break
            lo=candidates[-2][0]; hi=d
            for _ in range(50):
                mid=(lo+hi)/2
                try: length,pts=rounded(proposal(mid),sample=False)
                except ValueError: lo=mid; continue
                if length<target: lo=mid
                else: hi=mid
            d=(lo+hi)/2; length,pts=rounded(proposal(d))
            return dict(comprimento_eixo_mm=length,pontos_controle_mm=proposal(d),raio_eixo_mm=R,pontos_amostrados_mm=pts,
                largura_max_Y_mm=max(abs(p[1]) for p in pts),desvio_apice_mm=d)
    raise RuntimeError((kind,start,end,target,candidates[:1],candidates[-1:]))

boards=[]
for name,x,sx,kind in [('D0',0.,60.,'duplo_1x2'),('D1',-192.,39.,'duplo_1x4'),('D2',192.,39.,'duplo_1x4')]:
    ports=[]
    for pol,y in [('A',-19.25),('B',19.25)]:
        ports.append(dict(nome=pol+'_IN',x=x,y=y,z=Z))
        if name=='D0':
            for out,dx in [('INF',-15.2),('SUP',15.2)]: ports.append(dict(nome=pol+'_'+out,x=x+dx,y=y,z=Z))
        else:
            for pn,px,py in GEO['ports']:
                if pn.startswith(pol) and pn!=pol+'_IN': ports.append(dict(nome=pn,x=x+px,y=py,z=Z))
    boards.append(dict(nome=name,funcao=kind,centro_xy_mm=[x,0],dimensoes_xy_mm=[sx,78.],substrato_z_mm=[-12.,-10.48],
        sinal_z_mm=Z,terra_z_mm=-10.445,material='ZYF300CA-C',h_core_mm=1.52,cu_um=35,
        furos_montagem_xy_mm=[[x+xx,yy] for xx in ([-26.,26.] if name=='D0' else [-15.5,15.5]) for yy in [-35.,35.]],
        diametro_furos_proposto_mm=3.2,portas=ports,estado='ENVELOPE E TOPOLOGIA; COBRE PENDENTE DE AJUSTE EM'))
BD={b['nome']:b for b in boards}
def pcoord(board,name):
    p=next(p for p in BD[board]['portas'] if p['nome']==name); return [p['x'],p['y'],p['z']]

cables=[]; route_pool={}
for pol,y in [('A',-24.),('B',24.)]:
    start=[-367.25,y,-45.]; end=pcoord('D0',pol+'_IN')
    route=equal_route(start,end,425.,-63.,'input',-1 if pol=='A' else 1)
    cables.append(dict(id='IN_'+pol,classe='entrada',origem='N_'+pol,destino='D0_'+pol+'_IN',polarizacao=pol,**route))
    route_pool['IN_'+pol]=[route]
    plane=-35. if pol=='A' else -42.
    for branch,cellrows,outlet in [('D1',[1,2],'INF'),('D2',[3,4],'SUP')]:
        a=pcoord('D0',pol+'_'+outlet); b=pcoord(branch,pol+'_IN')
        options=[]
        for plane_t in [-50.,-53.,-55.,-57.]:
            for sign in [-1,1]:
                try:
                    ro=equal_route(a,b,260.,plane_t,prefer=sign)
                    if ro['largura_max_Y_mm']<=69.:options.append(ro)
                except RuntimeError: pass
        route=min(options,key=lambda x:x['largura_max_Y_mm'])
        cables.append(dict(id='T_'+branch+'_'+pol,classe='tronco',origem='D0_'+pol+'_'+outlet,destino=branch+'_'+pol+'_IN',polarizacao=pol,**route))
        route_pool['T_'+branch+'_'+pol]=options
        outputs=[pcoord(branch,pol+str(i)) for i in range(1,5)]
        destinations=[f'C{c}R{rr}_{pol}' for rr in cellrows for c in [1,2]]
        choices=[]
        for perm in itertools.permutations(destinations):
            distances=[np.linalg.norm(np.array(out[:2])-np.array([PORTS[dn]['x'],PORTS[dn]['y']])) for out,dn in zip(outputs,perm)]
            choices.append((max(distances),sum(distances),perm))
        order=min(choices)[2]
        for i,dn in enumerate(order,1):
            b=[PORTS[dn][k] for k in ['x','y','z']]; a=pcoord(branch,pol+str(i))
            options=[]
            for plane_r in [-35.,-38.,-41.,-44.,-47.,-50.,-53.]:
                for sign in [-1,1]:
                    try:
                        ro=equal_route(a,b,205.,plane_r,prefer=sign)
                        if ro['largura_max_Y_mm']<=69.:options.append(ro)
                    except RuntimeError: pass
            route=min(options,key=lambda x:x['largura_max_Y_mm'])
            cables.append(dict(id='R_'+dn,classe='ramal',origem=branch+'_'+pol+str(i),destino=dn,polarizacao=pol,**route))
            route_pool['R_'+dn]=options

# Collision-aware selection of equal-length candidate curves. No RF solve.
from scipy.spatial import cKDTree
def dense(r):
    p=np.array(r['pontos_amostrados_mm']); pts=[]
    for a,b in zip(p[:-1],p[1:]):pts.extend(np.linspace(a,b,max(2,int(np.linalg.norm(b-a)/.5)+2)))
    return np.array(pts)
cloud={}; trees={}
for ci,c in enumerate(cables):
    for ri,r in enumerate(route_pool[c['id']]):
        cloud[(ci,ri)]=dense(r);trees[(ci,ri)]=cKDTree(cloud[(ci,ri)])
dcache={}
def distance(i,ri,j,rj):
    if i>j:i,ri,j,rj=j,rj,i,ri
    key=i,ri,j,rj
    if key not in dcache:dcache[key]=float(trees[(i,ri)].query(cloud[(j,rj)])[0].min())
    return dcache[key]
def penalty(d):return max(0.,4.6-d)**2
def score(state):return sum(penalty(distance(i,state[i],j,state[j])) for i in range(len(cables)) for j in range(i))
rng=random.Random(9014);best_state=None;best_score=1e99
for restart in range(8):
    state=[rng.randrange(len(route_pool[c['id']])) for c in cables]
    for iteration in range(500):
        sc=score(state)
        if sc<best_score:best_score=sc;best_state=state.copy()
        if sc<1e-10:break
        burden=[sum(penalty(distance(i,state[i],j,state[j])) for j in range(len(cables)) if j!=i) for i in range(len(cables))]
        feasible=[i for i,c in enumerate(cables) if len(route_pool[c['id']])>1]
        i=max(feasible,key=lambda n:burden[n]+rng.random()*.25)
        vals=[]
        for ri in range(len(route_pool[cables[i]['id']])):
            val=sum(penalty(distance(i,ri,j,state[j])) for j in range(len(cables)) if j!=i)
            vals.append((val+rng.random()*(.12 if iteration%20<3 else .0001),ri))
        state[i]=min(vals)[1]
        if iteration%35==34:
            for _ in range(2):
                k=rng.choice(feasible);state[k]=rng.randrange(len(route_pool[cables[k]['id']]))
    if best_score<1e-10:break
for i,c in enumerate(cables):c.update(route_pool[c['id']][best_state[i]])
pair_min=min((distance(i,best_state[i],j,best_state[j]),cables[i]['id'],cables[j]['id']) for i in range(len(cables)) for j in range(i))
dump('auditoria_distancias_cabos.json',dict(metodo='Amostragem dos arcos e segmentos <=0,5mm; limite conservador subtrai0,5mm +0,004mm de discretizacao de arco',
    distancia_minima_amostras_mm=pair_min[0],par_minimo=pair_min[1:],diametro_mm=OD,
    folga_conservadora_minima_mm=pair_min[0]-.504-OD,sem_interferencia_cabo_cabo=pair_min[0]-.504>OD,
    penalidade_selecao=best_score,aviso='Nao substitui auditoria CAD com ferragens, reforcos e refletor'))

summary=dict(estado='PLANEJAMENTO SEM NOVO SOLVE OU LIBERACAO DE FABRICACAO',sistema_coordenadas='X vertical, Y transversal, Z frontal; refletor frontal Z=0',
    referencia_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),topologia='2 entradas -> duplo1:2 central -> 2 duplos1:4 distribuidos -> 16 portas C12',
    circuitos_1x2=2,circuitos_1x4=4,quantidade_pcbs=3,entradas=2,saidas=16,placas=boards,
    cabo_modelo='Micro-Coax UT-141C',cabo_od_mm=OD,cabos=cables,quantidade_cabos=len(cables),
    comprimento_total_eixos_mm=sum(c['comprimento_eixo_mm'] for c in cables),comprimento_por_caminho_mm=890.,
    comprimentos_iguais_por_classe_mm={'entrada':425.,'tronco':260.,'ramal':205.},
    aviso='Curvas matematicas de planejamento; montagem precisa verificar interferencias. Nao e lista de corte: faltam decapagem, insercao e ensaio de fase.',
    fonte_cabo='https://www.micro-coax.com/wp-content/uploads/2024/12/micro-coax-ut-141c-datasheet.pdf')
assert len(cables)==22 and len({c['destino'] for c in cables if c['classe']=='ramal'})==16
assert max(abs(c['comprimento_eixo_mm']-summary['comprimentos_iguais_por_classe_mm'][c['classe']]) for c in cables)<1e-6
dump('plano_rede.json',summary)
with (OUT/'conexoes.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=['id','classe','polarizacao','origem','destino','comprimento_eixo_mm']);w.writeheader()
    for c in cables:w.writerow({k:c[k] for k in w.fieldnames})

fig,ax=plt.subplots(figsize=(6,13))
ax.add_patch(Rectangle((-73,-388),146,776,facecolor='#d8dde4',edgecolor='#596171'))
for cell in CFG['celulas']:
    ax.add_patch(Rectangle((cell['y']-35,cell['x']-92),70,184,fill=False,edgecolor='#b7bfc6',linestyle='--'))
    ax.text(cell['y'],cell['x']+55,cell['nome'],ha='center',color='#56606a',fontsize=7)
for c in cables:
    pts=np.array(c['pontos_amostrados_mm']);ax.plot(pts[:,1],pts[:,0],c='#c45730' if c['polarizacao']=='A' else '#237eb5',lw=.75,alpha=.6)
for b in boards:
    x,y=b['centro_xy_mm'];sx,sy=b['dimensoes_xy_mm']
    ax.add_patch(Rectangle((y-sy/2,x-sx/2),sy,sx,facecolor='#2c8755',edgecolor='#15402a',zorder=4))
    ax.text(y,x,b['nome']+' '+b['funcao'].replace('_',' ').replace('1x','1:'),ha='center',va='center',color='white',fontsize=7,zorder=5)
    for p in b['portas']:ax.plot(p['y'],p['x'],'o',color='gold',ms=2,zorder=5)
ax.set(xlim=(-100,100),ylim=(-420,420),aspect='equal',xlabel='Y transversal (mm)',ylabel='X vertical (mm)')
ax.set_title('P2M19 — rede traseira proposta\n3 PCBs / 2 entradas / 16 saídas',fontsize=11)
ax.plot([],[],color='#c45730',label='Polarização A');ax.plot([],[],color='#237eb5',label='Polarização B');ax.legend(loc='upper center',fontsize=7)
fig.text(.5,.02,'PRELIMINAR — sem simulação; traçados de cabos sujeitos à revisão de montagem',ha='center',fontsize=8)
fig.tight_layout(rect=(0,.035,1,1));fig.savefig(OUT/'disposicao_rede.png',dpi=160);plt.close(fig)

fig,axes=plt.subplots(1,3,figsize=(13,5))
for ax,b in zip(axes,boards):
    x,y=b['centro_xy_mm'];sx,sy=b['dimensoes_xy_mm']
    ax.add_patch(Rectangle((-sy/2,-sx/2),sy,sx,facecolor='#d8efdc',edgecolor='#315f3c'))
    for p in b['portas']:
        ax.plot(p['y'],p['x']-x,'o',color='#c3891b');ax.text(p['y'],p['x']-x+1.5,p['nome'],ha='center',fontsize=7)
    for hx,hy in b['furos_montagem_xy_mm']:ax.add_patch(plt.Circle((hy,hx-x),1.6,color='white',ec='black'))
    ax.set(xlim=(-43,43),ylim=(-34,34),aspect='equal',xlabel='Y (mm)',ylabel='X local (mm)')
    ax.set_title(f"{b['nome']} — {b['funcao']}\n{sx:g} × {sy:g} mm")
fig.suptitle('Interfaces propostas das PCBs — sem cobre roteado / sem Gerbers',fontsize=13)
fig.tight_layout();fig.savefig(OUT/'interfaces_pcbs.png',dpi=150);plt.close(fig)

# Dimensions below are synthesis seeds, not a manufactured/matched design.
def microstrip(z_target,h=1.52,er=2.94):
    def calc(w):
        u=w/h; ee=(er+1)/2+(er-1)/2*(1/math.sqrt(1+12/u)+(0.04*(1-u)**2 if u<1 else 0))
        z=60/math.sqrt(ee)*math.log(8/u+u/4) if u<=1 else 120*math.pi/(math.sqrt(ee)*(u+1.393+.667*math.log(u+1.444)))
        return z,ee
    lo=.01;hi=20.
    for _ in range(60):
        mid=(lo+hi)/2
        if calc(mid)[0]>z_target:lo=mid
        else:hi=mid
    w=(lo+hi)/2; ee=calc(w)[1]
    return dict(Z_ohm=z_target,largura_semente_mm=w,epsilon_efetivo=ee,lambda_quarto_mm=299792458/5.17e9/math.sqrt(ee)*250)
atten=(27.6+(5.17-5)*(41.6-27.6)/5)/30.48
velocity=1/(50*95.2e-12);deg_mm=360*5.17e9/velocity/1000
electrical=dict(frequencia_GHz=5.17,impedancia_interfaces_ohm=50.,material='ZYF300CA-C',h_core_mm=1.52,dk=2.94,tandelta=.0016,cu_um=35,
    acabamento='ENIG nominal; NiP e espessura deverão corresponder ao stackup contratado',linhas_semente=[microstrip(z) for z in [50.,math.sqrt(2)*50,100.]],
    formulas='Aproximação quasi-estática de microstrip, condutor sem espessura; corrigir 35um/ENIG/junções/terminais no projeto RF.',
    transformacao='1:2: dois ramos de 70.7107ohm/90graus; 1:4: quatro ramos de100ohm/90graus. Todos terminados nominalmente em50ohm.',
    isolamento='T/radial sem resistores; as saídas não são isoladas. Cargas C12 acopladas exigem análise multip portas.',
    metas_propostas_nao_qualificadas=dict(vswr_final_ativo_max=1.25,desequilibrio_amplitude_pp_dB=.15,desequilibrio_fase_pp_graus=3),
    cabo=dict(OD_mm=3.581,diametro_central_mm=.9195,raio_interno_min_ficha_mm=1.905,raio_eixo_min_derivado_mm=3.6955,raio_eixo_projetado_mm=10.,
        capacitancia_pF_m=95.2,velocidade_derivada_m_s=velocity,fator_velocidade_derivado=velocity/299792458,
        fase_graus_por_mm=deg_mm,diferenca_comprimento_equivalente_3graus_mm=3/deg_mm,
        atenuacao_tipica_interpolada_517_GHz_dB_m=atten,atenuacao_tipica_por_caminho_890mm_dB=atten*.89,
        aviso='Interpolação linear entre pontos5/10GHz da ficha; não medição do cabo montado. Equalizar eletricamente comVNA, além do comprimento físico.'),
    orcamento=dict(ganho_frontal_baseline_dBi=20.544040492811696,meta_produto_dBi=19.,orcamento_perdas_adicionais_dB=1.544040492811696,
        saldo_apos_estimativa_cabos_dB=1.544040492811696-atten*.89,
        aviso='Saldo precisa cobrir PCBs externas, conectores, soldas, descasamento e desequilíbrio. Não prediz ganho final.'),
    referencias_historicas=dict(duplo1x4_vswr_AB=[1.5366479139179567,1.5364643986338682],duplo1x4_ILexcess_AB_dB=[.3319305937637802,.33038328780092396],
        duplo1x8_vswr_AB=[1.6961379550500706,1.6967262149272893],duplo1x8_ILexcess_AB_dB=[.5249395159473819,.5229614583150618],
        duplo1x2_R05_ILexcess_centro_dB=.2216646489816128,
        aviso='Históricos de geometrias distintas; não representam a rede R09 e não podem ser somados como validação do produto.'),
    nenhuma_simulacao_executada=True)
dump('dimensionamento_eletrico_preliminar.json',electrical)
comparison=[dict(topologia='Duplo1:8 central',pcbs=1,cabos=18,entrada_mm=425.,ramal_mm=390.,comprimento_por_caminho_mm=815.,total_mm=7090.,
    observacao='Proposta comparativa de reserva de comprimento, sem roteamento3D; menos juntas e aproximadamente0.069dB menos cabo por caminho, mais1.92m de cabo total; 1:8radial exige141.4ohm e históricoVSWR1.697.'),
    dict(topologia='Duplo1:2 + dois duplos1:4 distribuídos',pcbs=3,cabos=22,entrada_mm=425.,tronco_mm=260.,ramal_mm=205.,comprimento_por_caminho_mm=890.,total_mm=5170.,
    observacao='Proposta adotada: ramaisfinais menores, menos27.08% de cabo total; 22curvas calculadas e auditadas entre si; mais quatrocabos e duasPCBs. Não afirma menor perda RF que alternativa central.')]
dump('comparacao_topologias.json',comparison)
bom=[['D0','PCB duplo1:2',1,'60x78mm, ZYF300CA-C1.52, Cu35um, ENIG','Planejamento; cobre/ajuste RF pendentes'],
 ['D1/D2','PCB duplo1:4',2,'39x78mm, mesmo stackup deD0','Referência radial a ajustar; não fabricar'],
 ['ANT','PCB radiante C12 de4elementos',8,'184x70mm, RO4350B0.76mm','Existentes; geometria preservada'],
 ['IN','UT-141C entrada',2,'425mm de eixo cada','Não é corte; incluir inserção/decapagem após ensaio'],
 ['T','UT-141C tronco',4,'260mm de eixo cada','Mesma classe/mesmo comprimento e fase'],
 ['R','UT-141C ramal',16,'205mm de eixo cada','Mesmo comprimento; não encurtar os destinos próximos'],
 ['N','Amphenol 082-6784 Nfêmea',2,'STEP existente; caudas emX=-367.25,Y=±24,Z=-45','Alojamento e fixação na mecânicaR09'],
 ['SP','Espaçador POM para PCBdistribuidora',12,'OD5x8.48mm, interfaceM3','Centros/quantidade coordenados com mecânica'],
 ['FIX','Conjunto fixaçãoM3 de distribuidoras',12,'Furo passantePCBØ3.2','Comprimentos/arruelas naBOMmecânica']]
with (OUT/'lista_materiais_rede_PRELIMINAR.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f,delimiter=';');w.writerow(['id','item','quantidade','especificacao','estado']);w.writerows(bom)
readme=f'''# P2M19 R09 — planejamento da rede externa

**Sem nova simulação. Preliminar, não liberado para fabricação.** A proposta mantém as oito placas C12, duas colunas a 72 mm e quatro níveis de placas. As dezesseis portas locais serão alimentadas por duas entradas independentes, A e B. A geometria RF da R08 permanece preservada.

## Topologia e posição

`N A/B → D0 (duplo 1:2) → D1/D2 (duplo 1:4 cada) → 16 entradas das oito C12`.

São **três PCBs, dois circuitos 1:2 e quatro circuitos 1:4**. Cada filial atende quatro placas, em duas posições verticais e duas colunas. Não há união entre A/B nem novas divisões nas placas radiantes.

| PCB | Centro X/Y (mm) | Envelope X×Y (mm) | Função |
|---|---:|---:|---|
| D0 | 0 / 0 | 60×78 | Duas entradas centrais e quatro troncos |
| D1 | −192 / 0 | 39×78 | Placas R1/R2; quatro saídas por polarização |
| D2 | +192 / 0 | 39×78 | Placas R3/R4; quatro saídas por polarização |

X é vertical, Y transversal e Z aponta para a frente. Laminados entre Z=−12 e −10,48 mm; sinal na face posterior Z=−12,035 mm. Furos propostos de Ø3,2 mm para M3: D0 em X local ±26/Y ±35; D1/D2 em X local ±15,5/Y ±35. Esses furos diferem da referência histórica e exigem reserva sem cobre no futuro layout.

![Posicionamento da rede](disposicao_rede.png)

![Interfaces propostas das PCBs](interfaces_pcbs.png)

## Chicote com caminhos iguais

| Classe | Quantidade | Comprimento de eixo por cabo |
|---|---:|---:|
| Entrada N → D0 | 2 | 425 mm |
| Tronco D0 → filial | 4 | 260 mm |
| Ramal filial → C12 | 16 | 205 mm |

São **22 cabos e 5,170 m de eixos**. Cada caminho N → C12 tem **890 mm de cabo**, além dos trajetos impressos idênticos por classe. Os comprimentos são analíticos, incluindo arcos com raio de eixo de 10 mm; não são comprimentos das linhas facetadas usadas para visualização. **Não é lista de corte**: faltam inserção, decapagem, terminação e ensaio do chicote soldado.

As rotas iniciais com cruzamentos foram corrigidas. A auditoria entre os 22 cabos encontrou distância mínima amostrada entre centros de **{pair_min[0]:.6f} mm** e folga superficial conservadora de **{pair_min[0]-.504-OD:.6f} mm**, descontando 0,504 mm para discretização. A verificação contra reforços, postes, base e placas pertence à montagem FreeCAD; este teste isolado não libera fabricação.

O cabo de referência é **Micro-Coax UT-141C**, 50 Ω, diâmetro externo 3,581 mm e condutor central de 0,9195 mm. O raio interno mínimo da ficha é 1,905 mm, equivalente a raio de eixo de 3,6955 mm; foram adotados 10 mm. Fonte primária consultada em 14/11/2026: [ficha UT-141C](https://www.micro-coax.com/wp-content/uploads/2024/12/micro-coax-ut-141c-datasheet.pdf).

Comprimento físico igual não garante fase igual após soldagem. De 95,2 pF/m e 50 Ω da ficha, deriva-se velocidade de {velocity/299792458:.5f}c e aproximadamente {deg_mm:.3f}°/mm em 5,17 GHz. Uma diferença total de 3° equivale a {3/deg_mm:.3f} mm nesse modelo. As metas propostas são desequilíbrio total ≤3° e ≤0,15 dB; conferir eletricamente com VNA, usando cabo do mesmo lote e terminação reproduzível. Isso não constitui tolerância de corte aprovada.

## Dimensionamento das PCBs

A referência inicial é ZYF300CA-C, núcleo de 1,52 mm, Dk=2,94 e tanδ=0,0016 nominais, cobre de 35 µm e ENIG. A cotação JLC de 7/11 documenta o material historicamente; não houve nova consulta de estoque/preço. As radiantes permanecem RO4350B de 0,76 mm.

O 1:2 pode partir de dois transformadores de 70,7107 Ω/90°; o 1:4 de quatro transformadores de 100 Ω/90°. Síntese quasi-estática, ainda sem corrigir espessura de cobre:

| Impedância | Largura inicial (mm) | Quarto de onda (mm) |
|---|---:|---:|
| 50 Ω | 3,906 | 9,402 |
| 70,71 Ω | 2,172 | 9,587 |
| 100 Ω | 1,042 | 9,775 |

O 1:4 histórico usa W100=1,004 mm, L=9,769 mm e W50=3,872 mm. Essas dimensões são sementes para ajustar junções, pads de solda e retornos de terra com os efeitos do cobre/ENIG. Os ramais devem conservar comprimento físico e elétrico iguais, não apenas fase igual módulo 360°.

O 1:4 histórico tem VSWR **1,53665/1,53646** e perda excedente **0,33193/0,33038 dB**, com saídas de 50 Ω. **Não atende à meta futura de VSWR ≤1,25**; precisa de ajuste antes de fabricação. É uma rede T/radial sem resistores e sem isolamento entre saídas. A antena real deve ser carregada como matriz S16 acoplada.

## Comparação das alternativas

| Arquitetura | PCBs | Cabos | Eixos totais propostos | Cabo por caminho |
|---|---:|---:|---:|---:|
| Duplo 1:8 central | 1 | 18 | 7,090 m | 815 mm |
| Duplo 1:2 + dois duplos 1:4 | 3 | 22 | 5,170 m | 890 mm |

A distribuída reduz o cabo total em **27,08%** e encurta os ramais finais de 390 para 205 mm. Acrescenta duas PCBs e quatro interligações. A central pode ter menor perda por caminho, cerca de 0,069 dB menos cabo neste orçamento, e menos juntas; porém a referência radial 1:8 exige trilhas de 141,4 Ω e apresenta VSWR ≈1,697. A distribuída foi escolhida para organizar o painel e facilitar as interfaces, sem alegar que já minimiza a perda RF. Os 390 mm da alternativa são reserva comparativa não roteada; a proposta distribuída tem 22 curvas calculadas.

## Orçamento de perdas

A baseline de **20,544 dBi** inclui os divisores nas C12 e o acoplamento entre placas; **não inclui a nova rede externa**. A margem aritmética até 19 dBi é 1,544 dB. Interpolando os pontos de 5/10 GHz da ficha, o cabo tem cerca de {atten:.3f} dB/m em 5,17 GHz, ou **{atten*.89:.3f} dB** por caminho de 890 mm. Sobram aproximadamente **{1.544040492811696-atten*.89:.3f} dB** para PCBs externas, conectores N, soldas, descasamento e desequilíbrio. É orçamento típico, sem garantia de ganho final.

Os históricos 1:2 R05 (0,222 dB) e 1:4 (0,332 dB) são geometrias distintas. Não podem ser somados e tratados como resultado desta rede, sobretudo com o 1:4 descasado. **Não foi calculado novo VSWR nas duas entradas N nem ganho com a rede R09.**

O orçamento para manter 19 dBi é apertado: se os novos estágios externos consumissem aproximadamente 0,55 dB, restariam cerca de 0,17 dB para conectores, soldas e outros efeitos. Isso serve para orientar o ajuste e a comparação com a alternativa central; não demonstra aprovação nem reprovação do produto completo.

## Sequência após autorização de retomada

1. Ajustar o duplo 1:2 e o duplo 1:4 separadamente em HFSS, com saídas de 50 Ω e terminais de solda reais. Preservar a simetria e não incluir cabos em 3D.
2. Combinar S6/S10 dos divisores e S16 da antena no Nexxim. A rede externa equivale a S18 antes de conectar a antena; após conectar as dezesseis cargas, restam as duas entradas N. Começar com cabos ideais de fase; tratar perdas reais em caso separado autorizado.
3. Verificar VSWR ativo com A/B iguais em fase e VSWR com a outra entrada casada, amplitude/fase nas C12 e recomposição dos campos complexos H/V. Metas propostas: VSWR ≤1,25 e ganho ≥19 dBi, ainda não demonstrados com a rede.
4. Congelar cobre e chicote, executar DRC e só então gerar Gerbers. Qualquer esgotamento de memória deverá ser registrado e interromper o solve, sem retomada automática.

[Interfaces e curvas](plano_rede.json) · [Conexões](conexoes.csv) · [Dimensionamento elétrico](dimensionamento_eletrico_preliminar.json) · [BOM](lista_materiais_rede_PRELIMINAR.csv) · [Comparação](comparacao_topologias.json) · [Auditoria dos cabos](auditoria_distancias_cabos.json).

Não foram criados cobre novo no KiCad ou Gerbers. Os desenhos são interfaces de planejamento. A [montagem FreeCAD R09](../mecanica_R09_PRELIMINAR/README.md) documenta os novos componentes mecânicos, sem validação RF/estrutural do conjunto.

A [auditoria CAD dos cabos](../mecanica_R09_PRELIMINAR/verificacao_cabos.json) verifica a mesma interface SHA-256 `5ee180f49d67fa1d26430e51acc6bf7ebc6eaff4132a446e3cf6267c73a32173`. Os 22 cabos foram reconstruídos com arcos OCCT, sem interferências entre si, folga exata mínima de 1,156834 mm e comprimentos coincidentes com os analíticos. Isso complementa a auditoria conservadora de amostras; a verificação completa das ferragens e demais peças permanece descrita nas evidências mecânicas.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
print(json.dumps({'arquivos':str(OUT),'cabos':len(cables),'total_mm':summary['comprimento_total_eixos_mm'],'max_y_mm':max(c['largura_max_Y_mm'] for c in cables)},indent=2))
