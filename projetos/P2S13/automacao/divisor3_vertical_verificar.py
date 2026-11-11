"""Confere o pico vertical com campos HFSS reexportados a cada0.01grau."""
from pathlib import Path
import os,sys,json,csv,hashlib
import numpy as np
import skrf as rf
from scipy.interpolate import CubicSpline
from scipy.optimize import minimize_scalar
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'automacao/r05'))
from rede_carregada import read_pattern
ROOT=Path(os.environ['P2S13_DIV3_ROOT']);BASE=ROOT.parent;FINE=BASE/'antena_grade_fina'
ANT=Path('D:/dev/EMBRAER/P2S13/R06_Continuacao_Tres2')
names=['R1_A','R1_B','R2_A','R2_B','R3_A','R3_B']
sd=rf.Network(str(ROOT/'divisor_ordenado.s8p')).s[0]
sa=rf.Network(str(ANT/'centro.s6p')).s[0]
a=np.linalg.solve(np.eye(6)-sd[2:,2:]@sa,sd[2:,:2]@np.ones(2)/np.sqrt(2))
t,uniform=read_pattern(FINE/'ALL_V.csv');assert len(t)==401
ef=np.stack([read_pattern(FINE/(n+'_V.csv'))[1] for n in names],axis=-1)
np.testing.assert_allclose(ef@np.ones(6)/np.sqrt(6),uniform,rtol=1e-8,atol=1e-10)
tc=read_pattern(ANT/'ALL_V.csv')[0]
ec=np.stack([read_pattern(ANT/(n+'_V.csv'))[1] for n in names],axis=-1)
common=[(i,int(np.argmin(abs(tc-x)))) for i,x in enumerate(t) if abs(tc[np.argmin(abs(tc-x))]-x)<1e-8]
error=float(max(np.max(abs(ef[i]-ec[j])) for i,j in common))
relative_error=error/float(max(np.max(abs(ec[j])) for i,j in common))
gain_error=max(float(np.max(abs(10*np.log10(np.sum(abs(ef[i])**2,axis=0)/np.sum(abs(ec[j])**2,axis=0))))) for i,j in common)
# Reavaliar a esfera causa diferencas numericas sub-ppm; comparar grandezas
# relativas e ganho, nao um limiar absoluto arbitrario na escala de campo.
assert relative_error<1e-6 and gain_error<1e-5,(relative_error,gain_error)
g=10*np.log10(np.sum(abs(ef@a)**2,axis=1));gc=10*np.log10(np.sum(abs(ec@a)**2,axis=1))
i=int(np.argmax(g));i0=int(np.argmin(abs(t)));assert 0<i<len(t)-1 and abs(t[i])<1.9
assert abs(tc[np.argmax(gc)])<2
peak=minimize_scalar(lambda x:-float(CubicSpline(t,g)(x)),bounds=(t[i-1],t[i+1]),method='bounded')
curve=CubicSpline(tc,gc)
symx=np.linspace(0,4,401);sym=curve(symx)-curve(-symx)
r=json.loads((ROOT/'resultado.json').read_text())
left,right=r['cortes']['V']['cruzamentos_graus'];half=min(abs(left),abs(right))
mainx=np.linspace(0,half,401)
out=dict(frequencia_GHz=5.17,passo_angular_graus=.01,pico_V_grade_graus=float(t[i]),
    pico_V_interpolado_graus=float(peak.x),ganho_pico_dBi=float(g[i]),ganho_zero_dBi=float(g[i0]),
    diferenca_pico_zero_dB=float(g[i]-g[i0]),maximo_na_amostra_zero=bool(i==i0),
    assimetria_max_mais_menos4graus_dB=float(np.max(abs(sym))),
    assimetria_max_lobo_3dB_comum_dB=float(np.max(abs(curve(mainx)-curve(-mainx)))),
    intervalo_comum_lobo_3dB_graus=[-half,half],centro_cruzamentos_3dB_graus=(left+right)/2,
    SLL_V_dB=r['cortes']['V']['SLL']['nivel_dB'],erro_campos_grade_antiga=float(error),
    erro_relativo_campos_grade_antiga=relative_error,erro_ganho_grade_antiga_dB=gain_error,
    limites_conferencia_grade=dict(campo_relativo=1e-6,ganho_dB=1e-5),
    novo_solve_antena=False,S8_sha256=r['S8_sha256'],S6_sha256=r['S6_sha256'],
    nota='Grade angular mais fina da mesma solucao de campo, nao refinamento FEM; nao elimina as pendencias de convergencia da antena.')
(ROOT/'vertical_centro_fino.json').write_text(json.dumps(out,indent=2)+'\n')
with (ROOT/'vertical_centro_fino.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['theta_graus','ganho_total_realizado_dBi']);w.writerows(zip(t,g))
fig,axs=plt.subplots(1,2,figsize=(12,4.8))
axs[0].plot(tc,gc-g.max(),label='V real');axs[0].plot(tc[::-1],gc-g.max(),'--',lw=.9,label='V espelhado para comparação')
axs[0].set(xlim=(-90,90),ylim=(-35,1),xlabel='Ângulo vertical (°)',ylabel='Ganho relativo ao pico (dB)',title='Diagrama vertical completo');axs[0].legend(fontsize=8)
axs[1].plot(t,g-g.max());axs[1].axvline(0,color='k',lw=.8,ls='--');axs[1].scatter([t[i]],[0],s=18,color='crimson')
axs[1].set(xlim=(-1,1),ylim=(-.22,.015),xlabel='Ângulo vertical (°)',ylabel='Ganho relativo ao pico (dB)',title='Máximo %+.2f°; grade de 0,01°'%t[i])
for ax in axs:ax.grid(alpha=.25)
fig.suptitle('5,17 GHz — duas fontes de 0,5 W / 0° — divisor HFSS + antena S6\nPRELIMINAR | G(0°) %.3f dBi | VSWR A/B %.3f / %.3f'%(g[i0],*r['VSWR_ativo']),fontsize=11)
fig.tight_layout(rect=(0,0,1,.87));fig.savefig(ROOT/'vertical_centro_fino.png',dpi=180);plt.close(fig)
print(json.dumps(out,indent=2))
