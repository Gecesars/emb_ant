"""Documenta resultado real e copia artefatos compactos; não faz novo solve."""
from pathlib import Path
import json, hashlib, shutil, csv
ROOT=Path('D:/dev/EMBRAER/P2M19/R01_16x2_88mm')
REPO=Path(__file__).resolve().parents[3]
OUT=REPO/'projetos/P2M19/centro_16x2_88mm'
cfg=json.loads((ROOT/'configuracao.json').read_text())
r=json.loads((ROOT/'resultado.json').read_text())
assert r['passes']<=6 and r['nucleos']==14 and r['frequencia_GHz']==5.17
c=r['cortes'];f=r['cortes_finos']
state='Convergência ΔS atendida' if r['convergiu'] else 'PRELIMINAR — não convergiu dentro do limite de seis passes'
g=c['H']['ganho_frontal_dBi'];h=f['H']['abertura_graus'];v=f['V']['abertura_graus']
lines=['# P2M19 R01 — resultado em 5,17 GHz','',f'**{state}.** Ganho frontal realizado total **{g:.4f} dBi**, abertura H **{h:.4f}°**, abertura V **{v:.4f}°**.',
 '',f"Execução de 13/11/2026, {r['passes']} passes de um máximo de seis, ΔS final **{r['delta_s']:.8f}**, {r['consecutivos']} passes consecutivos convergidos. Alvo ΔS=0,05. Perfil conferido: 14 núcleos em todos os passes; solver direto, First Order, Classic com elementos curvilíneos. Sem sweep.",
 '', '| Grandeza | Resultado | Comparação |','|---|---:|---|',
 f'| Ganho frontal total | {g:.4f} dBi | Meta ≥19 dBi: {"atingida numericamente" if g>=19 else "não atingida"} |',
 f'| Abertura H, −3 dB | {h:.4f}° | Desvio de 20°: {h-20:+.4f}° ({100*(h/20-1):+.2f}%) |',
 f'| Abertura V, −3 dB | {v:.4f}° | Informativo; não exigidos 20° nesta execução |',
 f"| Máximo H / V (interpolado) | {f['H']['pico_interpolado_graus']:+.4f}° / {f['V']['pico_interpolado_graus']:+.4f}° | Amostras centrais a cada 0,05° |",
 f"| VSWR ativo, mínimo / máximo | {min(r['VSWR_ativo']):.4f} / {max(r['VSWR_ativo']):.4f} | Dezesseis entradas simultâneas |",
 f"| VSWR com outras entradas casadas, máximo | {max(r['VSWR_casado']):.4f} | Referência 50 Ω |",
 f"| Maior lóbulo secundário H / V | {c['H']['SLL']['nivel_dB']:.3f} / {c['V']['SLL']['nivel_dB']:.3f} dB | Hemisfério frontal; relativo ao pico de cada corte |", '',
 'O cumprimento numérico das metas não substitui convergência e consistência física. Não foi atribuída uma tolerância de aprovação à expressão “H próxima de 20°”; o desvio é reportado diretamente.',
 '', f"**Atenção ao diagrama horizontal:** a largura de {h:.2f}° é a do lóbulo principal. Existe outro lóbulo frontal em −37° com nível de {c['H']['SLL']['nivel_dB']:.2f} dB relativo ao pico. Portanto o painel apresenta radiação lateral forte, apesar da largura central próxima de 20°. Todos esses valores permanecem preliminares.",
 '', '![Diagramas polares E/Emax](polar_HV.png)', '', '![Cortes e referência histórica](comparacao_diagramas.png)',
 '', '## Excitação, geometria e perdas', '',
 'Oito placas C12 de quatro elementos, quatro por coluna: 16 níveis × duas colunas, 32 radiadores. Dezesseis portas locais de 50 Ω, cada uma com 0,0625 W a 0°, total 1 W. Ganho total coerente; não caracteriza MIMO por entrada.',
 '', 'Passos: 48 mm entre radiadores verticais, 192 mm entre centros das placas e 88 mm entre colunas. PCBs 70 × 184 mm, folgas 8 mm na vertical / 18 mm na horizontal. Envelope das placas 158 × 760 mm. Refletor comum plano de alumínio 5052: 178 × 776 × 2 mm. Laminado a 14,949 mm da face superior do refletor.',
 '', 'Divisores impressos das placas preservados, com perdas de RO4350B (núcleo 0,76 mm, εr 3,66, tanδ 0,0037), cobre 35 µm e ENIG nominal Au 0,0254 µm / NiP 4,5 µm. Sem rede externa 1:8, cabos em 3D, conectores N, radome ou suportes plásticos. Terminais locais de 0,18 mm e soldas preservados. Os ganhos não incluem a futura distribuição externa.',
 '', '![Geometria das oito placas](montagem_duas_faces.png)',
 '', 'A comparação R15 é histórica e preliminar: além do espaçamento horizontal, mudaram a largura do refletor e a remoção dos cabos de 50 mm. Portanto não isola o efeito do espaçamento.',
 '', '## Auditoria', '',
 f"- Consistência física: **{r['fisica_ok']}**; balanço de potência: **{r['balanco_potencia_valido']}**.",
 f"- Reparos de malha: Major={r['major']}, Minor={r['minor']}.",
 f"- Maior valor singular de S: {r['maior_singular']:.8f}; resíduo de reciprocidade: {r['reciprocidade']:.3e}.",
 f"- Erro relativo máximo da recomposição de campos: {max(r['recomposicao'].values()):.3e}.",
 f"- Estabilidade de nove campos nas duas últimas adaptações, limite informativo 0,1 dB: **{r['estavel_nove_sondas']}**. Essa monitoração não aumentou o número autorizado de passes.",
 f"- Avisos do solver matricial: {len(r['avisos_solver_matricial'])}.",
 '', 'A importação confere volume/envelope dos 329 sólidos; CAD sem interpenetrações em 552 pares examinados. Portas conferidas quanto a contatos e polaridade sinal→referência. Aberturas interpoladas entre amostras, sem alegar precisão física superior à malha.',
 '', '## Arquivos', '',
 '[Projeto HFSS](P2M19_16x2_88mm.aedt) · [CAD da geometria EM](P2M19_16x2_88mm.FCStd) · [Resultado completo](resultado.json) · [S16](centro.s16p) · [Configuração](configuracao.json).',
 '', 'Dados somente em 5,17 GHz; não qualificam a banda 5,09–5,25 GHz, tolerâncias de fabricação ou protótipo. Resultados volumétricos/malhas permanecem somente em `D:/dev/EMBRAER/P2M19/R01_16x2_88mm` e não são copiados ao repositório.']
if 'balanco_potencia' in r:
    lines+=['','Potências (W): '+', '.join(k+'='+format(x,'.8f') for k,x in r['balanco_potencia'].items())+'.']
lines+=['','Os contextos de esfera HV e Centro_fino apresentam diferença frontal máxima de '+format(max(abs(x['diferenca_frontal_dB']) for x in r['consistencia_contextos'].values()),'.8f')+' dB. A verificação entre relatórios usa 0,001 dB; o limite inicial de 0,0000001 dB era mais estrito que a diferença numérica do próprio HFSS entre esses contextos. Não houve nova solução nem alteração de ΔS.']
history=json.loads((ROOT/'historico_passes.json').read_text())['historico']
lines+=['','## Evolução da malha','','| Passe | Tetraedros | ΔS | Ganho frontal monitorado (dBi) |','|---:|---:|---:|---:|']
for step in history:
    ds='—' if step['delta_s'] is None else format(step['delta_s'],'.8f')
    lines.append(f"| {step['passe']} | {step['tetraedros']} | {ds} | {step['campos_dBi']['P2M19_Campo_00']:.6f} |")
if (ROOT/'evidencias/curvilinear_inicial.txt').exists():
    lines+=['','O diagnóstico da malha inicial registrou uma face curva rebaixada para representação linear (uma entre 1.216 faces curvas). A configuração curvilínea permaneceu ativa; o registro original está em [curvilinear_inicial.txt](evidencias/curvilinear_inicial.txt).']
text='\n'.join(lines)+'\n'
(ROOT/'RELATORIO.md').write_text(text,encoding='utf-8')
OUT.mkdir(exist_ok=True)
files=['RELATORIO.md','configuracao.json','resultado.json','qualificacao.json',cfg['native'],cfg['cad_native'],'centro.s16p','convergencia.txt','mensagens.json','ordem_fontes.json','HFSS_14nucleos.acf','malha.json','historico_passes.json','recursos_matriz.json','solver_efetivo.json','potencia.json','hfss_validacao.json','geometria_importada.json','polar_HV.png','comparacao_diagramas.png','acoplamento_vswr.png','comparacao.csv']
files += ['montagem_frontal.png','montagem_duas_faces.png']
files += ['evidencias/curvilinear_inicial.txt']
files += ['pipeline.json','revisao_visual.json','evidencias/pipeline_analise_original.json','evidencias/recuperacao_analise.json']
files += [p.name for p in ROOT.glob('*.csv') if p.name not in files]
files += ['cad/'+n for n in ['manifesto.json','folhas_solidas.json','portas.json','intersecoes.json','reabertura.json','contatos_portas.json','geometria_esperada.json','enig_hfss.json']]
manifest=[]
for name in files:
    p=ROOT/name
    if not p.exists():continue
    q=OUT/name;q.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(p,q)
    assert p.read_bytes()==q.read_bytes()
    manifest.append(dict(arquivo=name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(OUT/'README.md').write_text(text,encoding='utf-8')
(OUT/'manifesto.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(dict(estado=state,ganho=g,H=h,V=v,delta_s=r['delta_s'],arquivos=len(manifest)),ensure_ascii=False,indent=2))
