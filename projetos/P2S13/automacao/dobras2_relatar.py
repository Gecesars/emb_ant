"""Documenta os ensaios finalizados, inclusive reprovacoes; nenhuma escolha implicita de fabricacao."""
from pathlib import Path
import json
REPO=Path(__file__).resolve().parents[3];ROOT=Path('D:/dev/EMBRAER/P2S13/R04_Dobras_Ajustadas');OUT=REPO/'projetos/P2S13/dobras_placas_ajustadas';OUT.mkdir(exist_ok=True)
d=json.loads((ROOT/'comparacao.json').read_text());rows=d['resultados'];assert len(rows)>1
valid=[r for r in rows if r['aprovado']];numerical=[r for r in rows if r['metas_RF']]
eligible=[r for r in rows if r['meta_VSWR']];best=min(eligible or rows,key=lambda r:(abs(r['H_graus']-110),-r['G_frontal_dBi']))
verdict='Existe candidato aprovado nos criterios desta etapa.' if valid else ('Ha candidato que atende numericamente, mas a qualificacao numerica permanece pendente.' if numerical else 'Nenhum dos casos calculados atende simultaneamente a abertura horizontal, ganho e VSWR solicitados.')
table=[]
for r in rows:
    link='../continuacao_placa2/README.md' if r['caso'].startswith('referencia') else r['caso']+'/resultado.json'
    table.append('| [b%g / %g°](%s) | %.3f | %.2f | %.2f | %.4f / %.4f | %d / %.5f | %s |'%(r['b_mm'],r['angulo_graus'],link,r['G_frontal_dBi'],r['H_graus'],r['V_graus'],r['VSWR_ativo_max'],r['VSWR_casado_max'],r['passes'],r['DeltaS'],'Sim' if r['convergencia_S'] else 'Não'))
details=[]
for r in rows:
    details.append('- **b%g / %g°:** máximo H %+.2f°, V %+.2f°; lóbulo secundário V %.2f dB; %d passes consecutivos em ΔS; estabilidade das nove sondas %s; auditoria de matriz/potência/malha %s.'%(r['b_mm'],r['angulo_graus'],r['pico_H_graus'],r['pico_V_graus'],r['SLL_V_dB'],r['consecutivos'],'atendida' if r['campos_estaveis'] else 'pendente','atendida' if r['auditoria'] else 'reprovada'))
text='''# P2S13 — ajuste das dobras com as PCBs já casadas

**{verdict}** Estudo central em 5,17 GHz, sem sweep. Não há liberação de banda, fabricação ou medição experimental implícita.

## Método e parâmetros

Foram alterados somente **b**, a distância do eixo central Y=0 até o início tangente da dobra, e o **ângulo das abas para trás**. São duas dobras simétricas. 0° seria plano; 90° significa abas paralelas à direção frontal, para −Z; acima de 90° as abas se aproximam do eixo na parte traseira. A figura usa as mesmas equações de CAD/HFSS.

Mantidos: alumínio de 2 mm, largura desenvolvida 90 mm, comprimento 296 mm, raio interno 2 mm e K nominal 0,4. A face inferior das PCBs fica em Z=14,949 mm. Uma PCB C12 de quatro elementos + a PCB simétrica de dois elementos ajustada, passo vertical 48 mm e quatro cabos coaxiais físicos de 50 mm, com perdas. Os transformadores da PCB2 continuam em 0,546717 × 13,151813 mm. Não se alteraram materiais, radiadores, redes impressas ou fases.

**Quatro entradas de 0,25 W/0°, total 1 W, 14 núcleos.** Potências externas iguais não equivalem a potência uniforme por radiador entre as placas 4 e 2. Ganho realizado frontal total em +Z; não é ganho MIMO por entrada isolada. O VSWR é conferido tanto ativo quanto com as demais entradas casadas em 50 Ω, nas quatro entradas.

Metas desta etapa: **G frontal ≥13 dBi, H de 99° a 121° (110° ±10%) e VSWR ≤1,25**. A vertical é registrada; a meta histórica de 18° ±10% não é declarada atendida.

Cada nova geometria usa um ciclo independente de **no máximo seis passes, ΔS≤0,05 por dois passes consecutivos**, Classic automático, sem operações locais, MeshLink ou refinamento lambda. A geração inicial separada da malha serve para auditar os corpos antes dos passes, sem adicionar refinamento prévio. A referência histórica possui oito passes; não foi recalculada. Não se reutilizou uma malha incompatível com a nova chapa.

![Perfis das dobras](perfis_refletor.png)

## Resultados

| Início b / ângulo | G frontal dBi | H ° | V ° | VSWR máx. ativo / casado | Passes / ΔS | Convergiu S |
|---|---:|---:|---:|---:|---:|---|
{table}

{details}

Os JSONs preservam passividade, reciprocidade (limite 1×10⁻⁵), balanço de potência, recomposição dos campos e reparos de malha. Concluir seis passes não equivale a convergir. A comparação não prova um ótimo global; todos os candidatos calculados estão apresentados.

Entre os casos com casamento numérico ≤1,25, o mais próximo de 110° é **b={b:g} mm / {a:g}°**, com **H={h:.2f}° e G={g:.3f} dBi**. Esta indicação compara os resultados e não aprova um caso que falhe nas demais metas ou auditorias.

![Comparação dos diagramas H/V](comparacao_HV.png)

## Rastreabilidade

As fontes das duas PCBs foram conferidas por SHA-256; o CAD verifica sólidos válidos, cópia dos componentes e ausência de interpenetrações. O HFSS usa a construção nativa das dobras com arcos e extrusão, conferindo os demais corpos físicos após reconstruir a chapa. O arquivo FreeCAD contém sólidos e propriedades documentais; reconstruir pelo script/configuração para alterar suas dimensões.

`comparacao.json` inclui a decomposição dos campos embutidos das duas placas em boresight. A fase relativa dessa projeção não mede diretamente a fase em cada radiador. Qualquer limite de ganho com fases alinhadas é apenas diagnóstico algébrico com campos congelados; não foi aplicado às fontes nem tratado como nova simulação.

[Tabela CSV](comparacao.csv) · [Dados e diagnóstico](comparacao.json) · [Manifesto SHA-256](manifesto.json). Cada pasta de caso contém HFSS, FreeCAD, chapa STEP, S4, campos distantes, diagramas e evidências compactas. Malhas, `.aedtresults`, campos volumétricos e locks permanecem somente no trabalho local `D:/dev/EMBRAER/P2S13/R04_Dobras_Ajustadas`.
'''.format(verdict=verdict,table='\n'.join(table),details='\n'.join(details),b=best['b_mm'],a=best['angulo_graus'],h=best['H_graus'],g=best['G_frontal_dBi'])
if (ROOT/'interrupcao.json').exists():
    text=text.replace('# P2S13 — ajuste das dobras com as PCBs já casadas','# P2S13 — estudo 4+2 interrompido pelo usuário\n\n**Histórico encerrado em11/11.** O usuário substituiu esta topologia por três placas idênticas de dois elementos, com alvo horizontal100°. As filas foram paradas; o ensaio20/150 terminou durante a parada e foi apenas pós-processado. O caso3/45 tem CAD preparado, mas não foi simulado. Nenhum solve desta campanha será retomado automaticamente. [Registro da interrupção](interrupcao.json).')
(OUT/'README.md').write_text(text,encoding='utf-8')
(ROOT/'entrega.json').write_text(json.dumps(dict(veredito=verdict,casos=len(rows)-1,atende_metas_numericas=bool(numerical),aprovado=bool(valid),mais_proximo_H_com_VSWR=best['caso'],sem_sweep=True,nenhuma_fase_alterada=True),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(verdict)
