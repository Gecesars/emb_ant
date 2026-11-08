"""Imagens da geometria CAD real, mapa de conexoes e estado rastreavel."""
import json,csv,math
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
root=Path('D:/dev/EMBRAER/P2M21/R00_Concepcao');out=root/'imagens';out.mkdir(exist_ok=True)
cfg=json.loads((root/'configuracao.json').read_text())
meshes=json.loads((root/'mecanica/visualizacao.json').read_text())
colors={'AL5052':'#b8c6cf','RO4350B_R01':'#345561','folha_cu':'#e6b45f','POM_nom':'#e9e4d6','ZYF300':'#28777f'}
def draw(ax,mode,extent=None):
    selected=[]
    for item in meshes:
        name=item['name'];isdiv=name.startswith(('D4_','D8_'))
        if mode=='frente' and isdiv:continue
        if mode=='tras' and not (isdiv or name=='Refletor_dobrado' or name.startswith('Espacador_')):continue
        vs=np.array(item['vertices']);ts=vs[np.array(item['triangles'])]
        selected.append((np.mean(vs[:,2]),item,ts))
    for z,item,ts in sorted(selected,key=lambda v:v[0],reverse=mode=='tras'):
        coll=PolyCollection(ts[:,:,[1,0]],facecolors=colors.get(item['material'],'#888'),edgecolors='none',rasterized=True)
        ax.add_collection(coll)
    ax.set_xlim(-55,55);ax.set_ylim(-435,435);ax.set_aspect('equal');ax.set_xlabel('Horizontal Y (mm)');ax.set_ylabel('Vertical X (mm)')
    if extent:ax.set_xlim(*extent[0]);ax.set_ylim(*extent[1])
    ax.grid(alpha=.12);ax.set_axisbelow(True)
fig=plt.figure(figsize=(13,10));gs=fig.add_gridspec(2,3,width_ratios=[.8,.8,2.3])
ax=fig.add_subplot(gs[:,0]);draw(ax,'frente');ax.set_title('Frente: 32 radiadores')
ax=fig.add_subplot(gs[:,1]);draw(ax,'tras');ax.set_title('Traseira: distribuicao')
for i,x in enumerate(cfg['centros_modulos_x_mm'],1):ax.annotate(f'D{i}: 2 x 1:8',(0,x),xytext=(58,x),fontsize=8,arrowprops=dict(arrowstyle='-',lw=.7))
ax.annotate('Raiz: 2 x 1:4',(0,0),xytext=(58,0),fontsize=8,arrowprops=dict(arrowstyle='-',lw=.7))
ax=fig.add_subplot(gs[0,2]);draw(ax,'frente',((-39,39),(12,198)));ax.set_title('Modulo radiante 2 x 4\n186,1125 x 68,3125 mm')
ax=fig.add_subplot(gs[1,2]);draw(ax,'tras',((-43,43),(78,132)));ax.set_title('Divisor local duplo 1:8\n39 x 78 mm; entrada central em cada rede')
fig.suptitle('P2M21 R00 | 16 niveis x 2 colunas | CAD de concepcao',fontsize=16)
fig.text(.5,.015,'Geometria real do FreeCAD. Sem cabos desenhados. Meta: 21 dBi por entrada; desempenho novo ainda nao simulado.',ha='center',fontsize=10)
fig.subplots_adjust(wspace=.7,hspace=.35,bottom=.08,top=.91)
fig.savefig(out/'montagem_e_placas.png',dpi=180);plt.close(fig)

fig,axs=plt.subplots(1,2,figsize=(10,8))
for ax,n in zip(axs,(4,8)):
    g=json.loads((root/f'divisor_1x{n}/geometria.json').read_text());ax.set_facecolor('#dbecee')
    for pol,pts in g['copper'].items():
        pp=np.array(pts);ax.fill(pp[:,0],pp[:,1],color='#cc973c')
    for name,x,y in g['ports']:
        ax.add_patch(plt.Circle((x,y),.525,color='white'));ax.text(x+.6,y+1.4,name,fontsize=8)
    for x,y in g['montagem_furos']:ax.add_patch(plt.Circle((x,y),1.6,color='white',ec='black'))
    ax.set_xlim(-19.5,19.5);ax.set_ylim(-39,39);ax.set_aspect('equal');ax.set_xlabel('X (mm)');ax.set_ylabel('Y (mm)')
    ax.set_title(f'Duplo 1:{n}\nW transformador {g["width"]:.3f} mm; L {g["l_arm"]:.3f} mm')
fig.suptitle('Divisores radiais | PTFE ZYF300CA-C 1,52 mm | Cu 35 um\nSintese inicial: validacao EM e ajustes de casamento pendentes')
fig.tight_layout();fig.savefig(out/'divisores_detalhados.png',dpi=180);plt.close(fig)

# Duas faces do cobre do modulo, extraidas das tesselas CAD reais.
fig,axs=plt.subplots(1,2,figsize=(8,10))
for ax,side in zip(axs,('F','B')):
    ax.set_facecolor('#e3eeee')
    for item in meshes:
        if item['material']!='folha_cu' or not item['name'].startswith('E'):continue
        v=np.array(item['vertices']);z=np.mean(v[:,2])
        if (side=='F' and z<17) or (side=='B' and z>17):continue
        if not (-409<np.mean(v[:,0])<-222):continue
        t=v[np.array(item['triangles'])];t[:,:,0]+=315.6
        ax.add_collection(PolyCollection(t[:,:,[1,0]],facecolors='#bd8735',edgecolors='none',rasterized=True))
    ax.set_xlim(-34.15625,34.15625);ax.set_ylim(-93.05625,93.05625);ax.set_aspect('equal')
    ax.set_xlabel('Horizontal Y (mm)');ax.set_ylabel('Vertical local X (mm)');ax.set_title('Face superior F.Cu' if side=='F' else 'Face inferior B.Cu\nReferencia XY comum, sem espelhar',fontsize=11)
fig.suptitle('P2M21 | modulo de oito radiadores, duas polarizacoes\nCobre das duas faces / RO4350B 0,76 mm',fontsize=13)
fig.tight_layout(rect=(0,0,1,.95));fig.savefig(out/'pcb_duas_faces.png',dpi=180);plt.close(fig)

ports=json.loads((root/'antena/cad/portas.json').read_text());g8=json.loads((root/'divisor_1x8/geometria.json').read_text());g4=json.loads((root/'divisor_1x4/geometria.json').read_text())
links=[]
for mod,mc in enumerate(cfg['centros_modulos_x_mm'],1):
    for pol in 'AB':
        pp=[p for p in ports if p['module']==mod and p['polarization']==pol]
        outs=[p for p in g8['ports'] if p[0].startswith(pol) and not p[0].endswith('IN')]
        start=np.array([[mc+x,y,-11.7] for _,x,y in outs]);end=np.array([[p['x'],p['y'],p['z']] for p in pp])
        cost=np.abs(start[:,None,:]-end[None,:,:]).sum(axis=2);a,b=linear_sum_assignment(cost)
        for i,j in zip(a,b):links.append(dict(tipo='ramal',origem=f'D{mod}:{outs[i][0]}',destino=pp[j]['name'],comprimento_ortogonal_mm=float(cost[i,j]),inicio=start[i].tolist(),fim=end[j].tolist()))
for pol,sign in [('A',-1),('B',1)]:
    outs=[p for p in g4['ports'] if p[0].startswith(pol) and not p[0].endswith('IN')]
    start=np.array([[x,y,-11.7] for _,x,y in outs]);end=np.array([[mc,sign*19.25,-11.7] for mc in cfg['centros_modulos_x_mm']])
    cost=np.abs(start[:,None,:]-end[None,:,:]).sum(axis=2);a,b=linear_sum_assignment(cost)
    for i,j in zip(a,b):links.append(dict(tipo='tronco',origem='RAIZ:'+outs[i][0],destino=f'D{j+1}:{pol}_IN',comprimento_ortogonal_mm=float(cost[i,j]),inicio=start[i].tolist(),fim=end[j].tolist()))
lengths={kind:math.ceil((max(p['comprimento_ortogonal_mm'] for p in links if p['tipo']==kind)+30)/5)*5 for kind in ('ramal','tronco')}
for p in links:p['comprimento_reservado_mm']=lengths[p['tipo']]
network=dict(ligacoes=links,reservas_comprimento_mm=lengths,
 nota='Comprimentos preliminares para reserva de roteamento; nao e lista de corte liberada. Custo Manhattan mais30mm, sem curva 3D otimizada. Cabos ideais de fase no circuito. Ajuste por fase eletrica apos matrizes S reais.',
 entradas='Duas entradas independentes A/B, mesma abertura de32radiadores por entrada, outra casada50ohms.',
 comparacao_posicao=dict(centro_distancia_longitudinal_max_mm=315.6,base_distancia_longitudinal_max_mm=740.6,criterio='Distancia geometrica entre centros, sem somar arcos, conexoes e entradas N.'))
(root/'rede.json').write_text(json.dumps(network,indent=2),encoding='utf8')
with (root/'mapa_conexoes.csv').open('w',newline='',encoding='utf8') as f:
    w=csv.DictWriter(f,fieldnames=['tipo','origem','destino','comprimento_ortogonal_mm','comprimento_reservado_mm']);w.writeheader();w.writerows({k:p[k] for k in w.fieldnames} for p in links)
print('REDE',lengths,'ligacoes',len(links))
