"""Compara resultados reais a 5.17 GHz; nao calcula nem interpola banda."""
from pathlib import Path
import json,csv,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'automacao/r05'))
from rede_carregada import read_pattern
WORK=Path('D:/dev/EMBRAER/P2M21');OUT=WORK/'comparacao_colunas_niveis'
cases=[('R14_Oito_Celulas','8 placas / 72 mm / 6 passes'),('R15_Oito_Celulas_8passes','8 placas / 72 mm / 8 passes'),('R16_Oito_Celulas_78mm','8 placas / 78 mm'),('R17_Dez_Celulas_78mm','10 placas / 78 mm')]
def main():
    rows=[];curves={};results={}
    for folder,label in cases:
        root=WORK/folder;r=json.loads((root/'resultado.json').read_text());cfg=json.loads((root/'configuracao.json').read_text())
        assert r['frequencia_GHz']==5.17 and r['fisica_ok'] and cfg['sweep'] is False
        assert json.loads((root/'qualificacao.json').read_text())['estado']=='ANALISE_CONCLUIDA'
        results[folder]=r
        row=dict(versao=folder,placas=r['celulas'],portas=r['portas'],passo_horizontal_mm=cfg['passo_horizontal_mm'],passes=r['passes'],delta_s=r['delta_s'],convergiu=r['convergiu'],estavel_campo=r['estavel_nove_sondas'],validado=r['validado_numericamente'],ganho_frontal_dBi=r['cortes']['H']['ganho_frontal_dBi'],VSWR_ativo_max=max(v for v in r['VSWR_ativo'] if v is not None),VSWR_casado_max=max(v for v in r['VSWR_casado'] if v is not None))
        for a in 'HV':
            c=r['cortes'][a];row.update({f'abertura_{a}_graus':c['abertura_graus'],f'pico_{a}_graus':c['pico_graus'],f'SLL_{a}_dB':c['SLL']['nivel_dB']})
            t,e=read_pattern(root/('ALL_'+a+'.csv'));g=10*np.log10(np.sum(abs(e)**2,axis=1));curves[folder,a]=(t,g)
        rows.append(row)
    (OUT/'comparacao.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (OUT/'comparacao.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    colors=['#999999','#125fa3','#ca6916','#17854c']
    fig,axs=plt.subplots(1,2,figsize=(13,6))
    for a,ax in zip('HV',axs):
        for (folder,label),color in zip(cases,colors):
            t,g=curves[folder,a];ax.plot(t,g,label=label,color=color,lw=1.8 if 'R15' in folder else 1.3,ls='--' if 'R14' in folder else '-')
        ax.set(xlim=(-90,90),ylim=(-20,26),xlabel='Angulo (graus)',ylabel='Ganho realizado total (dBi)',title=('Horizontal — hemisferio frontal' if a=='H' else 'Vertical — hemisferio frontal'))
        ax.grid(alpha=.25);ax.legend(fontsize=8,loc='lower left')
    fig.suptitle('5,17 GHz — todas as entradas iguais e em fase — 1 W total\nComparacao de malha, separacao entre colunas e numero de placas')
    fig.text(.5,.025,'O SLL tabulado considera todo o hemisferio frontal. Conferir DeltaS e estabilidade antes de atribuir diferencas a geometria.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.05,1,.9));fig.savefig(OUT/'comparacao_HV.png',dpi=180);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(12,7),subplot_kw={'projection':'polar'})
    for a,ax in zip('HV',axs):
        for (folder,label),color in zip(cases[1:],colors[1:]):
            t,g=curves[folder,a];ax.plot(np.deg2rad(t),10**((g-g.max())/20),label=label,color=color,lw=1.4)
        ax.set_theta_zero_location('N');ax.set_theta_direction(-1);ax.set_ylim(0,1.05);ax.set_rticks([.25,.5,.75,1]);ax.set_rlabel_position(75);ax.set_title(a,pad=20)
    fig.suptitle('Diagramas polares E/Emax — 5,17 GHz\nCada curva normalizada pelo proprio maximo; ganho absoluto na tabela')
    fig.legend(*axs[0].get_legend_handles_labels(),loc='lower center',ncol=3,fontsize=9)
    fig.subplots_adjust(top=.80,bottom=.16,wspace=.28);fig.savefig(OUT/'polar_HV.png',dpi=180);plt.close(fig)
    def diff(i,j):
        return {k:rows[j][k]-rows[i][k] for k in ['ganho_frontal_dBi','SLL_H_dB','SLL_V_dB','abertura_H_graus','abertura_V_graus','VSWR_ativo_max']}
    contrasts=dict(malha6_para8=diff(0,1),colunas72_para78_contra8passes=diff(1,2),colunas72_para78_mesmo_limite6=diff(0,2),placas8_para10_em78mm=diff(2,3))
    (OUT/'diferencas.json').write_text(json.dumps(contrasts,indent=2)+'\n',encoding='utf-8')
    table='\n'.join('| '+' | '.join([x['versao'],str(x['passes']),f"{x['delta_s']:.6f}",'sim' if x['convergiu'] else 'nao',f"{x['ganho_frontal_dBi']:.3f}",f"{x['abertura_H_graus']:.3f}",f"{x['abertura_V_graus']:.3f}",f"{x['SLL_H_dB']:.3f}",f"{x['SLL_V_dB']:.3f}",f"{x['VSWR_ativo_max']:.3f}"])+' |' for x in rows)
    md=f'''# Comparacao das montagens modulares P2M21

Resultados **somente em 5,17 GHz**, sem sweep. Todas as conexoes recebem a mesma amplitude e fase: 16 × 0,0625 W nas oito placas; 20 × 0,05 W nas dez placas. Potencia incidente total de 1 W. Cada PCB conserva os quatro radiadores e os dois divisores 1:4 da C12. Os cabos fisicos de 50 mm e suas perdas nominais permanecem no modelo.

**O ganho realizado inclui as perdas dieletricas das PCBs e dos divisores impressos**, com RO4350B, nucleo de 0,76 mm, epsilon_r 3,66 e tan(delta) nominal 0,0037, alem das perdas metalicas, dos cabos modelados e do descasamento. **Nao inclui a futura rede externa que ligara duas entradas ao conjunto de placas.** A eficiencia total nao e uma medida isolada da perda dos divisores: agrega tambem antenas, cabos e descasamento.

| Versao | Passes | DeltaS | Convergiu | G frontal dBi | H graus | V graus | SLL H dB | SLL V dB | VSWR ativo max |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
{table}

As aberturas sao de meia potencia, os picos sao medidos na grade angular de 0,25 grau e o SLL e relativo ao pico do respectivo corte, fora dos primeiros minimos do lobo principal, no hemisferio frontal. Quanto mais negativo o SLL, menor o maior lobulo lateral. Nenhum destes resultados comprova uma entrada MIMO com rede externa de distribuicao.

![Comparacao H/V](comparacao_HV.png)

![Polar E/Emax](polar_HV.png)

## Continuidade e controles

R15 acrescentou exatamente os passes 7 e 8 a uma copia byte a byte da solucao R14: mesma geometria, materiais, portas, malha e cache; apenas minimo e maximo de passes passaram para oito. A prova inclui o historico dos seis passes anteriores. O criterio permanece DeltaS ≤0,05 por dois passes consecutivos. Nao atingir convergencia ou estabilidade de campo impede chamar o resultado de validado.

R16 aumenta o passo horizontal de 72 para 78 mm, mantendo quatro placas por coluna. A folga entre PCBs passa de 2 para 8 mm. A largura do refletor permanece em 162 mm; sua margem lateral passa de 10 para 7 mm. Os furos acompanham os cabos. R17 conserva 78 mm e acrescenta uma PCB por coluna: cinco placas, 20 niveis de radiadores e 40 radiadores. O refletor cresce de 776 para 968 mm na vertical, mantendo 162 × 2 mm nas outras dimensoes. A margem vertical permanece em 8 mm e o passo dos radiadores em 48 mm.

As novas geometrias usam Classic automatico, sem operacoes locais ou MeshLink, primeira ordem, alvo DeltaS 0,05, maximo de seis passes e 14 nucleos. A tabela inclui R14 com seis passes para explicitar a diferenca de orcamento numerico em relacao a R15 com oito. A troca automatica entre solver iterativo e direto, se ocorrer, consta de solver_efetivo.json de cada estudo. O cache de nove direcoes monitora estabilidade, sem acrescentar passes ao limite autorizado.

Os dados em comparacao.json, diferencas.json e os CSVs complexos permitem conferir ganho, fase, VSWR ativo e com demais portas casadas. As estimativas de fator de arranjo ficam separadas dos resultados FEM; nao substituem acoplamento e refletor do painel completo. Nenhum sweep foi executado. Arquivos de malha e resultados volumetricos permanecem somente locais.
'''
    (OUT/'README.md').write_text(md,encoding='utf-8',newline='\n');print(json.dumps(contrasts,indent=2))
if __name__=='__main__':main()
