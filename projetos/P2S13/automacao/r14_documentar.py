"""Relatorio rastreavel da simulacao HFSS separada e circuito Nexxim C09."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT=Path('D:/dev/EMBRAER/P2S13/R14_Compacto_Simetrico_SemRadome/c00')
OUT=ROOT/'circuito'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
r=read(OUT/'resultado.json');nx=read(OUT/'verificacao_nexxim.json')
assert nx['matriz_conferida'] and not r['nexxim_pendente']
dc=read(ROOT/'divisor/configuracao.json');pp=dc['parametros']
fig,axs=plt.subplots(1,2,figsize=(12,6),subplot_kw={'projection':'polar'})
for ax,axis in zip(axs,'HV'):
    data=np.genfromtxt(OUT/('diagrama_'+axis+'.csv'),delimiter=',',skip_header=1)
    ax.plot(np.deg2rad(data[:,0]),data[:,2]);ax.set_theta_zero_location('N');ax.set_theta_direction(-1)
    ax.set_ylim(0,1.05);ax.set_rticks([.25,.5,.75,1]);ax.set_rlabel_position(70)
    peak=r['pico_V_fino_graus'] if axis=='V' else r['cortes'][axis]['pico_graus']
    ax.set_title('%s: %.2f° | pico %+.3f°'%(axis,r['cortes'][axis]['abertura_graus'],peak),pad=20)
fig.suptitle('C09 compacto — antena sem radome — 5,17 GHz\nDuas entradas 0,5 W / 0° | cabos iguais no circuito | E/Emax')
if not r.get('qualificado'):fig.text(.5,.88,'PRELIMINAR — conferir metas e estabilidade de campo no relatório',ha='center',color='#a44b00')
fig.text(.5,.025,'G frontal %.3f dBi | VSWR %.3f / %.3f | H(0) %.3f dB abaixo do pico'%(r['cortes']['H']['ganho_frontal_dBi'],*r['VSWR_ativo'],r['queda_H_0_vs_pico_dB']),ha='center')
fig.subplots_adjust(top=.72,bottom=.12,wspace=.24);fig.savefig(OUT/'polar_HV.png',dpi=170);plt.close(fig)
fig,ax=plt.subplots(figsize=(12,7));ax.set(xlim=(0,12),ylim=(0,7));ax.axis('off')
def block(x,y,w,h,text,color):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.07',facecolor=color,edgecolor='#29445c'))
    ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=11)
block(2,1.3,2,4.4,'DIVISOR C09\nS8 do HFSS\n\n2 × 1:3\n36 × 78 mm','#dae7f5')
block(9,1.3,2.6,4.4,'ANTENA\nS6 do HFSS\n\n3 placas × 2\nelementos\n\nSem radome','#dfebd9')
for pol,y in [('A',4.5),('B',2.5)]:
    ax.annotate('',xy=(2,y),xytext=(.9,y),arrowprops=dict(arrowstyle='->',lw=1.5))
    ax.text(.75,y,'IN '+pol+'\n0,5 W / 0°',ha='right',va='center',fontsize=10)
for i,name in enumerate(['R1 A','R1 B','R2 A','R2 B','R3 A','R3 B']):
    y=5.4-i*.76
    block(5.3,y-.2,2.1,.4,'Coaxial '+name,'#f8ebcd')
    ax.plot([4,5.3],[y,y],color='#29445c');ax.plot([7.4,9],[y,y],color='#29445c')
ax.text(6,6.55,'Nexxim — 5,17 GHz — duas entradas simultâneas e em fase',ha='center',fontsize=14,weight='bold')
ax.text(6,.62,'Seis linhas RLGC idênticas; cabos fora do HFSS\nComprimento físico 134 mm; entre planos de referência EM 133,82 mm',ha='center',fontsize=11)
fig.tight_layout();fig.savefig(OUT/'circuito_blocos.png',dpi=160);plt.close(fig)

lines=['# C09 compacto — HFSS separado e Nexxim','',
       '**Resultado em 5,17 GHz: '+('metas atendidas e blocos EM convergidos.' if r.get('qualificado') else 'estudo ainda não qualificado; ver reprovações abaixo.')+'**','',
       'Duas entradas de 0,5 W / 0°, seis radiadores em três PCBs de dois elementos. O radome foi retirado. Cada polarização usa um divisor 1:3 de duas seções, com os três ramais fisicamente iguais.','',
       '| Grandeza | Resultado | Meta |','|---|---:|---:|',
       f"| Ganho frontal realizado total | {r['cortes']['H']['ganho_frontal_dBi']:.4f} dBi | ≥12 dBi |",
       f"| VSWR ativo A / B | {r['VSWR_ativo'][0]:.4f} / {r['VSWR_ativo'][1]:.4f} | ≤1,25 |",
       f"| VSWR com outra entrada casada A / B | {r['VSWR_outra_casada'][0]:.4f} / {r['VSWR_outra_casada'][1]:.4f} | Informativo |",
       f"| Abertura H / V a −3 dB | {r['cortes']['H']['abertura_graus']:.3f}° / {r['cortes']['V']['abertura_graus']:.3f}° | Informativo |",
       f"| H(0°) abaixo do máximo global | {r['queda_H_0_vs_pico_dB']:.4f} dB | ≤0,5 dB |",
       f"| Direção do máximo V | {r['pico_V_fino_graus']:+.4f}° | 0° ±0,5° |",
       f"| Assimetria do lóbulo principal V | {r['assimetria_principal_V_dB']:.4f} dB | ≤0,2 dB (diagnóstico) |",'',
       'Metas individuais: '+', '.join(k+'='+('atende' if v else '**não atende**') for k,v in r['metas'].items())+'. A abertura horizontal também ficou abaixo dos aproximadamente 100° buscados no projeto; essa redução não deve ser confundida com melhoria de ganho sem contrapartida.','',
       '![Diagramas E/Emax](circuito/polar_HV.png)','',
       '## Circuito efetivamente calculado','',
       f"O Nexxim LNA calculou os oito blocos Touchstone: S8 do divisor, seis S2 de coaxial e S6 da antena. A matriz S2 exportada pelo Nexxim confere com a conexão independente por ondas de potência; erro absoluto máximo {nx['erro_absoluto_max']:.3g}. Não se substituiu a simulação Nexxim por uma simples soma de perdas.",'',
       '![Interligação dos blocos](circuito/circuito_blocos.png)','',
       'Os diagramas são recompostos dos campos complexos embutidos das seis portas da antena, usando as ondas incidentes obtidas no circuito carregado. A recomposição da excitação uniforme foi confrontada com o HFSS. Ganho total refere-se às duas entradas coerentes, 1 W incidente total; não é ganho MIMO por entrada.','',
       f"Os cabos são seis linhas RLGC iguais, com comprimento físico de 134 mm. O trecho entre planos de referência EM é {r['cabo']['comprimento_mm']:.2f} mm: os últimos 0,18 mm do acesso estão no modelo da antena. A perda nominal calculada de cada linha é {r['cabo']['perda_insercao_dB']:.4f} dB. Inclui cobre e PTFE nominal (εr={r['cabo']['eps_r']:.9f}, tanδ={r['cabo']['tand']:.9f}); não é um ensaio de cabo comercial. Não há cabos longos em 3D no HFSS.",'',
       '## Divisor e geometria','',
       f"PCB ZYF300CA-C de 1,52 mm, 36 × 78 mm, cobre de 35 µm. Todos os seis ramais possuem duas seções com comprimentos {pp['L1_mm']:.6f} e {pp['L2_mm']:.6f} mm, larguras {pp['W1_mm']:.6f} e {pp['W2_mm']:.6f} mm. Comprimento total por ramal {pp['comprimento_por_ramal_mm']:.6f} mm. A mesma sequência de materiais e dimensões define a igualdade elétrica nominal; as fases reais estão medidas abaixo.",'',
       '| Saídas em 50 Ω | VSWR de entrada | Perda excedente | Dispersão de amplitude | Dispersão de fase |',
       '|---|---:|---:|---:|---:|']
for pol,d in r['divisor_casado'].items():
    lines.append(f"| {pol} | {d['VSWR']:.4f} | {d['perda_excedente_dB']:.4f} dB | {d['dispersao_amplitude_dB']:.4f} dB | {d['dispersao_fase_graus']:.4f}° |")
lines+=['',f"As trifurcações não possuem resistores de isolação. O maior acoplamento entre saídas da mesma polarização, com outras portas casadas, é {r['divisor_casado']['A']['maior_acoplamento_entre_saidas_dB']:.2f} dB (A) e {r['divisor_casado']['B']['maior_acoplamento_entre_saidas_dB']:.2f} dB (B). Por isso o casamento e o equilíbrio carregados são calculados com a matriz S6 completa da antena, incluindo reflexões entre blocos.",
        '','![Layout C09](divisor/layout.png)','','## Convergência e potência','',
        '| Bloco HFSS | Passes | ΔS atingido | Convergência |','|---|---:|---:|---|']
for name,c in r['convergencia'].items():lines.append(f"| {name} | {c['passes']} | {c['delta_s']:.7f} | {'Sim' if c['convergiu'] else '**Não**'} |")
p=r['potencia']
lines+=['','Limite de seis passes por bloco, ΔS alvo 0,05 e dois passes consecutivos; 14 núcleos confirmados no perfil. Classic com elementos curvilíneos e solver direto, sem sweep e sem operações locais de refinamento. Encerrar no limite não equivale a convergir.','',
        'As nove direções de campo são apenas monitoradas. Os dois últimos máximos de variação são '+' / '.join('%.4f'%v for v in r['campos_monitorados']['ultimos_deltas_max_dB'])+' dB; referência de estabilidade 0,1 dB. Este monitor não autoriza passes adicionais nem modifica o critério ΔS pedido.','',
        f"Balanço para 1 W incidente: refletido {p['refletida_W']:.6f} W, perda no divisor {p['perda_divisor_W']:.6f} W, perda nos cabos {p['perda_cabos_W']:.6f} W e potência aceita pela antena {p['aceita_antena_W']:.6f} W. Esta última ainda inclui perdas/radiação da própria antena; não é toda potência radiada.",'',
        'Matrizes passivas/recíprocas, ausência de reparos Major e potência uniforme HFSS verificadas nas auditorias EM. A ausência de reparos não significa ausência de todos os avisos locais do mesher; eles foram conservados nas auditorias.','',
        '## Limites e arquivos','',r['limites'].rstrip('.')+'. Apenas o ponto central foi calculado. Não há comprovação da banda de 5,09–5,25 GHz nem validação experimental.','',
        '[Nexxim nativo](circuito/C09_Antena_Nexxim.aedt) · [Arquivo Nexxim com Touchstones](circuito/C09_Antena_Nexxim_sem_malhas.aedtz) · [Resultados](circuito/resultado.json) · [Verificação Nexxim](circuito/verificacao_nexxim.json)','',
        '[HFSS divisor](divisor/Divisor_Duplo3.aedt) · [HFSS antena](antena/PCB_SemCabos.aedt) · [FreeCAD montagem preliminar](visual/Antena_C09_SemRadome_PRELIMINAR.FCStd)','',
        '![Montagem traseira](visual/traseira.png)','','![Placas radiantes](visual/frente.png)','',
        'A montagem FreeCAD continua aberta. KiCad/Gerbers C08 anteriores permanecem históricos; ainda não há Gerbers C09 liberados. Cabos aparecem somente no CAD mecânico e no circuito. O pacote Git contém nativos e exportações compactas, sem malhas ou campos volumétricos; abrir o HFSS do Git não restaura uma solução volumétrica salva.','']
(ROOT/'README.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
print('RELATORIO_C09_GERADO')
