"""Fator de arranjo ideal: diagnostico de espacamento, nao resultado HFSS."""
from pathlib import Path
import json
import numpy as np
from scipy.signal import find_peaks
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path('D:/dev/EMBRAER/P2M21/R11_Divisor_Ajustes')
wave=299792458/5.17e9*1000
theta=np.linspace(-90,90,36001)
rows=[]
fig,ax=plt.subplots(figsize=(9,5.5))
for pitch in [36.,40.,42.,44.,48.]:
    x=np.array([-1.5,-.5,.5,1.5])*pitch
    af=np.mean(np.exp(2j*np.pi*x[None,:]/wave*np.sin(np.deg2rad(theta))[:,None]),axis=1)
    db=20*np.log10(np.maximum(abs(af),1e-8))
    positive=theta>=0
    cross=np.flatnonzero(positive & (db<=-3))[0]
    hpbw=2*np.interp(-3,[db[cross],db[cross-1]],[theta[cross],theta[cross-1]])
    pk,_=find_peaks(db)
    sides=[i for i in pk if theta[i]>1e-3]
    strongest=max(sides,key=lambda i:db[i])
    null=np.rad2deg(np.arcsin(wave/(4*pitch)))
    outside=(abs(theta)>null)
    rows.append(dict(passo_mm=pitch,passo_lambda=pitch/wave,abertura_3dB_graus=hpbw,
        SLL_maximos_locais_dB=float(db[strongest]),angulo_primeiro_lobulo_graus=float(theta[sides[0]]),
        maximo_fora_lobo_incluindo_90graus_dB=float(max(db[outside]))))
    ax.plot(theta,db,label=f'{pitch:g} mm ({pitch/wave:.3f} λ)',lw=1.4)
ax.set(xlim=(-90,90),ylim=(-35,1),xlabel='Elevação (graus)',ylabel='Fator de arranjo normalizado (dB)')
ax.grid(alpha=.25);ax.legend(ncol=2)
ax.set_title('Quatro fontes ideais iguais e em fase — 5,17 GHz\nSem radiadores, rede, refletor, perdas ou acoplamento')
fig.tight_layout();fig.savefig(ROOT/'espacamento_ideal.png',dpi=160);plt.close(fig)
data=dict(metodo='AF(theta) = mean(exp(j*2*pi*x*sin(theta)/lambda)); quatro fontes pontuais iguais em fase.',
    comprimento_onda_mm=wave,resultados=rows,
    limite='Estimativa analitica do fator de arranjo. Nao prediz ganho, VSWR ou SLL do modulo real e nao substitui HFSS.')
(ROOT/'espacamento_ideal.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(data,ensure_ascii=False,indent=2))
