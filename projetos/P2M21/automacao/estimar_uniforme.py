"""Estimativa N x M, todas as portas A/B em fase; nao usa R00 nao convergida."""
import csv,json,sys,hashlib
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

repo=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(repo/'automacao/r05'))
from rede_carregada import read_pattern,beam
source=Path('D:/dev/EMBRAER/P1H/R06_sem_cabos/antena')
out=Path('D:/dev/EMBRAER/P2M21/R01_Estimativa_Uniforme');out.mkdir(parents=True,exist_ok=True)
frequency=5.17e9;c=299792458.;pitch_v=52.6
audit=json.loads((source/'auditoria_convergencia.json').read_text())
assert audit['convergencia_aprovada']
names=['E%02d_%s'%(i,pol) for i in range(1,11) for pol in 'AB']
sources={};base={};reference={}
for axis in 'HV':
    fields=[]
    for name in names:
        path=source/'padroes'/(name+'_'+axis+'.csv')
        theta,field=read_pattern(path);fields.append(field)
        sources[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
    fields=np.stack(fields,axis=-1)
    voltage=np.ones(20)/np.sqrt(20)
    gain=10*np.log10(np.maximum(np.sum(abs(fields@voltage)**2,axis=-1),1e-30))
    with (source/('Centro_'+axis+'.csv')).open(encoding='utf-8-sig',newline='') as f:native=list(csv.DictReader(f))
    native_theta=np.array([float(r['Theta [deg]']) for r in native])
    native_gain=np.array([float(r['dB(RealizedGainTotal) []']) for r in native])
    np.testing.assert_allclose(native_theta,theta,atol=1e-9)
    np.testing.assert_allclose(native_gain,gain,atol=.00001)
    reference[axis]=dict(erro_recomposicao_max_dB=float(max(abs(native_gain-gain))),
      ganho_frontal_dBi=float(gain[np.argmin(abs(theta))]),abertura_graus=float(beam(theta,gain)[0]))
    center=int(np.argmin(abs(theta)))
    reference[axis]['ganho_total_potencia_aceita_dBi']=float(native[center]['dB(GainTotal) []'])
    reference[axis]['diretividade_total_dBi']=float(native[center]['dB(DirTotal) []'])
    base[axis]=PchipInterpolator(theta,gain)
np.testing.assert_allclose(reference['H']['ganho_frontal_dBi'],reference['V']['ganho_frontal_dBi'],atol=1e-8)
g0=reference['H']['ganho_frontal_dBi']

def af(count,angles,pitch):
    # Intensidade do fator de arranjo com potencia incidente TOTAL constante.
    u=pitch/1000*frequency/c*np.sin(np.deg2rad(angles))
    return count*(np.sinc(count*u)/np.sinc(u))**2

angle_h=np.linspace(-90,90,18001)
angle_v=np.linspace(-4,4,1601)
af10=af(10,angle_v,pitch_v)
assert min(af10)>1 # Sem dividir pelos nulos da coluna de referencia.

def estimate(n,m,pitch_h):
    h=base['H'](angle_h)+10*np.log10(np.maximum(af(m,angle_h,pitch_h),1e-30))+10*np.log10(n/10)
    v=base['V'](angle_v)+10*np.log10(np.maximum(af(n,angle_v,pitch_v)/af10,1e-30))+10*np.log10(m)
    gain=g0+10*np.log10(n*m/10)
    row=dict(niveis=n,colunas=m,radiadores=n*m,portas=2*n*m,
      potencia_total_W=1.,potencia_por_porta_W=1/(2*n*m),fase_todas_portas_graus=0,
      passo_vertical_mm=pitch_v,passo_horizontal_mm=pitch_h,
      ganho_frontal_total_estimado_dBi=float(gain),
      abertura_horizontal_estimada_graus=float(beam(angle_h,h)[0]),
      abertura_vertical_estimada_graus=float(beam(angle_v,v)[0]),
      altura_pcb_ativa_mm=(n-1)*pitch_v+28.3125,
      largura_pcb_ativa_mm=(m-1)*pitch_h+28.3125,
      margem_pre_rede_para_21dBi_dB=float(gain-21),
      ganho_menos_reserva_1dB_dBi=float(gain-1))
    return row,h,v

rows=[]
for n in (10,12,14,16,18,20):
    for m in (2,4):
        for dh in (32,40,48):rows.append(estimate(n,m,dh)[0])
baseline=estimate(10,1,40)[0]
assert abs(baseline['ganho_frontal_total_estimado_dBi']-g0)<1e-10
assert abs(baseline['abertura_horizontal_estimada_graus']-reference['H']['abertura_graus'])<.01
assert abs(baseline['abertura_vertical_estimada_graus']-reference['V']['abertura_graus'])<.03
with (out/'comparacao_completa.csv').open('w',newline='',encoding='utf8') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
selected=[r for r in rows if r['passo_horizontal_mm']==40 and (r['colunas']==2 or r['niveis'] in (10,12))]
with (out/'comparacao_40mm.csv').open('w',newline='',encoding='utf8') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(selected)
data=dict(metodo='Recomposicao coerente dos20campos R06, depois fator de arranjo separavel e escala de contagem.',
  data='2026-11-09',frequencia_Hz=frequency,potencia_total_W=1.,referencia=reference,
  modelo_referencia='P1H R06 PCB de10radiadores/20portas, alimentacao direta uniforme A+B, sem rede.',
  reserva_1dB='Somente cenario de margem; nao e perda medida ou simulada da nova rede.',
  formula_ganho='G(N,M) = G(10,1) + 10log10(N*M/10)',
  formula_cortes='H: referenciaH*AF_M*(N/10). V: referenciaV*AF_N/AF_10*M, em intensidade.',
  limites=['Estimativa exclusivamente em5.17GHz; nao qualifica os17pontos.',
    'Padrão efetivo da coluna R06 preservado; novo acoplamento e alteracoes do refletor/substrato nao incluidos.',
    'Perdas/desequilibrios da rede e cabos ausentes; perdas e descasamento da PCB R06 estao na referencia.',
    'Normalizacao pela potencia incidente total; nenhuma soma automatica de3dB pelas polarizacoes.',
    'CorteV extrapolado somente de-4a4graus, longe dos nulos AF10; nao prediz os lobulos laterais verticais.',
    'Dados nativos em0.25grau; interpolacao PCHIP para cruzamentos-3dB. Resolucao grafica nao e nova simulacao.',
    'Excitacao coerente de todas as portas; nao substitui qualificacao MIMO por entrada com outra casada.'],
  fonte_auditoria_sha256=hashlib.sha256((source/'auditoria_convergencia.json').read_bytes()).hexdigest(),
  fontes_campos_sha256=sources,casos=rows,referencia10x1=baseline)
(out/'metodo_e_resultados.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')

plt.rcParams.update({'font.size':10})
fig,axs=plt.subplots(1,3,figsize=(15,4.8))
for m,color in [(2,'#147da0'),(4,'#ba542c')]:
    subset=[r for r in rows if r['colunas']==m and r['passo_horizontal_mm']==40]
    x=[r['niveis'] for r in subset];y=[r['ganho_frontal_total_estimado_dBi'] for r in subset]
    axs[0].plot(x,y,'o-',color=color,label=f'{m} colunas, portas diretas')
    axs[0].plot(x,np.array(y)-1,'--',color=color,alpha=.65,label=f'{m} colunas, reserva 1 dB')
axs[0].axhline(21,color='#444',ls=':');axs[0].set(xlabel='Níveis verticais',ylabel='Ganho total estimado (dBi)',xticks=list(range(10,21,2)));axs[0].legend(fontsize=8);axs[0].grid(alpha=.25)
for m,col in [(1,'#888888'),(2,'#147da0'),(4,'#ba542c')]:
    r,h,v=estimate(10,m,40);axs[1].plot(angle_h,h-r['ganho_frontal_total_estimado_dBi'],color=col,label=f'{m} col.: H {r["abertura_horizontal_estimada_graus"]:.1f}°')
axs[1].axhline(-3,color='#444',ls=':');axs[1].set(xlim=(-75,75),ylim=(-25,1),xlabel='Ângulo horizontal (graus)',ylabel='Nível relativo (dB)');axs[1].legend(fontsize=8);axs[1].grid(alpha=.25)
for n in (10,12,14,16):
    r,h,v=estimate(n,2,40);axs[2].plot(angle_v,v-r['ganho_frontal_total_estimado_dBi'],label=f'{n} níveis: V {r["abertura_vertical_estimada_graus"]:.2f}°')
axs[2].axhline(-3,color='#444',ls=':');axs[2].set(xlim=(-4,4),ylim=(-12,1),xlabel='Ângulo vertical (graus)',ylabel='Nível relativo (dB)');axs[2].legend(fontsize=8);axs[2].grid(alpha=.25)
fig.suptitle('P2M21 — estimativa a 5,17 GHz | todas as portas A/B iguais e em fase | passos 52,6 × 40 mm',fontsize=13)
fig.text(.5,.012,'Referência: campos convergidos da P1H R06. Novo acoplamento, rede e comprovação de banda pendentes.',ha='center',fontsize=10)
fig.tight_layout(rect=(0,.05,1,.92));fig.savefig(out/'comparacao_uniforme.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(7,4))
for m in (2,4):
    part=[estimate(10,m,d)[0] for d in (32,40,48)]
    ax.plot([p['passo_horizontal_mm'] for p in part],[p['abertura_horizontal_estimada_graus'] for p in part],'o-',label=f'{m} colunas')
ax.set(xlabel='Passo entre colunas (mm)',ylabel='Abertura horizontal estimada (graus)',xticks=[32,40,48]);ax.legend();ax.grid(alpha=.3)
fig.suptitle('Efeito do espaçamento horizontal — estimativa, 5,17 GHz');fig.tight_layout();fig.savefig(out/'espacamento_horizontal.png',dpi=180);plt.close(fig)
print(json.dumps(dict(referencia=reference,comparacao=selected),ensure_ascii=False,indent=2))
