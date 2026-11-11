"""Relatorio do conjunto de tres placas2, separando alvo nominal e validacao."""
from pathlib import Path
import json
REPO=Path(__file__).resolve().parents[3];ROOT=Path('D:/dev/EMBRAER/P2S13/R05_Tres_Placas2');OUT=REPO/'projetos/P2S13/tres_placas2';OUT.mkdir(exist_ok=True)
d=json.loads((ROOT/'comparacao.json').read_text());rows=d['resultados'];best=min(rows,key=lambda r:abs(r['erro_H_frente_100_graus']))
table=[]
for r in rows:
    table.append('| [b%g / %g°](%s/resultado.json) | %.3f | %.2f | %+.2f | %.2f | %.4f / %.4f | %d / %.5f | %s |'%(r['b_mm'],r['angulo_graus'],r['caso'],r['G_frontal_dBi'],r['H_graus'],r['erro_H_frente_100_graus'],r['V_graus'],r['VSWR_ativo_max'],r['VSWR_casado_max'],r['passes'],r['DeltaS'],'Sim' if r['convergiu_S'] else 'Não'))
r=json.loads((ROOT/best['caso']/'resultado.json').read_text());c=json.loads((ROOT/best['caso']/'configuracao.json').read_text())
history=json.loads((ROOT/best['caso']/'historico_passes.json').read_text())['historico']
phases=next(x for x in d['contribuicoes'] if x['caso']==best['caso'])['fases_campos_frontais_vs_placa_central_graus']
ports=['| %s | %.5f | %.5f |'%(n,a,b) for n,a,b in zip(r['ordem_portas'],r['VSWR_ativo'],r['VSWR_casado'])]
text=f'''# P2S13 — três placas idênticas de dois elementos

O usuário encerrou a composição 4+2 e pediu três PCBs de dois elementos idênticas, buscando **100° de abertura horizontal**. A campanha anterior está [preservada e bloqueada contra retomada](../dobras_placas_ajustadas/README.md).

**Caso mais próximo do alvo calculado: b={best['b_mm']:g} mm / {best['angulo_graus']:g}°, H={best['H_graus']:.2f}°, ganho frontal={best['G_frontal_dBi']:.3f} dBi.** Desvio frente a100°: {best['erro_H_frente_100_graus']:+.2f}°. Aproximação nominal de busca≤1°: {'atendida numericamente' if best['H_100_mais_menos_1grau'] else 'ainda não atendida'}. Aprovação numérica conjunta: **{'sim' if best['aprovado'] else 'não'}**. Não confundir proximidade ao alvo com convergência ou validação experimental.

## Montagem e condições

Três cópias da PCB2 ajustada, 50 × 88 mm, RO4350B de 0,76 mm, cobre de 35 µm e ENIG nominal. Transformadores simétricos de 0,546717 × 13,151813 mm. Centros das placas em X=−96,0,+96 mm; centros dos seis radiadores em −120,−72,−24,+24,+72,+120 mm. Passo de 48 mm e vãos entre PCBs de 8 mm. R1 é inferior, R2 central e R3 superior. Nenhum radiador, trilha ou divisor local foi alterado entre as cópias.

Seis cabos coaxiais físicos de 50 mm, seis portas de 50 Ω: **1/6 W a 0° em cada entrada, 1 W total**. Perdas de cobre/dielétrico/rede impressa/cabos incluídas. Sem conectores N, suportes plásticos ou rede externa. A mesma amplitude/fase nos acessos não elimina diferenças de acoplamento entre a placa central e as extremas.

Refletor de alumínio de 2 mm, comprimento de 296 mm e largura desenvolvida de 90 mm, raio interno de 2 mm e K nominal 0,4. `b` mede do eixo central ao início tangente de cada dobra; o ângulo é para trás (90°=abas paralelas a−Z). Altura inferior do núcleo das PCBs de 14,949 mm. As duas abas são simétricas.

**5,17 GHz, sem sweep, 14 núcleos, até 6 passes, ΔS≤0,05 por 2 passes consecutivos.** Classic automático, sem MeshLink ou refinamento local/lambda. A malha inicial é auditada separadamente, sem refinamento prévio imposto. Nove sondas de campo monitoram estabilidade em 0,1 dB. Não se ultrapassa o limite de passes para ocultar falta de convergência.

O alvo nominal atual é 100°; o intervalo histórico de ±10% foi registrado como 90–110°. Para ajustar perto do valor nominal, a busca usa desvio ≤1°, sem apresentar qualquer valor do intervalo amplo como se fosse 100°. Ganho de 13 dBi e VSWR ≤1,25 continuam verificados. A vertical é relatada; não há aprovação implícita da antiga meta de 18° ±10%.

![Montagem das três placas](montagem_tres_placas.png)

## Comparação dos ensaios reais

| Início / ângulo | G frontal dBi | H ° | Erro H ° | V ° | VSWR máx. ativo / casado | Passes / ΔS | Convergiu S |
|---|---:|---:|---:|---:|---:|---:|---|
{chr(10).join(table)}

Para o caso mais próximo: máximos H/V **{best['pico_H_graus']:+.2f}° / {best['pico_V_graus']:+.2f}°**, maior lóbulo secundário V **{best['SLL_V_dB']:.2f} dB**. Passes consecutivos em ΔS: **{best['consecutivos']}**; estabilidade das nove sondas: **{'atendida' if best['campos_estaveis'] else 'pendente'}**; auditoria de matriz/potência/malha: **{'atendida' if best['auditoria'] else 'reprovada, consultar resultado.json'}**.

O ganho em 0° está **{best['perda_frente_pico_H_dB']:.4f} dB** abaixo do pico horizontal; o ponto médio entre os cruzamentos de −3 dB fica em **{best['centro_cruzamentos_H_graus']:+.2f}°**. Esses valores descrevem o formato do lóbulo, sem substituir o ângulo real do máximo.

Última malha: **{history[-1]['tetraedros']} tetraedros**. Maior variação das nove sondas no último passe: **{history[-1]['delta_campo_max_dB']:.6f} dB**, contra o monitor de 0,1 dB. Diferença máxima de reciprocidade **|S−Sᵀ|={r['reciprocidade']:.8g}**, limite da auditoria **1×10⁻⁵**. A matriz é passiva; a potência aceita é **{r['potencia_aceita_W']:.6f} W**, a eficiência total é **{100*r['potencia']['H']['eficiencia_total']:.2f}%** e não há reparos Major/Minor. A falta de convergência e as ressalvas da auditoria impedem chamar este resultado de validado.

| Porta | VSWR ativo | VSWR demais casadas |
|---|---:|---:|
{chr(10).join(ports)}

![Diagramas comparados](comparacao_HV.png)

![Diagramas polares do caso mais próximo]({best['caso']}/polar_HV.png)

## Arquivos e limites

[HFSS do caso mais próximo]({best['caso']}/P2S13_TresPCB2.aedt) · [FreeCAD]({best['caso']}/P2S13_TresPCB2.FCStd) · [Tabela CSV](comparacao.csv) · [Resultados e fases dos campos embutidos](comparacao.json) · [Manifesto SHA-256](manifesto.json).

Os campos são a solução integral do conjunto, com acoplamento, e sua soma complexa é conferida contra o HFSS. O diagnóstico de fase usa projeção dos campos frontais de cada PCB sobre a placa central; não representa uma medição direta em cada dipolo. O ganho é realizado total em +Z para as seis entradas, não ganho MIMO por porta.

No caso selecionado, as fases dessas projeções para R1/R2/R3 são **{phases[0]:+.2f}° / {phases[1]:+.2f}° / {phases[2]:+.2f}°**. As três redes impressas idênticas eliminam a diferença nominal de percurso entre divisores 1:4 e 1:2; as diferenças residuais dos campos incluem o acoplamento e o erro numérico ainda relatado.

Nativos, S6, cortes/campos distantes e evidências compactas são arquivados, sem malhas, `.aedtresults`, locks ou campos volumétricos. O nativo preserva o modelo; restaurar a solução FEM completa exige os resultados locais. As propriedades do CAD são documentais; editar `configuracao.json` e reconstruir pelos scripts para alterar o BREP. Trabalho: `D:/dev/EMBRAER/P2S13/R05_Tres_Placas2`.
'''
for old,new in [('frente a100','frente a 100'),('busca≤1','busca ≤1'),('100°;','100°;'),('a−Z','a −Z')]:text=text.replace(old,new)
(OUT/'README.md').write_text(text,encoding='utf-8')
parent=REPO/'projetos/P2S13/README.md'
old=parent.read_text(encoding='utf-8')
marker='## Histórico anterior: oito níveis e composição 4+2'
if marker in old:
    history=old.split(marker,1)[1]
else:
    history='\n\n'+old.replace('# P2S13 — estudo do refletor para 110° horizontal\n','',1).replace('**Revisão atual, 11/11:','**Revisão histórica, 11/11:',1).lstrip()
summary=f'''**P2S13 — três PCBs idênticas de dois elementos, 11/11.** A composição 4+2 foi interrompida a pedido do usuário. O novo painel usa seis níveis a 48 mm, três placas a 96 mm e seis entradas de 1/6 W a 0°. Caso mais próximo do alvo de 100°: dobra a **{best['b_mm']:g} mm / {best['angulo_graus']:g}°**, ganho frontal **{best['G_frontal_dBi']:.3f} dBi**, H **{best['H_graus']:.2f}°**, V **{best['V_graus']:.2f}°**. VSWR máximo ativo/casado **{best['VSWR_ativo_max']:.4f}/{best['VSWR_casado_max']:.4f}**. **{best['passes']} passes, ΔS {best['DeltaS']:.6f}; convergência S: {'sim' if best['convergiu_S'] else 'não'}. Aprovação conjunta: {'sim' if best['aprovado'] else 'pendente'}.** 5,17 GHz, 14 núcleos, sem sweep, cabos físicos com perdas. Nenhum resultado não convergido é declarado validado.'''
parent.write_text('# P2S13 — três placas de dois elementos e alvo H100°\n\n'+summary+' [Resultados, diagramas e nativos](tres_placas2/README.md). [Campanha 4+2 encerrada](dobras_placas_ajustadas/README.md).\n\n'+marker+history,encoding='utf-8')
index=REPO/'README.md';old=index.read_text(encoding='utf-8');head,rest=old.split('\n\n',1)
assert rest.startswith('**P2S13')
_,tail=rest.split('\n\n',1)
index.write_text(head+'\n\n'+summary+' [Relatório e arquivos](projetos/P2S13/tres_placas2/README.md) · [Histórico interrompido 4+2](projetos/P2S13/dobras_placas_ajustadas/README.md).\n\n'+tail,encoding='utf-8')
(ROOT/'entrega.json').write_text(json.dumps(dict(estado='ALVO_H_APROXIMADO_PRELIMINAR' if best['H_100_mais_menos_1grau'] and not best['aprovado'] else 'APROVADO_NUMERICAMENTE' if best['aprovado'] else 'AJUSTE_H_PENDENTE',casos=len(rows),caso_mais_proximo=best['caso'],H_graus=best['H_graus'],erro_H_graus=best['erro_H_frente_100_graus'],alvo_nominal_mais_menos_1grau=best['H_100_mais_menos_1grau'],aprovado=best['aprovado']),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(best,indent=2))
