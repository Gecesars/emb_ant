"""Sensibilidade de fase usando S8 existente; previsao, nunca novo resultado HFSS."""
from pathlib import Path
import os,sys,json
import numpy as np
from scipy.interpolate import CubicSpline
from scipy.optimize import brentq,minimize_scalar
import skrf as rf
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'projetos/P2M21/automacao'))
sys.path.insert(0,str(REPO/'automacao/r05'))
from rede_carregada import read_pattern
ROOT=Path(os.environ['P2S13_DIV3_ROOT'])
ANT=Path('D:/dev/EMBRAER/P2S13/R06_Continuacao_Tres2')
names=['R1_A','R1_B','R2_A','R2_B','R3_A','R3_B']
sd=rf.Network(str(ROOT/'divisor_ordenado.s8p')).s[0]
sa=rf.Network(str(ANT/'centro.s6p')).s[0]
theta=read_pattern(ANT/'ALL_V.csv')[0]
ef=np.stack([read_pattern(ANT/(n+'_V.csv'))[1] for n in names],axis=-1)
field=CubicSpline(theta,ef,axis=0)
def waves(tilt):
    # Fases equivalentes no plano de saida; A/B de cada placa recebem a mesma correcao.
    phase=np.r_[0,0,tilt,tilt,0,0,-tilt,-tilt]
    d=np.exp(1j*np.deg2rad(phase));s=sd*d[:,None]*d[None,:]
    a=np.linalg.solve(np.eye(6)-s[2:,2:]@sa,s[2:,:2]@np.ones(2)/np.sqrt(2))
    s2=s[:2,:2]+s[:2,2:]@sa@np.linalg.solve(np.eye(6)-s[2:,2:]@sa,s[2:,:2])
    return s2,a
def slope(tilt):
    a=waves(tilt)[1];e=field(0)@a;de=field(0,1)@a
    return float(2*np.real(np.vdot(e,de)))
tilt=float(brentq(slope,-10,10))
def result(t):
    s,a=waves(t)
    gain=lambda x:10*np.log10(np.sum(abs(field(x)@a)**2))
    peak=minimize_scalar(lambda x:-gain(x),bounds=(-2,2),method='bounded')
    vs=lambda g:((1+abs(g))/(1-abs(g))).tolist()
    return dict(rampa_graus=t,pico_V_interpolado_graus=float(peak.x),ganho_frontal_dBi=float(gain(0)),
        ganho_pico_dBi=float(gain(peak.x)),VSWR_ativo=vs(s@np.ones(2)),VSWR_casado=vs(np.diag(s)),
        amplitude_dB=float(np.ptp(20*np.log10(abs(a)))),fase_graus=np.angle(a/a[2],deg=True).tolist(),
        assimetria_principal_max_dB=float(max(abs(gain(x)-gain(-x)) for x in np.linspace(0,4,81))))
cfg=json.loads((ROOT/'configuracao.json').read_text())
lam=cfg['lambda50_mm']
out=dict(atual_interpolado=result(0),previsao_fase=result(tilt),
    delta_comprimento_saidas_R1_R2_R3_mm=[-tilt*lam/360,0,tilt*lam/360],
    novo_solve=False,nota='Ajuste ideal de fase em S8: previsao para orientar geometria. Perdas, dispersao e descontinuidades de nova rota exigem HFSS. Pico interpolado nao equivale a nova grade angular exportada.')
(ROOT/'plano_centragem_vertical.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
