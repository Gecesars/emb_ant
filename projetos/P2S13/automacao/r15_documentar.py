"""Comparacao reproduzivel do casamento C09 com S8 real e Nexxim."""
from pathlib import Path
import os,json,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path('D:/dev/EMBRAER/P2S13/R15_Casamento_C09');CASE=Path(os.environ['P2S13_R15_CASE']);BASE=Path('D:/dev/EMBRAER/P2S13/R14_Compacto_Simetrico_SemRadome/c00')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
r=read(CASE/'circuito/resultado.json');nx=read(CASE/'circuito/verificacao_nexxim.json');assert nx['matriz_conferida'] and not nx['guia']
assert not r['nexxim_pendente']
cases=[('c00',BASE),('c01',ROOT/'c01')]+([(CASE.name,CASE)] if CASE.name!='c01' else [])
history=[(name,read(path/'circuito/resultado.json')) for name,path in cases]
cfg=read(CASE/'divisor/configuracao.json');old=read(BASE/'divisor/configuracao.json');q=cfg['parametros'];p=old['parametros']
fig,axs=plt.subplots(1,2,figsize=(9,8))
for ax,c,title in zip(axs,[old,cfg],['C09 inicial — c00','C09 ajustada — '+CASE.name]):
    ox,oy=c['board_origin'];bx,by=c['board'];ax.add_patch(plt.Rectangle((ox,oy),bx,by,facecolor='#e1e8dc',edgecolor='#344650'))
    for s in c['signals'].values():xy=np.array(s['exterior']);ax.fill(xy[:,0],xy[:,1],color='#bf843c')
    for port in c['portas']:
        ax.plot(port['x'],port['y'],'.',color='navy');ax.annotate(port['name'],(port['x'],port['y']),xytext=(2,3),textcoords='offset points',fontsize=7)
    ax.set_aspect('equal');ax.set(xlabel='X (mm)',ylabel='Y (mm)',title=title);ax.margins(.08)
fig.suptitle('Duas seções comuns aos seis ramais | mesmas conexões e comprimento total');fig.tight_layout();fig.savefig(ROOT/'layout_comparado.png',dpi=160);plt.close(fig)
fig,ax=plt.subplots(figsize=(8,4.7));x=np.arange(len(history));w=.28
for i,(pol,color) in enumerate([('A','#2476ab'),('B','#e59936')]):
    bars=ax.bar(x+(i-.5)*w,[v['VSWR_ativo'][i] for _,v in history],w,label='Entrada '+pol,color=color)
    for bar in bars:ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()-.025,f'{bar.get_height():.4f}',ha='center',va='top')
ax.axhline(1.25,color='#a52b35',ls='--',label='Meta 1,25');ax.set(xticks=x,xticklabels=[n for n,_ in history],ylabel='VSWR ativo',ylim=(1,1.9),title='Nexxim com os divisores HFSS e a antena S6\n5,17 GHz | 0,5 W / 0° em cada entrada');ax.legend();fig.tight_layout();fig.savefig(ROOT/'comparacao_VSWR.png',dpi=160);plt.close(fig)
ok=r['casamento_confirmado_HFSS_Nexxim'];lines=['# C09 — ajuste dos transformadores e confirmação HFSS/Nexxim','',
 '**'+('Casamento do conjunto confirmado em 5,17 GHz.' if ok else 'Casamento ainda não atende à meta.')+'** Versão selecionada: '+CASE.name+'.','',
 'O divisor foi recalculado no HFSS e seu S8 conectado no Nexxim ao S6 da antena formada por três placas de dois elementos. Mantidos dois sinais de 0,5 W / 0°, seis ramais iguais, cabos iguais de 134 mm somente no circuito, ausência de radome e nenhum sweep.','',
 '| Resultado com a antena conectada | Valor | Critério |','|---|---:|---:|',
 f"| VSWR ativo A / B | {r['VSWR_ativo'][0]:.5f} / {r['VSWR_ativo'][1]:.5f} | ≤1,25 |",
 f"| VSWR com outra entrada em 50 Ω | {r['VSWR_outra_casada'][0]:.5f} / {r['VSWR_outra_casada'][1]:.5f} | Informativo |",
 f"| Ganho frontal realizado total | {r['cortes']['H']['ganho_frontal_dBi']:.4f} dBi | ≥12 dBi |",
 f"| Abertura H / V | {r['cortes']['H']['abertura_graus']:.3f}° / {r['cortes']['V']['abertura_graus']:.3f}° | Abertura H≈100° ainda pendente |",
 f"| Máximo H / V | {r['cortes']['H']['pico_graus']:+.3f}° / {r['pico_V_fino_graus']:+.4f}° | V: 0° ±0,5° |",
 f"| H(0°) abaixo do máximo | {r['queda_H_0_vs_pico_dB']:.7f} dB | ≤0,5 dB |",
 f"| Assimetria principal V | {r['assimetria_principal_V_dB']:.4f} dB | Referência 0,2 dB |",'',
 '![Diagramas H/V]('+CASE.name+'/circuito/polar_HV.png)','','## Dimensões e simetria','',
 '| Dimensão comum aos seis ramais | c00 | '+CASE.name+' |','|---|---:|---:|']
for key in ['W1_mm','W2_mm','L1_mm','L2_mm','comprimento_por_ramal_mm']:lines.append(f'| {key} | {p[key]:.6f} | {q[key]:.6f} |')
lines+=['','PCB preservada em 36 × 78 mm, ZYF300CA-C de 1,52 mm (εr=2,94, tanδ=0,0016), cobre 35 µm e ENIG nominal. Somente Sinal_A e Sinal_B mudaram: as 50 outras peças do divisor, os oito terminais, as posições de solda e os cabos foram preservados. A divisão entre as duas seções mudou igualmente nos seis caminhos. Igualdade elétrica nominal significa mesmos materiais, larguras e comprimentos; as fases reais são verificadas no S8.','',
 '![Transformadores antes e depois](layout_comparado.png)','','## Confirmação de circuito e convergência','',
 '| Variante HFSS ligada no Nexxim | VSWR A | VSWR B | Passes do divisor | ΔS |','|---|---:|---:|---:|---:|']
for name,v in history:lines.append(f"| {name} | {v['VSWR_ativo'][0]:.5f} | {v['VSWR_ativo'][1]:.5f} | {v['convergencia']['divisor']['passes']} | {v['convergencia']['divisor']['delta_s']:.7f} |")
lines+=['','![Evolução do casamento](comparacao_VSWR.png)','',
 f"O divisor selecionado convergiu em {r['convergencia']['divisor']['passes']} passes, ΔS {r['convergencia']['divisor']['delta_s']:.7f}, com dois passes consecutivos abaixo de 0,05. Todos os passes usaram 14 núcleos, solver direto e Classic com elementos curvilíneos. A auditoria verificou importação CAD, passividade, reciprocidade e ausência de reparos Major. Não houve passes além de seis em nenhum candidato.",'',
 f"O Nexxim foi realmente executado, com duas fontes de igual potência/fase, oito blocos Touchstone e seis interligações iguais. A matriz S2 exportada confere com a conexão independente por ondas complexas: erro máximo {nx['erro_absoluto_max']:.3g}. As matrizes usadas aqui são do novo HFSS; os modelos de linhas calibrados ficam separados como guias, sem valor de confirmação EM.",'',
 '**Condição da antena reutilizada:** geometria, S6 e campos da R14 foram preservados por SHA-256. A antena já tinha seis passes e ΔS 0,0243789; não foi recalculada nesta sintonia do divisor. Seus campos ainda variaram 0,309 dB no último passe. Portanto o casamento do circuito pode ser confirmado, mas ganho e diagramas permanecem preliminares e a aprovação RF completa da antena não está sendo declarada. A abertura H continua inferior aos aproximadamente 100° desejados.','',
 '## Divisor isolado e conjunto carregado','',
 'O ajuste foi feito para a carga real da antena através dos cabos. Ele não transforma este divisor em um componente genericamente casado a 50 Ω em todas as portas. A trifurcação não tem resistores de isolação.','',
 '| Saídas terminadas em 50 Ω | VSWR de entrada | Dispersão de amplitude | Dispersão de fase |','|---|---:|---:|---:|']
for pol,d in r['divisor_casado'].items():lines.append(f"| {pol} | {d['VSWR']:.4f} | {d['dispersao_amplitude_dB']:.4f} dB | {d['dispersao_fase_graus']:.4f}° |")
po=r['potencia']
lines+=['',f"Balanço para 1 W incidente: refletido {po['refletida_W']:.6f} W, perda no divisor {po['perda_divisor_W']:.6f} W, perda nos cabos {po['perda_cabos_W']:.6f} W, aceito na antena {po['aceita_antena_W']:.6f} W. O último termo inclui dissipação e radiação da antena.",'',
 f"Cabos: 134 mm físicos, 133,82 mm entre planos EM; os 0,18 mm finais de terminal estão no S6. A linha RLGC usa cobre/PTFE nominal e perde {r['cabo']['perda_insercao_dB']:.4f} dB por caminho. Não inclui radiação dos cabos, acoplamento espacial divisor–antena, conectores N ou tolerâncias de fabricação. Não houve simulação de banda.",'',
 '## Montagem atualizada','',
 'Somente as duas trilhas do divisor foram alteradas no conjunto de 122 sólidos. A montagem mecânica continua preliminar; os cabos aparecem no CAD, mas não no modelo HFSS.','',
 '![Montagem ajustada]('+CASE.name+'/visual/montagem_isometrica.png)','','![Divisor na traseira]('+CASE.name+'/visual/montagem_traseira.png)','',
 '## Arquivos','',
 '[HFSS divisor]('+CASE.name+'/divisor/Divisor_Duplo3.aedt) · [Nexxim com arquivos externos]('+CASE.name+'/circuito/C09_Ajuste_Nexxim_sem_malhas.aedtz) · [Resultados]('+CASE.name+'/circuito/resultado.json) · [Auditoria]('+CASE.name+'/divisor/auditoria_em.json)','',
 '[Antena HFSS preservada](../compacto_c09/c00/antena/PCB_SemCabos.aedt) · [Montagem FreeCAD]('+CASE.name+'/visual/Antena_C09_Ajustada_PRELIMINAR.FCStd)','',
 'Os nativos e exportações compactas estão no pacote, sem malhas ou campos volumétricos. Os arquivos do estudo inicial foram preservados. Ainda não foram gerados novos Gerbers desta sintonia.','']
(ROOT/'README.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
(ROOT/'selecionado.json').write_text(json.dumps(dict(caso=CASE.name,casamento_confirmado=ok,metodo='HFSS separado e Nexxim; antena R14 preservada',VSWR_ativo=r['VSWR_ativo']),indent=2)+'\n',encoding='utf-8')
print('RELATORIO_R15',CASE.name)
