"""Compara resultados reais, sem criar nova solução ou inferir convergência."""
from pathlib import Path
import csv,json,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'automacao/r05'))
from rede_carregada import read_pattern
WORK=Path('D:/dev/EMBRAER/P2M19');OUT=WORK/'Campanha_72mm_20261113'
NAMES=['R01_16x2_88mm','R02_16x2_72mm','R03_72mm_ref162','R04_72mm_ref146']

def main():
    data=[]
    for name in NAMES:
        root=WORK/name
        if not (root/'resultado.json').exists():continue
        r=json.loads((root/'resultado.json').read_text());cfg=json.loads((root/'configuracao.json').read_text())
        h=r['cortes']['H'];v=r['cortes']['V'];f=r['cortes_finos']
        row=dict(caso=name,passo_mm=cfg['passo_horizontal_mm'],refletor_mm=cfg['refletor_mm'][0],
            ganho_frontal_dBi=h['ganho_frontal_dBi'],H_graus=f['H']['abertura_graus'],V_graus=f['V']['abertura_graus'],
            maximo_H_graus=f['H']['pico_interpolado_graus'],maximo_V_graus=f['V']['pico_interpolado_graus'],
            SLL_H_dB=h['SLL']['nivel_dB'],SLL_V_dB=v['SLL']['nivel_dB'],VSWR_ativo_max=max(r['VSWR_ativo']),
            delta_s=r['delta_s'],passes=r['passes'],convergiu=r['convergiu'],fisica_ok=r['fisica_ok'],
            campos_estaveis=r['estavel_nove_sondas'],validado=r['validado_numericamente'],
            potencia_aceita_W=r['balanco_potencia']['aceita_W'],potencia_radiada_W=r['balanco_potencia']['radiada_W'])
        row['delta_G_ultimo_passe_dB']=r['historico_cache'][-1]['campos_dBi']['P2M19_Campo_00']-r['historico_cache'][-2]['campos_dBi']['P2M19_Campo_00']
        row['delta_campo_ultimo_passe_dB']=r['historico_cache'][-1]['delta_campo_max_dB']
        row['lobos_H']=h['SLL']['lobos'];row['lobos_V']=v['SLL']['lobos'];data.append(row)
    assert len(data)>=2,'Aguardar ao menos a R02'
    (OUT/'comparacao.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    columns=[k for k in data[0] if not k.startswith('lobos_')]
    with (OUT/'comparacao.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,columns,extrasaction='ignore');writer.writeheader();writer.writerows(data)
    labels=[f"{d['caso'].split('_')[0]}: colunas {d['passo_mm']:g} / refletor {d['refletor_mm']:g} mm" for d in data]
    colors=['#6f7785','#1167b1','#e67e22','#16845b']
    curves={}
    for d in data:
        curves[d['caso']]={}
        for axis in 'HV':
            t,e=read_pattern(WORK/d['caso']/('ALL_'+axis+'.csv'))
            curves[d['caso']][axis]=(t,10*np.log10(np.sum(abs(e)**2,axis=1)))
    fig,axes=plt.subplots(1,2,figsize=(13,5.8))
    for ax,axis in zip(axes,'HV'):
        for i,d in enumerate(data):
            t,g=curves[d['caso']][axis];ax.plot(t,g,label=labels[i],color=colors[i],lw=1.6,ls='--' if i==0 else '-')
        ax.set(xlim=(-90,90),ylim=(-20,25),xlabel='Angulo (graus)',ylabel='Ganho realizado total (dBi)',title='Horizontal' if axis=='H' else 'Vertical')
        ax.grid(alpha=.25);ax.legend(fontsize=8,loc='lower left')
    fig.suptitle('P2M19 — 5,17 GHz — 16 entradas iguais e em fase\nConvergencia e estabilidade devem ser verificadas por caso; curvas nao implicam validacao',fontsize=12)
    fig.tight_layout(rect=(0,0,1,.88));fig.savefig(OUT/'comparacao_HV.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,7),subplot_kw={'projection':'polar'})
    for ax,axis in zip(axes,'HV'):
        for i,d in enumerate(data):
            t,g=curves[d['caso']][axis];ax.plot(np.deg2rad(t),10**((g-g.max())/20),label=labels[i],color=colors[i],lw=1.4,ls='--' if i==0 else '-')
        ax.set_theta_zero_location('N');ax.set_theta_direction(-1);ax.set_ylim(0,1.05);ax.set_rticks([.25,.5,.75,1]);ax.set_rlabel_position(75)
        ax.set_title(('H' if axis=='H' else 'V')+' — E/Emax',pad=24)
    handles,ls=axes[0].get_legend_handles_labels();fig.legend(handles,ls,loc='lower center',ncol=2,fontsize=9)
    fig.suptitle('P2M19 — comparacao polar em 5,17 GHz\nCada curva normalizada pelo proprio pico; resultados sem convergencia sao preliminares')
    fig.subplots_adjust(top=.77,bottom=.18,wspace=.3);fig.savefig(OUT/'comparacao_polar_HV.png',dpi=180);plt.close(fig)
    lines=['# P2M19 — 72 mm versus 88 mm e ajustes do refletor','',
        'Estudo em 5,17 GHz, 16 niveis × duas colunas, 32 radiadores e 16 portas de 0,0625 W / 0°. Cada caso usa 14 nucleos, no maximo seis passes, alvo ΔS 0,05 e nenhum sweep.',
        '', 'A R02 altera apenas o espacamento entre colunas de 88 para 72 mm e reposiciona os furos correspondentes. Mantem o refletor de 178 × 776 × 2 mm, PCBs C12, altura 14,949 mm, materiais, portas e setup. R03/R04 reduzem apenas a largura do refletor para 162/146 mm. As placas ficam com 2 mm entre bordas.',
        '', '| Caso | Colunas / refletor (mm) | G frontal (dBi) | H / V (°) | SLL H / V (dB) | ΔS / passes | Convergiu? |',
        '|---|---:|---:|---:|---:|---:|---|']
    for d in data:
        lines.append(f"| {d['caso']} | {d['passo_mm']:g} / {d['refletor_mm']:g} | {d['ganho_frontal_dBi']:.4f} | {d['H_graus']:.3f} / {d['V_graus']:.3f} | {d['SLL_H_dB']:.3f} / {d['SLL_V_dB']:.3f} | {d['delta_s']:.6f} / {d['passes']} | {'Sim' if d['convergiu'] else '**Nao**'} |")
    if len(data)==4:
        candidates=data[1:]
        lines[2:2]=[
            '**Lote concluido: tres geometrias novas, seis passes em cada uma. Nenhuma convergiu nem confirmou estabilidade completa dos campos.** A referencia de 88 mm tambem e preliminar.', '',
            f"Com 72 mm, os ganhos calculados ficaram entre {min(d['ganho_frontal_dBi'] for d in candidates):.2f} e {max(d['ganho_frontal_dBi'] for d in candidates):.2f} dBi, mas isso ainda nao valida a meta de 19 dBi. A abertura H ficou entre {min(d['H_graus'] for d in candidates):.2f} e {max(d['H_graus'] for d in candidates):.2f} graus; nenhum caso chegou a 30 graus.", '',
            'Na comparacao direta com refletor de 178 mm, reduzir as colunas para 72 mm alargou numericamente o lobulo principal H e reduziu os lobulos horizontais. Reduzir depois o refletor para 162/146 mm trouxe pequenas diferencas adicionais e estreitou um pouco H. Nao se escolheu uma geometria como validada com base nessas diferencas.', '',
        ]
    lines+=['','H/V sao larguras de meia potencia do lobulo principal, nao cobertura angular total. SLL e o maior lobulo secundario do hemisferio frontal, relativo ao pico do proprio corte. Um lobulo secundario forte pode formar outra regiao acima de −3 dB.',
        '', '**Nenhum resultado sem convergencia pode ser promovido a validado por apresentar ganho alto.** A referencia de 88 mm tambem nao convergiu. Diferencas pequenas podem conter erro numerico; a tabela nao prova uma melhoria fisica quando a malha ainda varia.',
        '', '![Comparacao dos cortes H/V](comparacao_HV.png)','', '![Comparacao polar E/Emax](comparacao_polar_HV.png)',
        '', '## Escopo e automacao','',
        'Fila local finita, sem agendamento recorrente do chat. Acompanha o processo existente, impede solves concorrentes e executa os dois ajustes geometricos preparados. Interrompe por erro do solver, reparo Major ou auditoria fisica invalida. Caso sem convergencia permanece exploratorio; nao recebe passes adicionais. O arquivo PARAR_APOS_CASO no diretorio da campanha impede o proximo inicio.',
        '', 'Inclui acoplamento e perdas dos divisores impressos, RO4350B, cobre e ENIG. Sem rede externa, cabos em 3D, conectores N, radome ou suportes plasticos. A abertura proxima de 30° e aceitavel conforme orientacao do usuario, sem tolerancia numerica de aprovacao inventada. A vertical e informativa.',
        '', '## Diferencas frente a R01','', '| Caso | ΔG (dB) | ΔH (°) | ΔV (°) | ΔSLL H (dB) | ΔSLL V (dB) |','|---|---:|---:|---:|---:|---:|']
    base=data[0]
    for d in data[1:]:
        differences=[d[k]-base[k] for k in ['ganho_frontal_dBi','H_graus','V_graus','SLL_H_dB','SLL_V_dB']]
        lines.append('| '+d['caso']+' | '+' | '.join(f'{v:+.4f}' for v in differences)+' |')
    lines+=['','Nos niveis de lobulos secundarios, ΔSLL negativo representa reducao relativa ao pico. A configuracao sera escolhida considerando tambem ganho, casamento e confiabilidade numerica, nao apenas a largura H.']
    lines+=['','## Apontamento, lobulos e casamento','',
        '| Caso | Maximo H / V (graus) | VSWR ativo maximo | Sondas de campo estaveis? | Validado numericamente? |',
        '|---|---:|---:|---|---|']
    for d in data:
        lines.append(f"| {d['caso']} | {d['maximo_H_graus']:+.3f} / {d['maximo_V_graus']:+.3f} | {d['VSWR_ativo_max']:.4f} | {'Sim' if d['campos_estaveis'] else 'Nao'} | {'Sim' if d['validado'] else '**Nao**'} |")
    lines+=['','Maiores lobulos secundarios no hemisferio frontal, ordenados por nivel em cada corte. Angulos usam 0 graus na frente do refletor; H varia ao longo das colunas e V ao longo dos 16 niveis.',
        '', '| Caso | Corte | Angulo (graus) | Nivel relativo (dB) |', '|---|---|---:|---:|']
    for d in data:
        for axis in 'HV':
            for lobe in sorted(d['lobos_'+axis],key=lambda p:p['nivel_dB'],reverse=True)[:3]:
                lines.append(f"| {d['caso']} | {axis} | {lobe['angulo_graus']:+.2f} | {lobe['nivel_dB']:.3f} |")
    lines+=['','## Potencia e rastreabilidade','',
        '| Caso | Incidente (W) | Aceita (W) | Radiada (W) | Balanco e passividade consistentes? |',
        '|---|---:|---:|---:|---|']
    for d in data:
        lines.append(f"| {d['caso']} | 1,000000 | {d['potencia_aceita_W']:.6f} | {d['potencia_radiada_W']:.6f} | {'Sim' if d['fisica_ok'] else '**Nao**'} |")
    lines+=['','A consistencia fisica e necessaria, mas nao substitui a convergencia. Os nativos, S16, campos complexos por porta e auditorias de cada caso estao nas subpastas correspondentes. Os campos individuais recompostos devem reproduzir a excitacao simultanea.']
    lines+=['','| Caso | Variacao G frontal no ultimo passe (dB) | Maior variacao das nove sondas no ultimo passe (dB) |', '|---|---:|---:|']
    for d in data:
        lines.append(f"| {d['caso']} | {d['delta_G_ultimo_passe_dB']:+.4f} | {d['delta_campo_ultimo_passe_dB']:.4f} |")
    lines+=['','Essas variacoes medem a evolucao numerica observada; nao sao intervalos estatisticos de incerteza. Diferencas de ganho entre geometrias menores que a variacao do ultimo passe exigem cautela especial.','']
    for d in data[1:]:
        lines.append(f"- [{d['caso']}](casos/{d['caso']}/README.md)")
    lines.append('- [Referencia R01 de 88 mm](../centro_16x2_88mm/README.md)')
    if len(data)==4:lines+=['','A fila local encerrou; nao ha nova geometria, passe adicional ou agendamento recorrente programado. O resultado e uma comparacao preliminar documentada, sem qualificacao de banda, rede externa ou ganho por entrada MIMO.']
    (OUT/'RELATORIO.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps([ {k:d[k] for k in ['caso','ganho_frontal_dBi','H_graus','V_graus','SLL_H_dB','SLL_V_dB','delta_s','convergiu']} for d in data],indent=2))
if __name__=='__main__':main()
