"""Dimensionamento preliminar; não executa HFSS nem modifica projetos anteriores."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq
from scipy.signal import find_peaks
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
P2M21 = OUT.parents[1] / 'P2M21'
CELL = P2M21 / 'quatro_elementos_casamento_banda/c12_raiz_intermediaria'
REF = P2M21 / 'comparacao_colunas_niveis'
sources = [CELL/'AB_H.csv', CELL/'AB_V.csv', CELL/'resultado.json',
           REF/'R15_Oito_Celulas_8passes/resultado.json',
           REF/'R16_Oito_Celulas_78mm/resultado.json']
refs = [json.loads(p.read_text(encoding='utf-8-sig')) for p in sources[-2:]]
wavelength = 299792458 / 5.17e9 * 1000
angles = np.linspace(-90, 90, 36001)

def read_pattern(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    a = np.array([float(r['Theta [deg]']) for r in rows])
    g = np.array([float(r['dB(RealizedGainTotal) []']) for r in rows])
    return PchipInterpolator(a, g)(angles)

def af_power(n, pitch):
    x = (np.arange(n) - (n-1)/2) * pitch
    af = np.mean(np.exp(2j*np.pi*x[:, None]*np.sin(np.deg2rad(angles))/wavelength), axis=0)
    return np.maximum(np.abs(af)**2, 1e-16)

def metrics(pattern):
    # Lóbulo central, cruzamentos adjacentes, não os lóbulos de grade.
    center = np.flatnonzero(np.abs(angles) <= 5)
    peak = center[np.argmax(pattern[center])]
    p = pattern - pattern[peak]
    left = peak
    right = peak
    while left > 0 and p[left] > -3: left -= 1
    while right < len(p)-1 and p[right] > -3: right += 1
    l = np.interp(-3, p[left:left+2], angles[left:left+2])
    r = np.interp(-3, p[right-1:right+1][::-1], angles[right-1:right+1][::-1])
    minima = find_peaks(-p)[0]
    lm = minima[minima < peak][-1]
    rm = minima[minima > peak][0]
    peaks = find_peaks(p)[0]
    side = [i for i in peaks if i < lm or i > rm]
    i = max(side, key=lambda q:p[q]) if side else None
    return dict(abertura_graus=float(r-l), maximo_graus=float(angles[peak]),
                lobulo_lateral_dB=None if i is None else float(p[i]),
                lobulo_lateral_graus=None if i is None else float(angles[i]))

hcell, vcell = read_pattern(sources[0]), read_pattern(sources[1])
def horizontal(d): return hcell + 10*np.log10(af_power(2, d))
d20 = brentq(lambda d: metrics(horizontal(d))['abertura_graus']-20, 70, 110)
horizontal_table = [dict(passo_mm=float(d), **metrics(horizontal(d)),
                         replica_fator_arranjo_graus=float(np.degrees(np.arcsin(wavelength/d))))
                    for d in [72,78,d20]]
spacing_empirical = [r['cortes']['H']['abertura_graus']*d/20 for r,d in zip(refs,[72,78])]
vertical_table = []
for n in [4,8,12,16,20]:
    v = vcell + 10*np.log10(af_power(n//4, 192))
    gains = [r['cortes']['H']['ganho_frontal_dBi'] + 10*np.log10(n/16) for r in refs]
    vertical_table.append(dict(niveis=n, colunas=2, radiadores=2*n, placas=n//2,
                               ganho_estimado_min_dBi=min(gains), ganho_estimado_max_dBi=max(gains),
                               largura_vertical_estimada_graus=metrics(v)['abertura_graus'],
                               altura_envelope_pcbs_mm=184+(n//4-1)*192))

result = dict(estado='ESTIMATIVA_INICIAL_NAO_SIMULADA', data='2026-11-13', frequencia_GHz=5.17,
              comprimento_onda_mm=wavelength, fontes=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sources],
              meta=dict(ganho_frontal_total_dBi=19, H_graus=20, V_desejavel_graus=20),
              excitacao='Todas as entradas das células iguais e em fase; 1 W incidente total. Não é ganho MIMO por entrada.',
              referencia=[dict(passes=r['passes'], convergiu=r['convergiu'], delta_s=r['delta_s'],
                              G=r['cortes']['H']['ganho_frontal_dBi'], H=r['cortes']['H']['abertura_graus'], V=r['cortes']['V']['abertura_graus']) for r in refs],
              niveis=vertical_table, horizontal=horizontal_table,
              extrapolacao_passo_horizontal_mm=spacing_empirical,
              advertencia_horizontal='O fator de arranjo prevê 22,33/20,71 graus a 72/78 mm, enquanto os painéis HFSS preliminares deram 24,35/22,96. Portanto 80,91 mm não é dimensão validada. A extrapolação inversa das larguras HFSS aponta 87,7–89,5 mm; usar 88 mm apenas como candidato inicial, acompanhado de controle dos lóbulos laterais.',
              metodo_ganho='G_ref + 10 log10(N/16), nas geometrias horizontais de referência de 72/78 mm. Intervalo entre duas referências preliminares, não intervalo de confiança. Não transfere o ganho para a nova separação horizontal.',
              metodo_cortes='Padrão C12 + fator de arranjo normalizado. Cópias idênticas, sem novo acoplamento. Vertical usa centros das células a 192 mm. Horizontal usa duas colunas. Interpolação não aumenta a resolução física de 0,25 grau da fonte.',
              limites='Ganhos R15/R16 não convergidos. Incluem divisores locais e cabos de 50 mm originais; excluem futura distribuição externa, radome e tolerâncias. Novo espaçamento e refletor requerem HFSS. Nenhum solve executado.',
              candidato=dict(niveis=16,colunas=2,placas=8,passo_vertical_mm=48,
                             distancia_pcb_refletor_mm=14.949,passo_horizontal_exploratorio_mm=88,
                             passos_horizontais_a_comparar_mm=[84,88,92],
                             entrada_por_polarizacao=1,externas=2,conexoes_celulas=16,
                             distribuicao_proposta='Uma rede simétrica 1:8 por polarização: raiz 1:2 central e 1:4 por coluna. Caminhos elétricos iguais; perdas e casamento ainda não dimensionados.'))
(OUT/'estimativa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'comparacao_niveis.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f, fieldnames=vertical_table[0]); w.writeheader(); w.writerows(vertical_table)

fig,ax=plt.subplots(1,2,figsize=(12,4.8))
for d in [72,78,d20]:
    p=horizontal(d); central=np.abs(angles)<5; p-=p[central].max()
    ax[0].plot(angles,p,label=f'{d:.1f} mm entre colunas')
ax[0].set(xlim=(-90,90),ylim=(-30,1),xlabel='Ângulo horizontal (°)',ylabel='Ganho normalizado (dB)',title='Previsão H — padrão C12 × fator de arranjo')
ax[0].axhline(-3,color='gray',ls='--',lw=.8); ax[0].grid(alpha=.3); ax[0].legend(fontsize=8)
for n in [4,8,12,16,20]:
    p=vcell+10*np.log10(af_power(n//4,192)); p-=p[np.abs(angles)<5].max()
    ax[1].plot(angles,p,label=f'{n} níveis por coluna')
ax[1].set(xlim=(-20,20),ylim=(-20,1),xlabel='Ângulo vertical (°)',ylabel='Ganho normalizado (dB)',title='Previsão V — passo vertical de 48 mm')
ax[1].axhline(-3,color='gray',ls='--',lw=.8); ax[1].grid(alpha=.3); ax[1].legend(fontsize=8)
fig.suptitle('P2M19 — dimensionamento preliminar em 5,17 GHz',fontsize=14)
fig.text(.5,.015,'Estimativa por fator de arranjo: não inclui novo acoplamento nem valida ganho da nova geometria.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.045,1,.94)); fig.savefig(OUT/'diagramas_estimados.png',dpi=170);plt.close(fig)
print(json.dumps(dict(niveis=vertical_table,horizontal=horizontal_table),ensure_ascii=False,indent=2))
