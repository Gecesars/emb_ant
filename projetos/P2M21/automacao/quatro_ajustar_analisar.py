"""Auditoria de variantes R11, com maior lobulo secundario frontal em elevacao."""
from pathlib import Path
import argparse,csv,json,re
import numpy as np
from scipy.signal import find_peaks
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from divisor_variantes_comparar import assess

ROOT=Path('D:/dev/EMBRAER/P2M21/R11_Divisor_Ajustes')
BASE=Path('D:/dev/EMBRAER/P2M21/R10_Quatro_Verticais')

def sidelobe(theta,gain):
    front=np.flatnonzero(abs(theta)<=90);pk=front[np.argmax(gain[front])]
    minima,_=find_peaks(-gain)
    left=max(i for i in minima if i<pk);right=min(i for i in minima if i>pk)
    maxima,_=find_peaks(gain)
    sides=[i for i in maxima if abs(theta[i])<=90 and (i<left or i>right)]
    strongest=max(sides,key=lambda i:gain[i])
    return dict(nivel_dB=float(gain[strongest]-gain[pk]),angulo_graus=float(theta[strongest]),
        limites_lobo_principal_graus=[float(theta[left]),float(theta[right])],
        lobos=[dict(angulo_graus=float(theta[i]),nivel_dB=float(gain[i]-gain[pk])) for i in sides],
        criterio='Maximos locais no hemisferio frontal, fora dos primeiros minimos que delimitam o lobo principal.')

def analyze(folder):
    r,curves=assess(folder);r.pop('validado',None)
    cfg=json.loads((folder/'configuracao.json').read_text())
    r.update(alvo_delta_s=cfg['max_delta_s'],SLL_V=sidelobe(*curves['V']),parametros=cfg.get('parametros',{}))
    r['espacamento_vertical_mm']=cfg['espacamento_vertical_mm']
    r['distancia_face_inferior_laminado_ao_refletor_mm']=cfg.get('distancia_face_inferior_laminado_ao_refletor_mm',16.61)
    native=(folder/cfg['native']).read_text(errors='replace')
    r['basis_order']=int(re.search(r'\bBasisOrder=(-?\d+)',native)[1])
    assert r['basis_order']==cfg.get('parametros',{}).get('basis_order',-1)
    for cut in r['cortes'].values():
        cut['diferenca_pico_frente_dB']=cut['ganho_pico_dBi']-cut['ganho_frontal_dBi']
    with (folder/'AB_H.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
    z=next(x for x in rows if float(x['Theta [deg]'])==0)
    gr,ga,di=[float(z[k]) for k in ['dB(RealizedGainTotal) []','dB(GainTotal) []','dB(DirTotal) []']]
    r['eficiencia_radiacao']=10**((ga-di)/10);r['eficiencia_total']=10**((gr-di)/10)
    r['erro_potencia_W']=abs(10**((gr-ga)/10)-r['potencia_aceita_W'])
    r['fisica_ok']=bool(r['passivo'] and r['major']==0 and r['residuo_reciprocidade']<.001 and r['eficiencia_radiacao']<=1.005 and r['erro_potencia_W']<.005)
    limit=1.3
    r['limite_VSWR_exclusivo']=limit
    r['metas']=dict(ganho12=gr>=12,VSWR_ativo=bool(max(r['VSWR_ativo'])<limit),VSWR_casado=bool(max(r['VSWR_casado'])<limit),maximos_zero_na_grade=r['centrado_na_grade_025grau'])
    r['aprovado']=bool(r['convergiu'] and r['fisica_ok'] and all(r['metas'].values()))
    # Integral aproximada de Ez entre retorno e sinal, apenas como diagnostico
    # relativo. Nao equivale a potencia entregue nem a ondas normalizadas.
    if (folder/'sondas_Real.fld').exists() and (folder/'sondas_Imag.fld').exists():
        arrays=[]
        for part in ['Real','Imag']:
            vals=[]
            for line in (folder/('sondas_'+part+'.fld')).read_text().splitlines():
                try:row=[float(x) for x in line.split()]
                except ValueError:continue
                if len(row)==4:vals.append(row)
            arrays.append(np.array(vals))
        if arrays[0].shape==arrays[1].shape==(168,4) and all(np.isfinite(a).all() for a in arrays):
            np.testing.assert_allclose(arrays[0][:,:3],arrays[1][:,:3])
            field=(arrays[0][:,3]+1j*arrays[1][:,3]).reshape(4,2,21)
            voltage=-np.trapezoid(field,dx=.75998/20/1000,axis=2)
            probe=[]
            for i in range(4):
                for j,pol in enumerate('AB'):
                    probe.append(dict(elemento=i+1,polarizacao=pol,modulo_V=float(abs(voltage[i,j])),fase_graus=float(np.angle(voltage[i,j],deg=True))))
            r['sondas_tensao_aproximada']=probe
            (folder/'sondas_resumo.json').write_text(json.dumps(dict(valores=probe,metodo='Integral trapezoidal de Ez em 21 pontos na espessura; fontes AB. Indicador relativo, nao potencia por radiador.'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (folder/'resultado.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    fig,axs=plt.subplots(1,2,figsize=(11,5.7))
    for ax,a in zip(axs,'HV'):
        t,g=curves[a];c=r['cortes'][a]
        ax.plot(t,g,lw=1.5);ax.axvline(0,color='gray',lw=.7);ax.axvline(c['pico_graus'],ls=':',c='#c05225')
        ax.set(xlim=(-90,90),ylim=(-20,16),xlabel='Angulo (graus)',ylabel='Ganho realizado total (dBi)',title=f"{a}: maximo {c['pico_graus']:+.2f}°; abertura {c['abertura_graus']:.2f}°")
        ax.grid(alpha=.25)
    status='convergiu' if r['convergiu'] else 'NAO CONVERGIDO'
    fig.suptitle(f"{folder.name} | 5,17 GHz | A=B=0,5 W / 0°\n{r['passes']} passes; DeltaS={r['delta_s']:.6f}; {status}")
    fig.text(.5,.025,f"G0={gr:.3f} dBi; VSWR ativo={r['VSWR_ativo'][0]:.3f}/{r['VSWR_ativo'][1]:.3f}; SLL V={r['SLL_V']['nivel_dB']:.2f} dB",ha='center')
    fig.tight_layout(rect=(0,.06,1,.90));fig.savefig(folder/'diagramas_HV.png',dpi=170);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(11,7),subplot_kw={'projection':'polar'})
    for ax,a in zip(axs,'HV'):
        t,g=curves[a];c=r['cortes'][a]
        ax.plot(np.deg2rad(t),10**((g-g.max())/20),lw=1.7)
        ax.set_theta_zero_location('N');ax.set_theta_direction(-1);ax.set_ylim(0,1.05)
        ax.set_rticks([.25,.5,.75,1]);ax.set_rlabel_position(75)
        ax.set_thetagrids(np.arange(0,360,30),['0°','30°','60°','90°','120°','150°','180°','−150°','−120°','−90°','−60°','−30°'])
        ax.set_title(f"{a}: maximo {c['pico_graus']:+.2f}° | abertura {c['abertura_graus']:.2f}°",pad=22,fontsize=10)
        ax.grid(alpha=.25)
    fig.suptitle(f"{folder.name} — 5,17 GHz — E/Emax\nA=B=0,5 W / 0°; {status}; DeltaS {r['delta_s']:.6f}",fontsize=12)
    fig.text(.5,.035,f"G0 {gr:.3f} dBi | VSWR ativo {r['VSWR_ativo'][0]:.3f}/{r['VSWR_ativo'][1]:.3f} | SLL V {r['SLL_V']['nivel_dB']:.2f} dB",ha='center')
    fig.subplots_adjust(top=.76,bottom=.17,wspace=.30);fig.savefig(folder/'polar_HV.png',dpi=170);fig.savefig(folder/'polar_HV.pdf');plt.close(fig)
    qp=folder/'qualificacao.json';q=json.loads(qp.read_text(encoding='utf-8'))
    if 'estado_exportacao' not in q:q['estado_exportacao']=q.get('estado')
    q.update(estado='AUDITADO_APROVADO' if r['aprovado'] else 'AUDITADO_PRELIMINAR_NAO_APROVADO',
        auditoria_concluida=True,resultado='resultado.json',convergiu=r['convergiu'],aprovado=r['aprovado'])
    qp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:r[k] for k in ['variante','passes','delta_s','convergiu','VSWR_ativo','VSWR_casado','cortes','SLL_V','fisica_ok','metas']},ensure_ascii=False,indent=2))
    return r

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('variant');a=p.parse_args()
    analyze(BASE if a.variant=='base' else ROOT/a.variant)
