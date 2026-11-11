"""Arquiva a otimizacao R09 com resultados reais; nunca inclui malhas."""
from pathlib import Path
import argparse, json, hashlib, shutil, zipfile

REPO = Path(__file__).resolve().parents[3]
BASE = Path('D:/dev/EMBRAER/P2S13/R09_Correcao_Divisor')
OUT = REPO / 'projetos/P2S13/divisor_duplo_1x3_correcao'
ap = argparse.ArgumentParser()
ap.add_argument('--final', required=True)
args = ap.parse_args()
FINAL = BASE / args.final
assert FINAL.parent == BASE and (FINAL / 'resultado.json').is_file()
read = lambda p: json.loads(p.read_text(encoding='utf8'))
r = read(FINAL / 'resultado.json')
cfg = read(FINAL / 'configuracao.json')
nx = read(FINAL / 'circuito/verificacao_nexxim.json')
assert nx['matriz_conferida'] and nx['erro_absoluto_max'] < 2e-6
cases = sorted(p.parent for p in BASE.glob('c*/resultado.json'))
rows = []
for p in cases:
    v = read(p / 'resultado.json')
    c = read(p / 'configuracao.json')
    assert v['passes'] <= 6 and all(n == 14 for n in v['nucleos_por_passe'])
    assert not (p / 'Divisor_Duplo3.aedt.lock').exists()
    rows.append('| %s | %s | %d / %.6f | %d/2 | %.4f / %.4f | %.4f | %.3f / %.3f |' % (
        p.name, c.get('basis_order', 1), v['passes'], v['delta_s'], v['consecutivos'],
        *v['VSWR_ativo'], v['cortes']['H']['ganho_frontal_dBi'], v['dispersao_amplitude_dB'], v['dispersao_fase_graus']))
yes = lambda x: 'sim' if x else 'não'
trace_rows = ['| %s | %.3f | %.4f | %.4f |' % (t['name'][2:], t['Z_ohm'], t['width_mm'], t['length_mm'])
              for t in cfg['traces'] if t['name'].startswith('A_')]
wave_rows = ['| %s | %.7f | %+.4f |' % x for x in zip(r['ordem_S8_circuito'][2:],
    r['ondas_incidentes_antena_potencia_W'], r['ondas_incidentes_antena_fase_relativa_graus'])]
hist = read(FINAL / 'historico_passes.json')
fine=read(FINAL/'vertical_centro_fino.json')
outer=cfg['parametros'].get('outer_delta_mm',[0,0])
goal=read(BASE/'objetivos.json')
gain_target=goal['ganho_frontal_min_dBi']
mask = cfg.get('mask_windows')
mask_text = ('A versão selecionada não usa máscara nas trilhas simuladas.' if not mask else
    'A versão selecionada cobre trechos longos com máscara física, deixando ENIG somente nas áreas abertas. '
    'O modelo usa 20,32 µm sobre laminado e 12,7 µm sobre cobre, εr=3,8 e tanδ=0,025. '
    'Espessuras e εr são referências genéricas da JLC; tanδ=0,025 em 5,17 GHz é hipótese nominal, '
    'baseada em referência genérica Rogers a 1 GHz, e precisa de confirmação do material efetivamente fabricado. '
    'O efeito não foi modelado como remoção gratuita de perdas: o dielétrico da máscara participa do HFSS. '
    'Os planos artificiais de partição do cobre não recebem ENIG; a continuidade metálica é preservada.')
md = f'''# P2S13 — correção do divisor duplo 1:3

Estudo de 11/11/2026, **5,17 GHz**, duas entradas iguais de **0,5 W / 0°**, total 1 W, sem sweep. Versão selecionada: **{args.final}**. A antena R06 de três placas de dois elementos permaneceu inalterada; seus seis cabos físicos de 50 mm e respectivas perdas já estão incluídos no S6. Não se adicionaram cabos ideais ou fases artificiais para corrigir os resultados.

| Verificação do conjunto carregado | Resultado | Meta |
|---|---:|---:|
| Ganho frontal realizado total | {r['cortes']['H']['ganho_frontal_dBi']:.4f} dBi | ≥{gain_target:g} dBi: {yes(r['cortes']['H']['ganho_frontal_dBi'] >= gain_target)} |
| VSWR ativo A / B | {r['VSWR_ativo'][0]:.4f} / {r['VSWR_ativo'][1]:.4f} | ≤1,25: {yes(max(r['VSWR_ativo']) <= 1.25)} |
| VSWR com outra entrada casada A / B | {r['VSWR_outra_casada'][0]:.4f} / {r['VSWR_outra_casada'][1]:.4f} | ≤1,25: {yes(max(r['VSWR_outra_casada']) <= 1.25)} |
| Dispersão nas seis saídas carregadas | {r['dispersao_amplitude_dB']:.4f} dB / {r['dispersao_fase_graus']:.4f}° | equilíbrio de amplitude / fase |
| Aberturas H / V | {r['cortes']['H']['abertura_graus']:.3f}° / {r['cortes']['V']['abertura_graus']:.3f}° | medição do resultado |
| Máximos H / V | {r['cortes']['H']['pico_graus']:+.2f}° / {fine['pico_V_grade_graus']:+.2f}° | H: grade0,25°; V: grade0,01° |
| Assimetria do lóbulo principal V | {fine['assimetria_max_mais_menos4graus_dB']:.4f} dB | maior diferença entre +θ e −θ em ±4° |
| Lóbulo secundário V mais alto | {fine['SLL_V_dB']:.3f} dB | relativo ao máximo frontal do corte |
| Passes / ΔS final | {r['passes']} / {r['delta_s']:.8f} | máximo 6 / ΔS≤0,05 |
| Consecutivos / convergência do divisor | {r['consecutivos']}/2 / {yes(r['convergiu'])} | dois passes abaixo do alvo |

A meta inicial era 13 dBi. Durante a rodada, o usuário aceitou **12 dBi incluindo os divisores** e priorizou uniformidade do diagrama vertical com máximo em **0°**. As duas fontes externas continuam iguais/em fase; eventuais pequenas compensações são comprimentos físicos de trilha e não alterações das fontes. Os resultados são nominais e preliminares: o S6 e os campos da antena conservam pendências anteriores de estabilidade e reciprocidade. Cumprimento numérico das metas, quando indicado, não equivale a validação experimental ou liberação de fabricação.

## Correção física

O divisor em cascata da R08 foi substituído por duas trifurcações diretas espelhadas, com três transformadores de impedância por entrada, sem resistores de isolamento. Essa escolha reduz o percurso e elimina a dissipação nos resistores, mas as saídas deixam de ser isoladas entre si. As reflexões das seis cargas são incluídas pela conexão das matrizes completas S8 e S6.

A PCB mantém **220 × 64 mm**, ZYF300CA-C de núcleo **1,52 mm**, εr=2,94, tanδ=0,0016, Cu físico **35 µm**, rugosidade nominal 0,5 µm e ENIG Au **0,0254 µm** / NiP **4,5 µm**, σNiP=1,5 MS/m. Pinos, acessos PTFE, massas e soldas locais estão representados. As saídas permanecem em X=−93,491 / +2,509 / +98,509 mm e Y=±18 mm, alinhadas aos cabos existentes.

As rotas externas foram abertas para reduzir acoplamento com a dobra da linha central. Comprimentos e larguras foram ajustados com o divisor carregado pela antena. O ramo central é fisicamente menor em cerca de duas ondas guiadas; isso iguala a fase somente próximo da frequência central. Não há demonstração de banda.

Compensação adicional de comprimento nas saídas dos grupos R1/R3: **{outer[0]:+.6f} / {outer[1]:+.6f} mm**, aplicada igualmente nas polarizações A/B por alteração do chanfro das curvas; os terminais não mudam de posição. Ela busca compensar a inclinação residual do diagrama da célula. Isso não significa fases exatamente idênticas nas seis portas carregadas: as fases efetivas são listadas abaixo, e as duas fontes externas permanecem 0°.

{mask_text}

![Layout]({args.final}/layout.png)

| Trecho em cada polarização | Z de síntese (Ω) | Largura (mm) | Comprimento da linha central (mm) |
|---|---:|---:|---:|
{chr(10).join(trace_rows)}

Os valores de Z são de síntese de microstrip uniforme; curvas, junções, transições e acoplamento são calculados no HFSS. A/B mantêm geometria espelhada e fontes iguais/em fase. Nenhuma matriz foi simetrizada para melhorar artificialmente o resultado.

## Histórico das geometrias

Cada candidato abaixo é uma geometria própria, limitada a seis passes. Não houve continuação de um candidato além desse limite. BasisOrder1=primeira ordem, 2=segunda ordem, −1=mista. C03 e C04 também diferem na discretização; sua comparação não isola exclusivamente a contribuição da máscara. O parâmetro PercentRefinement consta na configuração de cada caso, e não representa necessariamente o crescimento efetivo da malha.

| Caso | BasisOrder | Passes / ΔS | Consecutivos | VSWR ativo A / B | G frontal (dBi) | Dispersão amplitude (dB) / fase (°) |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

A separação de perdas foi obtida por pós-processamento dos campos existentes, com as oito ondas incidentes correspondentes ao circuito carregado, sem novo solve. Na C03, a diferença de potência de 0,129506 W contém **0,082144 W radiados pelo divisor** e aproximadamente 0,047362 W dissipados. Isso motivou a C05: tampa/parede de alumínio AL5052 nominal, espessura 1 mm, tampa 6 mm acima das trilhas e contato elétrico contínuo ideal com a borda da massa. Essa C05 também ajusta o transformador central; não é uma comparação de uma única variável.

A C05 convergiu em cinco passes e atingiu **13,1596 dBi**, VSWR ativo **1,1644/1,0633**, mas máximo V **−0,37°**. Seu balanço apresenta 0,049540 W de perda total, dos quais apenas 0,000046 W radiados pelo divisor. A geometria com blindagem fica preservada como alternativa, com contato e montagem ainda nominais. Após o usuário aceitar 12 dBi, a centragem do lóbulo principal passou a ser a prioridade da versão sem tampa. O pequeno ajuste de fase foi feito em cobre, sem mudar os ângulos ou normalizar artificialmente os diagramas.

Na versão selecionada: **{hist[-1]['tetraedros']} tetraedros**, **14 núcleos em todos os passes**, Classic, sem MeshLink, sem operações locais de pré-refinamento, sem refinamento lambda e solver iterativo residual 1×10⁻⁵. A convergência exige dois passes consecutivos; a flag genérica `Converged: Yes` do HFSS não substitui esse contador. Reparos Major/Minor: **{r['malha_major']}/{r['malha_minor']}**. Evidências: [histórico]({args.final}/historico_passes.json), [convergência]({args.final}/convergencia.txt), [recursos]({args.final}/recursos_matriz.json).

## Equilíbrio e circuito

O campo foi recomposto com as excitações efetivas calculadas após todas as reflexões múltiplas. A potência abaixo é a onda incidente em cada porta da antena, não a potência líquida absorvida. As fontes externas permanecem 0,5 W / 0° em todos os casos.

| Porta | Potência da onda incidente (W) | Fase relativa a R2_A (°) |
|---|---:|---:|
{chr(10).join(wave_rows)}

![Equilíbrio carregado]({args.final}/balanceamento.png)

Para 1 W incidente: potência refletida **{r['potencia_refletida_W']:.7f} W**; potência líquida aceita pela antena **{r['potencia_aceita_antena_W']:.7f} W**; diferença no divisor **{r['perda_divisor_dissipacao_mais_radiacao_W']:.7f} W**. A diferença inclui dissipação e radiação do divisor, sem separação por mecanismo. A recomposição das fontes uniformes confere com o campo original da antena; a interconexão foi verificada por solução matricial, scikit-rf e Nexxim (erro máximo **{nx['erro_absoluto_max']:.3g}**).

Maior valor singular S8: **{r['passividade_divisor']:.8f}**; erro de reciprocidade S8: **{r['reciprocidade_divisor']:.7g}**. Referência estrita de reciprocidade dos estudos anteriores: 1×10⁻⁵. As matrizes e as limitações são preservadas tal como exportadas.

![Diagramas polares E/Emax]({args.final}/polar_HV.png)

![Comparação de ganho]({args.final}/comparacao_HV.png)

![Detalhe do máximo vertical e simetria]({args.final}/vertical_centro_fino.png)

O pico V foi conferido reexportando os campos já resolvidos da antena em −2°…+2°, passo **0,01°**. O máximo amostrado está em **{fine['pico_V_grade_graus']:+.2f}°**; estimativa interpolada **{fine['pico_V_interpolado_graus']:+.5f}°**. Diferença de ganho entre pico e zero: **{fine['diferenca_pico_zero_dB']:.8f} dB**. A concordância de ganho com a grade original nos ângulos coincidentes é **{fine['erro_ganho_grade_antiga_dB']:.3g} dB**. A grade angular mais fina não refina a malha FEM nem comprova tolerância de fabricação.

Na região comum de −3 dB, a maior diferença entre +θ e −θ é **{fine['assimetria_max_lobo_3dB_comum_dB']:.4f} dB**; o ponto médio dos dois cruzamentos de −3 dB é **{fine['centro_cruzamentos_3dB_graus']:+.4f}°**. O usuário confirmou que os lóbulos secundários serão apenas documentados nesta etapa, priorizando o lóbulo principal. A centragem nominal não garante zero exato após tolerâncias de placa, cabos e montagem.

O corte H da antena de referência tem topo amplo com dois máximos próximos de ±19°; a mudança de lado do maior pico não deve ser interpretada isoladamente como deslocamento significativo do feixe. Aberturas medidas a −3 dB. Os diagramas são os campos da antena recompostos: não somam a radiação direta do divisor nem seu acoplamento espacial com o refletor.

## Arquivos e reprodução

[HFSS]({args.final}/Divisor_Duplo3.aedt) · [FreeCAD]({args.final}/Divisor_Duplo3.FCStd) · [S8]({args.final}/divisor.s8p) · [S2 carregado]({args.final}/conjunto.s2p) · [Resultados]({args.final}/resultado.json) · [Circuito portátil Nexxim]({args.final}/circuito/P2S13_Divisor_EM_sem_malhas.aedtz).

Os nativos são modelos editáveis, sem solução FEM arquivada. O AEDTZ de circuito inclui Touchstones externos e exclui resultados/malhas. S6 original SHA-256 `{r['S6_sha256']}`. O [manifesto](manifesto.json) registra origem, tamanho e SHA-256. Os dados volumétricos, malhas, g3derr e locks permanecem locais e não entram no Git. Estes arquivos não constituem Gerbers aprovados.

Scripts: `divisor3_corrigir_preparar.py`, `divisor3_em_cad.py`, `divisor3_em_hfss.py`, `divisor3_em_analisar.py`, `divisor3_corrigir_resumir.py`, `divisor3_em_nexxim.py` e este empacotador. Usar `P2S13_DIV3_ROOT` em diretório próprio e `P2S13_DIV3_PARAM` com os parâmetros preservados; a criação recusa sobrescrever um nativo existente.

Fontes: [materiais e ENIG para RF na JLC](https://jlcpcb.com/pcb-fabrication/high-frequency-pcb), [acabamento somente nas aberturas da máscara](https://jlcpcb.com/blog/basic-design-of-solder-mask), [parâmetros genéricos de máscara JLC](https://cart.jlcpcb.com/client/template/placeOrder/impedance.html), [perdas e limitações da máscara em RF — Rogers](https://www.rogerscorp.com/blog/2020/finding-the-right-solder-mask-for-rfmicrowave-pcbs). Não foi solicitada compra nem nova cotação.
'''
OUT.mkdir(exist_ok=True)
(OUT / 'README.md').write_text(md, encoding='utf8')
records = []
direct = ['Divisor_Duplo3.aedt', 'Divisor_Duplo3.FCStd', 'HFSS_14nucleos.acf', 'configuracao.json',
          'hfss_validacao.json', 'estado.json', 'convergencia.txt', 'historico_passes.json', 'recursos_matriz.json',
          'mensagens.json', 'malha.json', 'resultado.json', 'diagnostico_balanceamento.json',
          'divisor.s8p', 'divisor_ordenado.s8p', 'conjunto.s2p', 'diagrama_H.csv', 'diagrama_V.csv',
          'layout.png', 'polar_HV.png', 'comparacao_HV.png', 'balanceamento.png']
def copy(p, dest):
    assert p.is_file(), p
    assert not any(t in str(p).lower() for t in ['.aedtresults', '.g3derr', '.lock'])
    if p.suffix == '.aedtz' and zipfile.is_zipfile(p):
        with zipfile.ZipFile(p) as z:
            assert not any('.aedtresults' in n or n.endswith(('.ngmesh', '.g3derr', '.lock')) for n in z.namelist())
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, dest)
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    assert hashlib.sha256(dest.read_bytes()).hexdigest() == sha
    records.append(dict(arquivo=dest.relative_to(REPO).as_posix(), fonte=str(p), sha256=sha, bytes=p.stat().st_size))
for p in cases:
    paths = [p / n for n in direct] + list((p / 'cad').glob('*.json')) + list((p / 'cad').glob('*.step'))
    for optional in ['decisao_setup.json','diagnostico_perdas.json','quantidades_perdas.json','plano_centragem_vertical.json','vertical_centro_fino.json','vertical_centro_fino.csv','vertical_centro_fino.png']:
        if (p / optional).exists(): paths.append(p / optional)
    if (p / 'circuito').exists():
        paths += [q for q in (p / 'circuito').iterdir() if q.is_file() and q.suffix in ['.aedt', '.aedtz', '.s8p', '.s6p', '.s2p', '.json']]
    for q in paths: copy(q, OUT / p.name / q.relative_to(p))
for n in ['comparacao.json', 'fontes_mascara.json','objetivos.json','calibracao_c07.json','parametros_c07.json']:
    if (BASE / n).is_file(): copy(BASE / n, OUT / n)
for p in (BASE/'antena_grade_fina').glob('*'):
    if p.is_file() and p.suffix in ['.json','.csv']: copy(p,OUT/'antena_grade_fina'/p.name)
(OUT / 'manifesto.json').write_text(json.dumps(dict(caso_selecionado=args.final, artefatos=records,
    total_bytes=sum(x['bytes'] for x in records)), ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print('ENTREGA_PRONTA', len(records), 'arquivos', args.final)
