"""Analise dos dados HFSS existentes: duas entradas coerentes, sem novo solve."""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import skrf as rf
from scipy.signal import find_peaks

ROOT = Path('D:/dev/EMBRAER/P2M21/R08_Dois_Verticais_Sem_Suportes')
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO/'automacao/r05'))
sys.path.insert(0, str(REPO/'automacao/r06'))
from rede_carregada import beam
from auditar_malha import audit


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(mode, axis):
    path = ROOT/(mode+'_'+axis+'.csv')
    rows = list(csv.DictReader(path.open(encoding='utf-8-sig', newline='')))
    theta = np.array([float(r['Theta [deg]']) for r in rows])
    gain = np.array([float(r['dB(RealizedGainTotal) []']) for r in rows])
    fields = np.array([[complex(float(r['re(rETheta) [V]']), float(r['im(rETheta) [V]'])),
                        complex(float(r['re(rEPhi) [V]']), float(r['im(rEPhi) [V]']))] for r in rows])
    assert np.isfinite(gain).all() and np.isfinite(fields).all()
    np.testing.assert_allclose(theta, np.arange(-180, 180.001, .25), atol=1e-10)
    assert all(abs(float(r['Freq [GHz]'])-5.17) < 1e-10 for r in rows)
    assert all(float(r['Phi [deg]']) == (90 if axis == 'H' else 0) for r in rows)
    return theta, gain, fields, rows


def main():
    cfg = json.loads((ROOT/'configuracao.json').read_text(encoding='utf-8'))
    native = (ROOT/cfg['native']).read_text(errors='replace')
    source_rows = re.findall(r'SourceEntry\([^\n]+', native)
    assert len(source_rows) == 2
    assert all("Magnitude='0.5W'" in s and "Phase='0deg'" in s for s in source_rows)
    conv_text = (ROOT/'convergencia.txt').read_text()
    max_passes = int(re.search(r'Maximum\s*:\s*(\d+)', conv_text)[1])
    completed = int(re.search(r'Completed\s*:\s*(\d+)', conv_text)[1])
    assert max_passes == 6 and completed <= 6
    history = {}
    conv_files = list(ROOT.rglob('*.EMConvData'))
    assert len(conv_files) == 1
    for b in conv_files[0].read_text().split("$begin 'QuantityValues'")[1:]:
        b = b.split("$end 'QuantityValues'", 1)[0]
        n = int(re.search(r'PassNo=(\d+)', b)[1])
        ds = re.search(r'MaxMagDeltaS\(([^,]+)', b)
        history[n] = dict(passe=n, tetraedros=int(float(re.search(r'SolvedElements\(([^,]+)', b)[1])),
                          delta_s=float(ds[1]) if ds else None)
    assert max(history) == completed
    delta = history[completed]['delta_s']
    converged = 'Converged : Yes' in conv_text and delta <= .04
    mesh = audit(ROOT)
    n = rf.Network(str(ROOT/'centro.s2p'))
    assert n.nports == 2 and list(n.port_names) == ['A', 'B'] and len(n.f) == 1
    np.testing.assert_allclose(n.f, [5.17e9], rtol=0, atol=1)
    np.testing.assert_allclose(n.z0, 50)
    s = n.s[0]
    a = np.ones(2)/np.sqrt(2)
    b = s@a
    active = b/a
    vswr = lambda g: (1+abs(g))/(1-abs(g))
    accepted = float(1-np.sum(abs(b)**2))
    singular = float(np.linalg.svd(s, compute_uv=False).max())
    reciprocity = float(abs(s-s.T).max())
    cuts, curves, check_fields = {}, {}, {}
    for axis in 'HV':
        theta, gain, fields, rows = read('AB', axis)
        _, _, fa, _ = read('A', axis)
        _, _, fb, _ = read('B', axis)
        reconstructed = (fa+fb)/np.sqrt(2)
        field_error = float(np.max(abs(fields-reconstructed))/np.max(abs(fields)))
        assert field_error < 1e-7, field_error
        check_fields[axis] = field_error
        width, left, right = beam(theta, gain)
        center = int(np.argmin(abs(theta)))
        front = np.flatnonzero(abs(theta) <= 90)
        peak = front[np.argmax(gain[front])]
        gain_accepted = float(rows[center]['dB(GainTotal) []'])
        directivity = float(rows[center]['dB(DirTotal) []'])
        ratio = 10**((gain[center]-gain_accepted)/10)
        assert abs(ratio-accepted) < 1e-6
        efficiency = 10**((gain_accepted-directivity)/10)
        assert 0 < efficiency <= 1
        enorm = np.sqrt(np.sum(abs(fields)**2, axis=1))
        enorm /= enorm.max()
        np.testing.assert_allclose(enorm, 10**((gain-gain.max())/20), rtol=1e-8)
        cuts[axis] = dict(phi_graus=90 if axis == 'H' else 0,
            ganho_frontal_realizado_dBi=float(gain[center]), ganho_pico_no_corte_dBi=float(gain[peak]),
            angulo_pico_graus=float(theta[peak]), abertura_3dB_graus=float(width),
            limites_3dB_graus=[float(left), float(right)],
            ganho_traseiro_eixo_dBi=float(gain[0]), frente_costas_no_eixo_dB=float(gain[center]-gain[0]),
            ganho_frontal_dBi=gain_accepted, diretividade_frontal_dBi=directivity,
            eficiencia_radiacao=efficiency, erro_potencia_aceita=abs(ratio-accepted))
        peaks, _ = find_peaks(gain)
        secondary = [i for i in peaks if abs(theta[i]) <= 90 and i != peak]
        cuts[axis]['picos_secundarios_hemisferio_frontal'] = [
            dict(angulo_graus=float(theta[i]), ganho_dBi=float(gain[i]),
                 nivel_relativo_ao_pico_dB=float(gain[i]-gain[peak]))
            for i in sorted(secondary, key=lambda i:gain[i], reverse=True)]
        curves[axis] = (theta, gain, enorm)
    assert abs(cuts['H']['ganho_frontal_realizado_dBi']-cuts['V']['ganho_frontal_realizado_dBi']) < 1e-8
    profiles = list(ROOT.rglob('*.profile'))
    assert len(profiles) == 1
    profile = profiles[0].read_text(errors='replace').replace("\\'", "'")
    solve_cores = [int(re.search(r"'Cores', (\d+)", line)[1]) for line in profile.splitlines()
                   if "ProfileItem('Matrix Solve'" in line]
    assert len(solve_cores) == completed and set(solve_cores) == {14}, solve_cores
    result = dict(frequencia_GHz=5.17, espacamento_vertical_mm=48,
        nucleos_matrix_solve_por_passe=solve_cores,
        alimentacao=dict(A='0.5 W / 0 graus', B='0.5 W / 0 graus', total_W=1),
        fonte_excitado_no_native=source_rows,
        convergiu=converged, preliminar=not converged, passes=completed, max_passes=max_passes,
        delta_s=delta, alvo_delta_s=.04, tetraedros=history[completed]['tetraedros'],
        historico=[history[k] for k in sorted(history)], cortes=cuts,
        VSWR_ativo_AB=vswr(active).tolist(), VSWR_outro_casado=vswr(np.diag(s)).tolist(),
        potencia_aceita_por_porta_W=(abs(a)**2-abs(b)**2).tolist(),
        potencia_aceita_total_W=accepted, potencia_refletida_total_W=1-accepted,
        eficiencia_radiacao=efficiency, eficiencia_total=accepted*efficiency,
        S21_dB=float(20*np.log10(abs(s[1, 0]))),
        matriz_passiva=singular <= 1.0001, maior_valor_singular=singular,
        residuo_reciprocidade=reciprocity, erro_recomposicao_complexa=check_fields,
        malha_major=mesh['reparos_major'], malha_minor=mesh['reparos_minor'],
        notas=['Soma coerente dos campos complexos A e B confirmada; nao soma de ganhos em dB.',
               'Abertura medida a -3 dB do maximo de cada corte, com interpolacao linear e grade0.25grau.',
               'Picos informados sao dos cortes, nao uma busca pelo maximo em toda a esfera.',
               'Inclui os dois cabos fisicos50mm, divisores impressos, PCB e refletor; exclui os apoiosPOM.',
               'Resultado limitado a5.17GHz e6passes, sem convergencia; nao qualifica banda nem espacamento otimo.',
               'Igual fase/amplitude nas entradas externas nao demonstra igualdade nos quatro terminais radiantes.'],
        fontes={p.name:sha(p) for p in [ROOT/cfg['native'], ROOT/'centro.s2p', ROOT/'convergencia.txt']+
                [ROOT/(mode+'_'+axis+'.csv') for mode in ['AB','A','B'] for axis in 'HV']})
    (ROOT/'analise_AB.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (ROOT/'malha.json').write_text(json.dumps(mesh, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10})
    fig, axes = plt.subplots(1, 2, figsize=(12, 6.7), subplot_kw={'projection':'polar'})
    colors = {'H':'#186eaa', 'V':'#d57824'}
    for ax, axis, label in zip(axes, 'HV', ['Horizontal / plano YZ', 'Vertical / plano XZ']):
        theta, gain, e = curves[axis]
        c = cuts[axis]
        ax.plot(np.deg2rad(theta), e, color=colors[axis], lw=2)
        ax.plot(np.linspace(-np.pi,np.pi,361),np.full(361,10**(-3/20)), '--', color='#777777', lw=.9)
        for bound in c['limites_3dB_graus']:
            ax.plot([np.deg2rad(bound)]*2,[0,10**(-3/20)],':',color=colors[axis],alpha=.8)
        ax.set_theta_zero_location('N'); ax.set_theta_direction(-1)
        ax.set_thetagrids(np.arange(0,360,30), ['0°','30°','60°','90°','120°','150°','180°','−150°','−120°','−90°','−60°','−30°'])
        ax.set_ylim(0,1); ax.set_rticks([.2,.4,.6,.8,1]); ax.set_rlabel_position(120)
        ax.grid(alpha=.35)
        ax.set_title(f"{label}\nAbertura: {c['abertura_3dB_graus']:.2f}° | Pico: {c['angulo_pico_graus']:+.2f}°",pad=25)
    fig.suptitle('Dois elementos verticais — ambas as entradas em fase\n5,17 GHz | A = B = 0,5 W ∠0° | E/Emax por corte',y=.98,fontsize=14)
    fig.text(.5,.065,f"Ganho frontal realizado: {cuts['H']['ganho_frontal_realizado_dBi']:.2f} dBi   |   6 passes   |   ΔS = {delta:.5f} > 0,04",ha='center',fontsize=11)
    fig.text(.5,.025,'PRELIMINAR — NÃO CONVERGIU  •  0° = frente (+Z); linha tracejada = −3 dB de potência',ha='center',color='#a43427',fontsize=10)
    fig.subplots_adjust(top=.76,bottom=.15,left=.05,right=.95,wspace=.27)
    fig.savefig(ROOT/'diagramas_polares_AB.png',dpi=180)
    fig.savefig(ROOT/'diagramas_polares_AB.pdf')
    plt.close(fig)

    fig, axes = plt.subplots(1,2,figsize=(12,4.8),sharey=True)
    for ax, axis in zip(axes,'HV'):
        th,g,_=curves[axis]; c=cuts[axis]
        ax.plot(th,g,color=colors[axis],lw=1.8)
        ax.axhline(c['ganho_pico_no_corte_dBi']-3,ls='--',color='#777777',lw=.9)
        ax.axvline(0,color='#999999',lw=.7)
        ax.scatter([c['angulo_pico_graus']],[c['ganho_pico_no_corte_dBi']],color=colors[axis])
        ax.set(xlim=(-180,180),ylim=(-30,12),xticks=np.arange(-180,181,45),xlabel='Ângulo θ (graus)',
               title=f"Corte {axis} — pico {c['ganho_pico_no_corte_dBi']:.2f} dBi a {c['angulo_pico_graus']:+.2f}°")
        ax.grid(alpha=.25)
    axes[0].set_ylabel('Ganho realizado total (dBi)')
    fig.suptitle('5,17 GHz | A = B = 0,5 W / 0° | dois cabos físicos | sem apoios plásticos',fontsize=12)
    fig.text(.5,.02,f'PRELIMINAR: 6 passes; ΔS = {delta:.5f}; alvo 0,04 não atingido.',ha='center',color='#a43427')
    fig.tight_layout(rect=[0,.05,1,.94]);fig.savefig(ROOT/'ganho_cortes_AB.png',dpi=180);plt.close(fig)

    h,v=cuts['H'],cuts['V']
    md=f'''# Dois elementos verticais — análise com A e B em fase

Simulação concluída em 09/11/2026, às09:16:49, na GUI do HFSS2024R2. Resultado **preliminar, não convergido**.

- Configuração: dois elementos separados48mm, dois divisores1:2 impressos, dois cabos físicos50mm, PCBRO4350B0,76mm e refletorAl2mm; sem os dois suportesPOM.
- Excitação: A=B=0,5W/0°, potência incidente total1W, referência50Ω nas extremidades dos cabos.
- Frequência única5,17GHz; sem sweep. SetupClassic sem refinamento local prévio. Perfil14núcleos.
- Término por limite: {completed}passes, {history[completed]['tetraedros']:,}tetraedros. ΔS={delta:.8f}, alvo0,04; zero passes consecutivos aprovados. Sem reparosMajor/Minor.

| Métrica | Horizontal | Vertical |
|---|---:|---:|
| Ganho frontal realizado | {h['ganho_frontal_realizado_dBi']:.2f}dBi | {v['ganho_frontal_realizado_dBi']:.2f}dBi |
| Abertura a−3dB do pico do corte | {h['abertura_3dB_graus']:.2f}° | {v['abertura_3dB_graus']:.2f}° |
| Pico no corte | {h['ganho_pico_no_corte_dBi']:.2f}dBi | {v['ganho_pico_no_corte_dBi']:.2f}dBi |
| Direção do pico | {h['angulo_pico_graus']:+.2f}° | {v['angulo_pico_graus']:+.2f}° |
| Limites de−3dB | {h['limites_3dB_graus'][0]:+.2f}° a {h['limites_3dB_graus'][1]:+.2f}° | {v['limites_3dB_graus'][0]:+.2f}° a {v['limites_3dB_graus'][1]:+.2f}° |

O máximo horizontal está deslocado+15,25° e o vertical−6,25°, tomando+Z como frente. O ganho na frente está0,77dB abaixo do pico horizontal. Esses picos são os encontrados nos dois cortes, não um máximo3D da esfera.

| Casamento | Porta A | Porta B |
|---|---:|---:|
| VSWR ativo, A+B em fase | {result['VSWR_ativo_AB'][0]:.3f} | {result['VSWR_ativo_AB'][1]:.3f} |
| VSWR com outra entrada casada | {result['VSWR_outro_casado'][0]:.3f} | {result['VSWR_outro_casado'][1]:.3f} |

A portaB apresenta o maior descasamento. A potência aceita total é{accepted:.6f}W ({100*accepted:.2f}% da incidente), eficiência de radiação{100*efficiency:.2f}% e eficiência total{100*accepted*efficiency:.2f}%. Relação frente/costas no eixo:{h['frente_costas_no_eixo_dB']:.2f}dB. AcoplamentoS21:{result['S21_dB']:.2f}dB. Os valores de eficiência vêm dos ganhos/diretividade e da matrizS, não de uma integração independente de perdas.

A soma complexa(E_A+E_B)/√2 reproduziu os camposAB com erro relativo máximo{max(check_fields.values()):.3e}. A matriz é passiva (maior valor singular{singular:.6f}); o resíduo de reciprocidade|S12−S21| é{reciprocity:.3e}. A normalização de potência foi conferida com a matrizS. A ausência de reparos não substitui a convergência.

O deslocamento e o VSWRB indicam que vale examinar o casamento e as fases efetivas do ramoB antes de ampliar esta placa. Os dados atuais não separam a influência da rede, da assimetria geométrica e do erro de malha; não permitem atribuir uma causa única. Mesma amplitude/fase nas duas entradas não comprova mesma amplitude/fase nos quatro pontos dos radiadores.

Não foi executado novo solve nesta análise. Nenhuma qualificação de banda, de espaçamento ótimo ou de ganhoMIMO por entrada é inferida.

![Diagramas polares](diagramas_polares_AB.png)

![Ganho absoluto](ganho_cortes_AB.png)

Dados rastreáveis em`analise_AB.json`, arquivosAB_H/AB_V.csv, centro.s2p e convergencia.txt. O projeto.aedt sem sua pasta.aedtresults preserva o modelo e relatórios, mas não os campos FEM nativos.
'''
    # Legibilidade do documento, sem alterar dados ou valores do calculo.
    substitutions = {
        'às09:16:49':'às 09:16:49', 'HFSS2024R2':'HFSS 2024 R2',
        'separados48mm':'separados 48 mm', 'divisores1:2':'divisores 1:2', 'físicos50mm':'físicos de 50 mm',
        'PCBRO4350B0,76mm':'PCB RO4350B de 0,76 mm', 'refletorAl2mm':'refletor de Al de 2 mm',
        'suportesPOM':'suportes POM', 'A=B=0,5W/0°':'A = B = 0,5 W / 0°',
        'total1W':'total de 1 W', 'referência50Ω':'referência de 50 Ω',
        'única5,17GHz':'única de 5,17 GHz', 'SetupClassic':'Setup Classic', 'Perfil14núcleos.':'14 núcleos confirmados no solver matricial em todos os passes.',
        'alvo0,04':'alvo 0,04', 'reparosMajor/Minor':'reparos Major/Minor',
        'a−3dB':'a −3 dB', 'de−3dB':'de −3 dB', 'deslocado+15,25°':'deslocado +15,25°',
        'vertical−6,25°':'vertical −6,25°', 'tomando+Z':'tomando +Z',
        'está0,77dB':'está 0,77 dB', 'máximo3D':'máximo 3D', 'portaB':'porta B',
        'AcoplamentoS21':'Acoplamento S21', 'complexa(E_A+E_B)/√2':'complexa (E_A + E_B)/√2',
        'camposAB':'campos AB', 'reciprocidade|S12−S21|':'reciprocidade |S12 − S21|',
        'matrizS':'matriz S', 'VSWRB':'VSWR B', 'ramoB':'ramo B', 'ganhoMIMO':'ganho MIMO',
        'em`analise_AB.json`':'em `analise_AB.json`', 'arquivosAB_H/AB_V.csv':'arquivos AB_H/AB_V.csv',
        'projeto.aedt':'projeto .aedt', 'pasta.aedtresults':'pasta .aedtresults'}
    for old,new in substitutions.items(): md=md.replace(old,new)
    md=re.sub(r'(\d)(dBi|dB|W|passes|tetraedros)\b',r'\1 \2',md)
    (ROOT/'analise_AB.md').write_text(md,encoding='utf-8')
    state=json.loads((ROOT/'qualificacao.json').read_text(encoding='utf-8'))
    state.update(estado='ANALISADO_PRELIMINAR_NAO_CONVERGIU', convergiu=converged, delta_s=delta, passes=completed,
                 analise='analise_AB.json', diagrama='diagramas_polares_AB.png')
    (ROOT/'qualificacao.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['fontes','fonte_excitado_no_native','historico']},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
