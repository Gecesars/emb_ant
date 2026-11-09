"""Preparar os dez 1:4; a interface final de 32 saidas para 64 portas fica pendente."""
from pathlib import Path
import json,shutil,csv,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyArrowPatch

repo=Path(__file__).resolve().parents[3]
source=repo/'projetos/P2M21'
root=Path('D:/dev/EMBRAER/P2M21/R05_Dez_Divisores_1x4')
dest=source/'rede_dez_1x4'
for p in (root,dest,dest/'referencia_1x4',dest/'imagens',dest/'freecad'):
    p.mkdir(parents=True,exist_ok=True)
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
positions=[('D0',0,None),('D1',-315.6,[1,4]),('D2',-105.2,[5,8]),('D3',105.2,[9,12]),('D4',315.6,[13,16])]
cfg=dict(revisao='R05_Dez_Divisores_1x4',estado='POSICIONAMENTO_PREPARADO_INTERFACE_FINAL_PENDENTE',
    niveis=16,colunas=2,radiadores=32,portas_radiantes=64,entradas=2,
    divisores_1x4=10,pcbs_duplas_propostas=5,saidas_finais_por_entrada=16,saidas_finais_total=32,
    posicoes=[dict(pcb=n,centro_x_mm=x,centro_y_mm=0,base_z_mm=-11.52,niveis=niv,redes=[n+'A',n+'B']) for n,x,niv in positions],
    placa_referencia_mm=[39,78,1.52],material='ZYF300CA-C',dk=2.94,df=.0016,cu_um=35,
    geometria_1x4='Referencia R00, inalterada; nao representa novo casamento aprovado.',
    interface_pendente='Definir ligacao das 32 saidas finais as 64 portas A/B. Nenhuma porta suprimida ou ligada em paralelo sem aprovacao.',
    proposta='Uma entrada por polarizacao; cada saida local atende duas colunas do mesmo nivel mediante 1:2 integrado na PCB. Requer 32 redes 1:2 adicionais e revisao das placas radiantes.',
    divisoes_1x2_propostas=32,divisoes_1x2_implementadas=0,
    solver_executado=False,geometria_antena_alterada=False,
    proximos_ensaios=dict(frequencia_GHz=5.17,sweep=False,nucleos=14,max_passes=4,delta_s_referencia=.04),
    comprimentos_cabos='Nao liberados. Caminhos devem ter atraso eletrico equilibrado, com cabos sem atenuacao apenas no circuito.')
write(root/'configuracao.json',cfg);write(dest/'configuracao.json',cfg)
copies=[(source/'kicad/P2M21_Duplo_1x4'/n,dest/'referencia_1x4'/n) for n in ['P2M21_Duplo_1x4.kicad_pcb','P2M21_Duplo_1x4.kicad_pro','drc.json']]
copies += [(source/'hfss/divisor_1x4'/n,dest/'referencia_1x4'/n) for n in ['P2M21_Duplo_1x4.aedt','divisor.s10p','analise.json','convergencia.txt']]
local=Path('D:/dev/EMBRAER/P2M21/R00_Concepcao/divisor_1x4')
copies +=[(local/n,dest/'referencia_1x4'/n) for n in ['P2M21_Duplo_1x4.FCStd','geometria.json']]
evidence=[]
for src,out in copies:
    shutil.copy2(src,out);assert src.read_bytes()==out.read_bytes()
    evidence.append(dict(fonte=str(src),copia=out.relative_to(dest).as_posix(),sha256=hashlib.sha256(out.read_bytes()).hexdigest()))
write(dest/'origem_referencias.json',evidence)
rows=[]
for pol in 'AB':
    rows.append(dict(origem='Entrada_'+pol,destino='D0'+pol+'_IN',tipo='entrada',estado='topologia_definida'))
    for mod in range(1,5):
        rows.append(dict(origem='D0'+pol+'_OUT'+str(mod),destino='D'+str(mod)+pol+'_IN',tipo='tronco',estado='ramo_logico_porta_fisica_a_atribuir'))
        for j in range(1,5):
            level=(mod-1)*4+j
            rows.append(dict(origem=f'D{mod}{pol}_OUT{j}',destino=f'INTERFACE_NIVEL_{level:02}_{pol}',tipo='saida_final',estado='64_portas_dependem_de_interface_a_confirmar'))
with (dest/'mapa_logico.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=['origem','destino','tipo','estado']);w.writeheader();w.writerows(rows)
assert len([r for r in rows if r['tipo']=='saida_final'])==32
fig,axs=plt.subplots(1,2,figsize=(13,9),gridspec_kw={'width_ratios':[1,1.55]})
ax=axs[0];ax.set_xlim(-115,155);ax.set_ylim(-445,445);ax.set_aspect('equal')
ax.add_patch(Rectangle((-50,-425),100,850,fc='#e7edf1',ec='#8597a6'))
for level in range(16):
    x=(level-7.5)*52.6
    for y in [-20,20]:ax.add_patch(Rectangle((y-14.15625,x-14.15625),28.3125,28.3125,fc='#b7c6ba',ec='#8ba190',alpha=.55))
for name,x,niv in positions:
    ax.add_patch(Rectangle((-39,x-19.5),78,39,fc='#16697a',ec='#143d4c'))
    ax.text(0,x,name+' A | B',ha='center',va='center',color='white',fontsize=9)
    ax.annotate(f'{name}: X={x:+.1f} mm\n'+('central' if niv is None else f'niveis {niv[0]} a {niv[1]}'),xy=(39,x),xytext=(60,x),va='center',fontsize=9,arrowprops={'arrowstyle':'-','color':'#436170'})
ax.set_title('Posicoes propostas na traseira\n5 PCBs, 2 circuitos 1:4 em cada uma',fontsize=12)
ax.set_xlabel('Horizontal Y (mm)');ax.set_ylabel('Vertical X (mm)');ax.grid(alpha=.12)
ax=axs[1];ax.set_xlim(0,12);ax.set_ylim(-.5,10);ax.axis('off')
def box(x,y,w,h,label,color='#e8f1f4'):
    ax.add_patch(Rectangle((x,y),w,h,fc=color,ec='#326071',lw=1.2));ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=10)
def arrow(a,b):ax.add_patch(FancyArrowPatch(a,b,arrowstyle='->',mutation_scale=10,lw=1,color='#326071'))
box(.1,4.3,1.8,1.0,'Entrada A\n50 ohms');box(2.4,4.3,2,1,'D0A\n1:4');arrow((1.9,4.8),(2.4,4.8))
for i,y in enumerate([8,5.8,3.6,1.4],1):
    box(5.5,y,2.2,1.0,f'D{i}A  1:4\nniveis {4*i-3}-{4*i}')
    arrow((4.4,4.8),(5.5,y+.5));arrow((7.7,y+.5),(8.5,y+.5))
    box(8.5,y-.15,3.1,1.3,'4 saidas\ninterface com 8 portas\na definir','#fff0ce')
ax.text(6,9.7,'Cadeia de uma entrada; repetir para B',ha='center',fontsize=13,weight='bold')
ax.text(6,.45,'2 centrais + 8 locais = 10 divisores 1:4\n32 saidas finais para 64 portas radiantes',ha='center',fontsize=12,weight='bold')
fig.suptitle('P2M21 | proposta de distribuicao com dez divisores 1:4',fontsize=17)
fig.text(.5,.035,'INTERFACE FINAL PENDENTE. Nao e esquema de fiacao liberado.\nPlacas e rede de referencia sem ajuste EM novo; antena original preservada.',ha='center',fontsize=10,color='#9b421e')
fig.subplots_adjust(left=.06,right=.98,top=.90,bottom=.12,wspace=.13)
fig.savefig(dest/'imagens/distribuicao_dez_1x4.png',dpi=170);plt.close(fig)
g=json.loads((local/'geometria.json').read_text());fig,ax=plt.subplots(figsize=(5.5,9));ax.set_facecolor('#e3efef')
for pol,coords in g['copper'].items():
    ax.fill([p[0] for p in coords],[p[1] for p in coords],color='#be8b32')
for name,x,y in g['ports']:
    ax.add_patch(plt.Circle((x,y),.525,color='white'));ax.text(x+.7,y+1.3,name,fontsize=8)
for x,y in g['montagem_furos']:ax.add_patch(plt.Circle((x,y),1.6,fc='white',ec='black'))
ax.set_xlim(-19.5,19.5);ax.set_ylim(-39,39);ax.set_aspect('equal');ax.set_xlabel('X local (mm)');ax.set_ylabel('Y local (mm)')
ax.set_title('Referencia existente: dois divisores 1:4\nZYF300CA-C 1,52 mm; Cu 35 um\n39 x 78 mm; replicar em 5 posicoes',fontsize=11)
fig.text(.5,.025,'W100 = 1,004 mm; L inicial = 9,769 mm\nVSWR ~1,54 em 5,17 GHz: ajuste pendente',ha='center',fontsize=10)
fig.tight_layout(rect=(0,.08,1,1));fig.savefig(dest/'imagens/pcb_referencia_1x4.png',dpi=170);plt.close(fig)
print(json.dumps(dict(pasta=str(dest),pcbs=5,divisores=10,saidas=32,portas_radiantes=64,interface_pendente=True)))
