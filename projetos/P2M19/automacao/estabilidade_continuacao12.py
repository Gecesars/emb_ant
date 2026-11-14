"""Compara campos reais dos passes 10, 11 e 12; nao extrapola diagramas."""
from pathlib import Path
import json,sys,csv,re
import numpy as np
import skrf as rf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from continuacao12_analisar import read_pattern,metrics,beam
from oito_celulas_monitorar import progress
ROOT=Path('D:/dev/EMBRAER/P2M19/R07_72mm_ref146_12passes')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
    cfg=read(ROOT/'configuracao.json');base=Path(cfg['referencia_comparacao']);cp=ROOT/'passe11'
    h=read(ROOT/'historico_passes.json')['historico'];ph=progress(cp)
    assert len(ph['historico'])==11 and ph['historico']==h[:11]
    save(cp/'historico_passes.json',ph)
    conv=(cp/'convergencia.txt').read_text();assert re.search(r'Completed\s*:\s*11\b',conv)
    network=rf.Network(str(cp/'centro.s16p'));assert network.nports==16 and len(network.f)==1 and network.f[0]==5.17e9
    np.testing.assert_allclose(network.z0,50);s=network.s[0]
    names=[name.strip().removesuffix(':1') for name in network.port_names]
    assert names==read(ROOT/'resultado.json')['ordem_portas']
    gamma=s@np.ones(16);vs=lambda v:((1+abs(v))/(1-abs(v))).tolist()
    accept=1-float(np.sum(abs(s@np.ones(16)/4)**2));power=read(cp/'potencia.json')
    pin=power['IncidentPower']['real'][0];pac=power['AcceptedPower']['real'][0];prad=power['RadiatedPower']['real'][0]
    assert abs(pin-1)<1e-6 and abs(pac-accept)<1e-4 and 0<prad<=pac+1e-3
    sigma=float(np.linalg.svd(s,compute_uv=False)[0]);recip=float(np.max(abs(s-s.T)))
    assert sigma<1.0001 and recip<1e-5 and np.max(abs(gamma))<1
    sources=re.findall(r'SourceEntry\([^\n]+',(cp/cfg['native']).read_text(errors='replace'))
    assert len(sources)==16 and all("Magnitude='0.0625W'" in row and "Phase='0deg'" in row for row in sources)
    r11=dict(passes=11,delta_s=ph['historico'][-1]['delta_s'],convergiu='Converged : Yes' in conv,
      VSWR_ativo=vs(gamma),VSWR_casado=vs(np.diag(s)),ordem_portas=names,cortes={},cortes_finos={},
      balanco_potencia=dict(incidente_W=pin,refletida_W=1-accept,aceita_W=pac,radiada_W=prad,dissipada_W=pac-prad),
      balanco_potencia_valido=True,maior_singular=sigma,reciprocidade=recip)
    rows=[];curves={};data={10:read(base/'resultado.json'),11:r11,12:read(ROOT/'resultado.json')}
    for num,folder in [(10,base),(11,cp),(12,ROOT)]:
        curves[num]={}
        for axis in 'HV':
            t,e=read_pattern(folder/('ALL_'+axis+'.csv'));g=10*np.log10(np.sum(abs(e)**2,axis=1));curves[num][axis]=(t,g)
            if num==11:
                r11['cortes'][axis]=metrics(t,g)
                tf,ef=read_pattern(folder/('ALL_'+axis+'_fino.csv'));gf=10*np.log10(np.sum(abs(ef)**2,axis=1))
                i=int(np.argmax(gf));assert 0<i<len(tf)-1;poly=np.polyfit(tf[i-1:i+2],gf[i-1:i+2],2)
                bw,lo,hi=beam(tf,gf);r11['cortes_finos'][axis]=dict(pico_interpolado_graus=float(-poly[1]/(2*poly[0])),abertura_graus=float(bw))
                assert abs(float(gf[np.argmin(abs(tf))])-r11['cortes'][axis]['ganho_frontal_dBi'])<=.001
        r=data[num];rows.append(dict(passe=num,delta_s=r['delta_s'],ganho_frontal_dBi=r['cortes']['H']['ganho_frontal_dBi'],
          H_graus=r['cortes_finos']['H']['abertura_graus'],V_graus=r['cortes_finos']['V']['abertura_graus'],
          pico_H_graus=r['cortes_finos']['H']['pico_interpolado_graus'],pico_V_graus=r['cortes_finos']['V']['pico_interpolado_graus'],
          SLL_H_dB=r['cortes']['H']['SLL']['nivel_dB'],SLL_V_dB=r['cortes']['V']['SLL']['nivel_dB'],
          VSWR_ativo_min=min(r['VSWR_ativo']),VSWR_ativo_max=max(r['VSWR_ativo']),VSWR_casado_max=max(r['VSWR_casado'])))
    assert abs(r11['cortes']['H']['ganho_frontal_dBi']-ph['historico'][-1]['campos_dBi']['P2M19_Campo_00'])<1e-6
    save(cp/'resultado.json',r11)
    changes=[]
    for n0,n1 in [(10,11),(11,12),(10,12)]:
        a,b=rows[n0-10],rows[n1-10]
        item=dict(de=n0,para=n1,diferencas={k:b[k]-a[k] for k in a if k not in ['passe','delta_s']},diagramas={})
        item['variacao_max_VSWR_ativo_por_porta']=float(np.max(abs(np.array(data[n1]['VSWR_ativo'])-data[n0]['VSWR_ativo'])))
        for axis in 'HV':
            t,g0=curves[n0][axis];tn,g1=curves[n1][axis];np.testing.assert_array_equal(t,tn)
            front=abs(t)<=90;norm0=g0-g0[front].max();norm1=g1-g1[front].max()
            e0=10**(norm0[front]/20);e1=10**(norm1[front]/20);delta=e1-e0
            bright=front&(norm0>=-20)&(norm1>=-20)
            item['diagramas'][axis]=dict(max_diferenca_E_Emax=float(np.max(abs(delta))),rms_diferenca_E_Emax=float(np.sqrt(np.mean(delta**2))),
              max_diferenca_normalizada_dB_acima_menos20=float(np.max(abs(norm1[bright]-norm0[bright]))))
        changes.append(item)
    out=dict(casos=rows,comparacoes=changes,criterio_monitoramento_sondas_dB=cfg['monitoramento_estabilidade_campo_dB'],
      criterio_sondas_dois_passes_atendido=data[12]['estavel_nove_sondas'],
      nota='Diferencas completas dos diagramas sao diagnosticos, sem tolerancia adicional inventada. E/Emax normalizado por corte no hemisferio frontal; diferencas em dB excluem pontos abaixo de -20 dB em qualquer um dos diagramas para nao amplificar nulos.')
    directions=[(0,90),(-10,90),(10,90),(-54,90),(54,90),(-1.75,0),(1.75,0),(-45,0),(45,0)]
    out['sondas_monitoradas']=[]
    for i,(theta,phi) in enumerate(directions):
        name='P2M19_Campo_%02d'%i
        values=[h[n-1]['campos_dBi'][name] for n in [10,11,12]]
        out['sondas_monitoradas'].append(dict(nome=name,theta_graus=theta,phi_graus=phi,
          ganho_dBi_10_11_12=values,delta_10_11_dB=values[1]-values[0],delta_11_12_dB=values[2]-values[1]))
    save(ROOT/'estabilidade_10_11_12.json',out)
    with (ROOT/'estabilidade_10_11_12.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    fig,axs=plt.subplots(2,2,figsize=(12,8))
    for col,axis in enumerate('HV'):
        for num,style in [(10,'--'),(11,'-.'),(12,'-')]:
            t,g=curves[num][axis];axs[0,col].plot(t,g,style,label=str(num)+' passes',lw=1.5)
            tf,ef=read_pattern(({10:base,11:cp,12:ROOT}[num])/('ALL_'+axis+'_fino.csv'));gf=10*np.log10(np.sum(abs(ef)**2,axis=1))
            axs[1,col].plot(tf,gf,style,label=str(num)+' passes',lw=1.5)
        axs[0,col].set(xlim=(-90,90),ylim=(-15,24),title=axis+' — hemisferio frontal',ylabel='Ganho realizado total (dBi)')
        axs[1,col].set(xlim=((-16,16) if axis=='H' else (-3,3)),ylim=(14,21.5),title=axis+' — lobulo principal',xlabel='Angulo (graus)',ylabel='Ganho realizado total (dBi)')
        for ax in axs[:,col]:ax.grid(alpha=.25);ax.legend(fontsize=8)
    fig.suptitle('P2M19 — estabilidade dos passes 10, 11 e 12\n5,17 GHz | 16 entradas iguais/em fase | mesma geometria e malha continuada')
    fig.tight_layout(rect=(0,0,1,.93));fig.savefig(ROOT/'estabilidade_HV_10_11_12.png',dpi=175);plt.close(fig)
    print(json.dumps(out,indent=2))
    return out
if __name__=='__main__':main()
