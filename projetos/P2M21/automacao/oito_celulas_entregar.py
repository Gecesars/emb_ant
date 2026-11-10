"""Relata e arquiva R14 apenas depois da exportacao/auditoria; nunca inicia solve."""
from pathlib import Path
import json,hashlib,shutil,csv
ROOT=Path('D:/dev/EMBRAER/P2M21/R14_Oito_Celulas')
REPO=Path(__file__).resolve().parents[3]
DEST=REPO/'projetos/P2M21/oito_celulas_4_elementos'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cfg=read('configuracao.json');r=read('resultado.json');q=read('qualificacao.json')
assert q['estado']=='ANALISE_CONCLUIDA'
assert not (ROOT/(cfg['native']+'.lock')).exists(),'Esperar fechamento do projeto'
qa=read('revisao_visual.json')
assert qa['aprovado'] and all(sha(ROOT/x['arquivo'])==x['sha256'] for x in qa['arquivos']),'Revisar imagens atuais'
h,v=r['cortes']['H'],r['cortes']['V'];comparison=read('comparacao.json')
status='CONVERGIU EM DELTA S; checagens fisicas aprovadas' if r['validado_numericamente'] else 'PRELIMINAR / NAO VALIDADO'
table='\n'.join('| '+ ' | '.join([c['versao'],f"{c['ganho_dBi']:.4f}",f"{c['H_graus']:.4f}",f"{c['V_graus']:.4f}",f"{c['picoH_graus']:+.2f}",f"{c['picoV_graus']:+.2f}"])+' |' for c in comparison)
ports='\n'.join(f"| {n} | {r['VSWR_ativo'][i]:.4f} | {r['VSWR_casado'][i]:.4f} |" if r['VSWR_ativo'][i] is not None and r['VSWR_casado'][i] is not None else f"| {n} | Gamma >=1; VSWR convencional nao definido | — |" for i,n in enumerate(r['ordem_portas']))
history=read('historico_passes.json')['historico']
def fmt(value,n=6):return '—' if value is None else f'{value:.{n}f}'
history_table='\n'.join(f"| {p['passe']} | {p['tetraedros']} | {fmt(p['delta_s'])} | {fmt(p['campos_dBi'].get('R14_Campo_00'),4)} | {fmt(p['delta_campo_max_dB'],4)} |" for p in history)
gain_met='sim' if r['metas']['ganho_total_21dBi'] else 'nao'
point_met='sim' if r['metas']['apontamento_H'] and r['metas']['apontamento_V'] else 'nao'
fallback=r['solver_efetivo']['avisos_troca_automatica_direto']
solver_note=(f'O perfil nativo registrou **{fallback} avisos de troca automática do solver iterativo para o direto** por convergência lenta. Os registros de Matrix Solve e os núcleos efetivamente empregados estão em [solver_efetivo.json](solver_efetivo.json); a execução não permaneceu exclusivamente iterativa.' if fallback else 'O perfil nativo não registrou troca automática do solver iterativo para o direto.')
md=f'''# R14 — oito placas 4_elementos como células do painel 16 × 2

Estudo de **10/11/2026**, **{status}**. Resultado com todas as **16 portas a 0,0625 W / 0°**, total de **1 W incidente**, em **5,17 GHz**. **{r['passes']} passes**, ΔS final **{r['delta_s']:.7f}**, alvo 0,05, limite seis, {r['consecutivos']} passes consecutivos atendendo ao alvo. **14 núcleos**, sem GUI e sem sweep.

## Resultado e comparação solicitada

| Modelo | Ganho frontal total (dBi) | H −3 dB (°) | V −3 dB (°) | Pico H (°) | Pico V (°) |
|---|---:|---:|---:|---:|---:|
{table}

O ganho numérico total atinge 21 dBi: **{gain_met}**. Os dois máximos ficam dentro de ±0,5°: **{point_met}**. SLL horizontal **{h['SLL']['nivel_dB']:.3f} dB**; SLL vertical **{v['SLL']['nivel_dB']:.3f} dB**, considerados os máximos locais no hemisfério frontal fora dos primeiros mínimos do lobo principal. Os picos são amostras da grade de 0,25°, não máximos 3D otimizados.

**A referência R04 com 64 portas individuais não convergiu**: ΔS 0,110424 e inconsistência de eficiência acima de 100%. Seus números são históricos, não uma referência validada. Além da modularização, mudaram passo vertical **52,6 → 48 mm**, horizontal **40 → 72 mm**, altura da PCB, refletor e presença dos divisores impressos/cabos. A comparação não atribui toda diferença à adoção das células.

A estimativa auxiliar usando o campo da C12 isolada e fator de arranjo previu **21,4875 dBi**, H **22,3252°**, V **3,8134°**. Ela não inclui acoplamento entre células nem o novo refletor. O resultado R14 acima provém do painel completo em FEM, não dessa estimativa.

![Comparação H/V](comparacao_diagramas.png)

![Polar E/Emax](polar_HV.png)

## Modelo físico montado

Oito cópias da **C12 R13 / KiCad 4_elementos**, organizadas em **quatro níveis de placas × duas colunas**. Cada placa contém quatro radiadores e dois divisores 1:4 impressos, um por polarização. Resultam **16 níveis de radiadores × duas colunas = 32 radiadores**, com 16 conexões coaxiais.

| Parâmetro | Valor |
|---|---|
| Dimensões de cada PCB | 70 × 184 mm |
| Passo vertical dos radiadores | 48 mm, inclusive entre placas |
| Centros verticais das placas, X HFSS | −288, −96, +96, +288 mm |
| Centros horizontais, Y HFSS | −36, +36 mm; passo de 72 mm aprovado pelo usuário |
| Folgas entre placas | 8 mm vertical / 2 mm horizontal |
| Envolvente das oito PCBs | 142 × 760 mm |
| Refletor contínuo | Alumínio, 162 × 776 × 2 mm, 16 furos Ø4,2 mm para coaxiais |
| Face inferior do núcleo acima do refletor | 14,949 mm; cobre inferior em 14,914 mm |
| Cabos | 16 trechos retos de 50 mm, iguais aos da C12, com perdas físicas nominais |
| RO4350B | Núcleo 0,76 mm, εr 3,66 e tanδ 0,0037 |
| Metalização | Cu físico 35 µm; ENIG nominal Au 0,0254 µm / NiP 4,5 µm |
| Ausentes nesta etapa | Rede externa de distribuição, conectores N, apoios plásticos e radome |

As oito células mantêm a mesma orientação e a geometria dos sólidos C12; não foram espelhadas nem redesenhadas. Os oito refletores locais foram substituídos por uma chapa comum. O CAD tem **329 sólidos válidos**, **600 pares** de caixas sobrepostas examinados e **zero interseções indevidas**. O projeto foi reaberto para verificar persistência. A importação HFSS preservou nomes/quantidades por material e passou na validação nativa com 16 portas e sem erros de configuração.

![Cobre das duas faces projetado na vista frontal](montagem_duas_faces.png)

## Alimentação, acoplamento e futura rede

Portas lumped em 50 Ω nas extremidades dos cabos, sem de-embedding, com sentido de integração idêntico ao da C12. Todas recebem igual onda incidente e fase zero. Há **oito conexões A e oito B**. O modelo resolve conjuntamente PCBs, redes impressas, cabos e refletor, incluindo o acoplamento entre as células. Não se trata de repetição periódica infinita.

Foram exportados **S16** e **32 cortes complexos embutidos**, H/V para cada porta a 1 W com as outras casadas, além dos casos com todas ativas e com cada grupo de polarização ativo. Estes dados preservam a interface para o próximo estudo de distribuição. Os grupos A/B usam oito fontes coerentes de 0,125 W, total de 1 W por ensaio, sem divisor externo real; não comprovam ganho MIMO por entrada do sistema acabado.

Os CSVs foram exportados após selecionar explicitamente as fontes de cada caso. O projeto nativo foi salvo com **todas as 16 fontes ativas**. No HFSS, os relatórios usam a excitação corrente: para reproduzir um CSV individual ou de um grupo, selecionar novamente esse caso com `EditSources`, conforme `oito_celulas_resolver.py`; o nome do relatório sozinho não fixa a alimentação.

**A rede de duas entradas independentes para 16 conexões não foi projetada nesta etapa**, conforme a sequência solicitada. A etapa seguinte deve partir do estado de convergência e dos diagramas desta entrega, sem declarar o painel aprovado apenas pelo ganho.

| Conexão | VSWR ativo com as 16 fontes | VSWR com demais portas casadas |
|---|---:|---:|
{ports}

![Acoplamento e casamento das 16 conexões](acoplamento_vswr.png)

## Convergência e qualidade numérica

Classic automático, slider global 5, sem controles locais, sem MeshLink e sem LambdaRefine inicial. **BasisOrder=1 (First Order, primeira ordem)**, solver configurado como iterativo com residual 1e−5, adaptação de **20% durante o cálculo**, mínimo dois/máximo seis passes e dois passes consecutivos em ΔS ≤0,05. A célula isolada usa **BasisOrder=2 (Second Order, segunda ordem)**. A ordem menor foi escolhida para limitar o custo do painel; essa diferença numérica também impede atribuir a diferença de ganho somente à montagem. A geometria e os materiais das células foram preservados. Nenhum limite de passes foi ampliado nesta execução. A nomenclatura foi conferida no enum `BasisOrder` do PyAEDT instalado: Zero=0, Single=1, Double=2 e Mixed=−1.

{solver_note}

| Passe | Tetraedros | Máximo ΔS | Ganho frontal monitorado (dBi) | Maior variação nas 9 direções monitoradas (dB) |
|---:|---:|---:|---:|---:|
{history_table}

As nove direções de campo são monitoramento, não um critério adicional de parada. O ganho frontal do último cache confere com a exportação explícita das 16 fontes: **{r['cache_confere_fontes_finais']}**. Para classificar a estabilidade observada, verificou-se variação ≤0,1 dB nas nove direções em ambas as últimas transições: **{r['estavel_nove_sondas']}**. A falta de estabilidade mantém o resultado preliminar e não aciona novos passes. ΔS compara soluções adaptativas e não é garantia de erro físico percentual. Não foi realizado estudo independente de refinamento adicional; não confundir convergência de S com validação experimental.

Malha: **{r['major']} Major / {r['minor']} Minor**. Maior valor singular de S: **{r['maior_singular']:.8f}**; máximo |S−Sᵀ|: **{r['reciprocidade']:.3g}**. Potência aceita: **{r['potencia_aceita_W']:.7f} W**. Eficiência de radiação: **{100*r['potencia']['H']['eficiencia_radiacao']:.4f}%**; total: **{100*r['potencia']['H']['eficiencia_total']:.4f}%**. Erro máximo da recomposição dos 16 campos: **{max(r['recomposicao'].values()):.3g}**. Erro de potência aceita entre S e razões de ganhos: **{max(x['erro_aceita_W'] for x in r['potencia'].values()):.3g} W**.

Checagens físicas aprovadas: **{r['fisica_ok']}**. Limites: singular ≤1,0001, reciprocidade ≤1e−5, eficiência ≤1,0001, diferença de potência <1e−4 W e zero Major. Todas as métricas e ressalvas permanecem em [resultado.json](resultado.json), inclusive quando reprovadas.

## Arquivos e reprodução

- [Projeto HFSS](P2M21_8celulas.aedt) · [Montagem FreeCAD](P2M21_8celulas.FCStd).
- [S16 em 5,17 GHz](centro.s16p) · [Comparação CSV](comparacao.csv) · [Histórico adaptativo](historico_passes.json).
- [Configuração e posições](configuracao.json) · [Mapa das 16 portas](cad/portas.json) · [Manifesto](manifesto.json).
- [Célula e Gerbers preservados](../kicad/4_elementos/README.md) · [Referência individual R04](../centro_sem_refinamento/continuacao_6_passes/README.md).
- Scripts `oito_celulas_*.py` e [pipeline](../automacao/oito_celulas_pipeline.ps1) em `../automacao/`.

Os nativos e dados compactos são arquivados; `.aedtresults`, malhas, diagnósticos triangulados, locks e campos volumétricos permanecem fora do Git. A solução FEM restaurável permanece em **D:/dev/EMBRAER/P2M21/R14_Oito_Celulas**; o `.aedt` isolado exige novo solve para restaurar esses campos. Não houve sweep, nova fabricação, cotação ou envio de email nesta etapa.
'''
(ROOT/'README.md').write_text(md,encoding='utf-8',newline='\n')
DEST.mkdir(parents=True,exist_ok=True)
names=[cfg['native'],'P2M21_8celulas.FCStd','configuracao.json','qualificacao.json','hfss_validacao.json',
    'HFSS_14nucleos.acf','setup_conferido.json','ordem_fontes.json','convergencia.txt','centro.s16p','resultado.json','historico_passes.json',
    'recursos_matriz.json','solver_efetivo.json','malha.json','mensagens.json','comparacao.json','comparacao.csv','estimativa.json','estimativa_H.csv','estimativa_V.csv',
    'montagem_frontal.png','montagem_duas_faces.png','estimativa_inicial.png','comparacao_diagramas.png','polar_HV.png','acoplamento_vswr.png','revisao_visual.json','README.md']
names += [p.name for p in ROOT.glob('*.csv') if p.name not in names]
names += ['cad/'+p.name for p in (ROOT/'cad').glob('*.json')]
for name in names:
    p=DEST/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,p)
manifest=dict(revisao=cfg['revisao'],fonte_celula=cfg['fontes_sha256'],
    arquivos=[dict(arquivo=n,bytes=(ROOT/n).stat().st_size,sha256=sha(ROOT/n)) for n in sorted(set(names))])
(DEST/'manifesto.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(DEST,len(names),'arquivos',sum((ROOT/n).stat().st_size for n in set(names)),'bytes')
