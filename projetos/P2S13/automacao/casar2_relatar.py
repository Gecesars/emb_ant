"""Relatorio final de casamento com valores HFSS reais e limites explicitos."""
from pathlib import Path
from datetime import datetime
import json
REPO=Path(__file__).resolve().parents[3];ROOT=Path('D:/dev/EMBRAER/P2S13/R02_Casamento_Placa2');OUT=REPO/'projetos/P2S13/casamento_placa2';OUT.mkdir(exist_ok=True)
data=json.loads((ROOT/'comparacao.json').read_text());rows=data['resultados'];new=rows[1:];assert new
best=min(new,key=lambda r:max(r['VSWR2_ativo_A'],r['VSWR2_ativo_B'],r['VSWR2_casado_A'],r['VSWR2_casado_B']))
tab='\n'.join('| {caso} | {largura_mm:.6f} / {comprimento_mm:.6f} | {VSWR2_ativo_A:.4f} / {VSWR2_ativo_B:.4f} | {VSWR2_casado_A:.4f} / {VSWR2_casado_B:.4f} | {ganho_frontal_dBi:.3f} | {H_graus:.2f} / {V_graus:.2f} | {passes} / {DeltaS:.6f} |'.format(**r) for r in rows)
status='validado numericamente' if best['casamento_validado'] else 'atinge numericamente o VSWR, mas permanece preliminar' if best['VSWR2_meta_numerica'] else 'ainda nao atinge o VSWR solicitado'
md=f'''# P2S13 — casamento da placa de dois elementos

O usuário pediu VSWR ≤1,25 em 5,17 GHz, alimentação simétrica/em fase, 14 núcleos, até seis passes e ΔS≤0,05. O ajuste é aplicado **somente aos transformadores da placa de dois elementos** no painel de seis níveis (C12 de quatro + nova placa de dois). A referência é o refletor b=10 mm/90°, que apresentou a maior abertura horizontal na etapa anterior. Não houve mudança de refletor, radiadores, retornos, espaçamento, altura ou cabos nesta comparação.

O candidato **{best['caso']}** {status}. Transformadores iguais nas duas polarizações: **{best['largura_mm']:.6f} mm de largura e {best['comprimento_mm']:.6f} mm de comprimento**. As duas bifurcações continuam simétricas, com quatro caminhos geométricos de 39,490832 mm. O restante de cada caminho é a linha de 1,623415 mm. Alterar a partição de larguras conserva o caminho geométrico, mas altera seu comprimento elétrico.

## Condições e objetivo

- Quatro entradas externas de 0,25 W a 0°, total de 1 W; nenhuma fase ajustada externamente.
- Cabos coaxiais físicos de 50 mm, substratos e metalizações com perdas, como na referência. Não inclui conectores N ou rede externa.
- Passo vertical 48 mm, seis níveis; PCB2 de 50 × 88 mm; RO4350B com núcleo de 0,76 mm e face inferior a 14,949 mm do refletor.
- Classic automático, 14 núcleos, frequência única de 5,17 GHz, sem sweep, máximo de seis passes, ΔS-alvo de 0,05 e dois passes consecutivos. Concluir no limite não significa convergir.
- Objetivo de casamento: VSWR nas entradas A/B da **PCB2**, tanto com todas as entradas iguais/em fase quanto com as demais terminadas em 50 Ω. O maior VSWR ativo de todas as quatro entradas também é registrado no JSON.

A triagem inicial usou MLine e a matriz Z4 efetiva congelada extraída do S4 anterior. Ela remove e repõe uma rede equivalente dos transformadores para selecionar dimensões; não prediz a alteração do campo nem do acoplamento geométrico. A recomposição exata da matriz original é apenas um teste da álgebra. O coaxial foi ideal de fase somente nessa triagem; as soluções HFSS abaixo incluem os cabos físicos com perdas.

## Resultados HFSS

| Caso | Largura / comprimento mm | VSWR2 ativo A/B | VSWR2 demais casadas A/B | G frontal dBi | H / V graus | Passes / ΔS |
|---|---:|---:|---:|---:|---:|---:|
{tab}

Máximos dos cortes do candidato selecionado: **H {best['pico_H_graus']:+.2f}° / V {best['pico_V_graus']:+.2f}°**. Lóbulo secundário vertical mais alto: **{best['SLL_V_dB']:.2f} dB** relativo ao pico do corte. Ganho é frontal realizado total com as quatro entradas simultâneas; não representa ganho MIMO por entrada isolada.

Convergência S: **{best['convergiu_S']}**; estabilidade das nove sondas de campo: **{best['campos_estaveis']}**; auditoria de passividade, reciprocidade, potência e malha: **{best['auditoria']}**. A meta de casamento não substitui essas verificações. As metas anteriores de ganho 13 dBi/H99–121°/V16,2–19,8° são relatadas nos resultados do painel e não foram relaxadas para classificar o casamento.

O último ΔS ficou abaixo de 0,05, mas foram registrados **{best['passes_consecutivos']} de dois passes consecutivos necessários**. O rótulo `Converged` exportado pelo HFSS é `{best['rotulo_HFSS_converged']}`; a auditoria não o aceita isoladamente quando o próprio contador consecutivo é insuficiente. Entre os dois últimos passes, o ganho frontal mudou **{best['delta_G_ultimo_passe_dB']:+.3f} dB**, e a maior mudança entre as nove sondas foi **{best['delta_campo_max_ultimo_passe_dB']:.3f} dB**. Não foram executados passes adicionais ou reiniciado o mesmo caso.

O maior VSWR ativo considerando **as quatro entradas do painel** é **{best['VSWR_todas_ativo_max']:.4f}**. O atendimento numérico ao limite 1,25 nesta etapa se refere às duas entradas da PCB2; não deve ser estendido às entradas da PCB4 nem à banda completa.

![Comparação dos cortes](comparacao_HV.png)

![Placa com transformadores ajustados]({best['caso']}/placa2/layout.png)

[Placa FreeCAD]({best['caso']}/placa2/2_elementos_simetrica.FCStd) · [Conjunto FreeCAD]({best['caso']}/P2S13_Casamento2.FCStd) · [Projeto HFSS]({best['caso']}/P2S13_Casamento2.aedt) · [Diagramas polares]({best['caso']}/polar_HV.png) · [Tabela CSV](comparacao.csv) · [Dados e classificação](comparacao.json) · [Manifesto SHA-256](manifesto.json).

O CAD foi verificado quanto a simetria, continuidade, isolamento e interferências. O nativo AEDT contém o modelo; a malha e os campos volumétricos ficam somente na pasta de trabalho e não são restaurados pela cópia do Git. S4, campos distantes, cortes e evidências compactas são preservados. Esta etapa não libera fabricação nem comprova desempenho em toda a banda.

Pasta de trabalho: `D:/dev/EMBRAER/P2S13/R02_Casamento_Placa2`. Scripts: `../automacao/casar2_*.py` e `casar2_pipeline.ps1`. Ensaios anteriores preservados em [seis_elementos](../seis_elementos/README.md).
'''
(OUT/'README.md').write_text(md,encoding='utf-8')
(ROOT/'qualificacao.json').write_text(json.dumps(dict(estado='ESTUDO_CONCLUIDO',atualizado=datetime.now().astimezone().isoformat(),candidato=best['caso'],VSWR_meta_numerica=best['VSWR2_meta_numerica'],casamento_validado=best['casamento_validado'],status=status,proximo_solve_automatico=False),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(str(OUT/'README.md'))
