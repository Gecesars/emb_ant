"""Documenta continuacao real dos passes7/8, com estabilidade e metas separadas."""
from pathlib import Path
from datetime import datetime
import json
REPO=Path(__file__).resolve().parents[3];ROOT=Path('D:/dev/EMBRAER/P2S13/R03_Continuacao_M00');OUT=REPO/'projetos/P2S13/continuacao_placa2';OUT.mkdir(exist_ok=True)
data=json.loads((ROOT/'comparacao.json').read_text());old,now=data['resultados'];delta=data['delta_8_menos_6'];assert old['passes']==6 and now['passes']==8
cont=json.loads((ROOT/'continuidade_auditada.json').read_text());assert cont['aprovado'] and cont['origem6_nao_alterada']
diag=json.loads((ROOT/'diagnostico_numerico.json').read_text());probe=diag['maior_delta_sonda']
yes=lambda v:'sim' if v else 'não'
status='Casamento e estabilidade numérica confirmados no centro.' if now['casamento_validado'] else 'Resultado requer as ressalvas de convergência/estabilidade descritas abaixo.'
rows=[]
for label,key,fmt in [('ΔS','DeltaS','.6f'),('Passes consecutivos','passes_consecutivos','d'),('VSWR ativo PCB2 A','VSWR2_ativo_A','.5f'),('VSWR ativo PCB2 B','VSWR2_ativo_B','.5f'),('VSWR PCB2 A, demais casadas','VSWR2_casado_A','.5f'),('VSWR PCB2 B, demais casadas','VSWR2_casado_B','.5f'),('Ganho frontal realizado total (dBi)','ganho_frontal_dBi','.4f'),('Abertura H (°)','H_graus','.3f'),('Abertura V (°)','V_graus','.3f'),('Máximo H (°)','pico_H_graus','+.2f'),('Máximo V (°)','pico_V_graus','+.2f'),('Lóbulo secundário V (dB)','SLL_V_dB','.3f')]:
    rows.append('| '+label+' | '+format(old[key],fmt)+' | '+format(now[key],fmt)+' |')
table='\n'.join(rows)
md=f'''# P2S13 — dois passes adicionais na versão ajustada

Continuação solicitada em 11/11/2026: **somente os passes 7 e 8**, preservando os seis anteriores. **{status}**

- **ΔS≤0,05 com dois passes consecutivos: {yes(now['convergiu_S'])}.** Último ΔS={now['DeltaS']:.8f}; contador consecutivo={now['passes_consecutivos']}.
- **VSWR≤1,25 nas duas entradas da PCB2: {yes(now['VSWR_meta_numerica'])}**, tanto ativo com quatro entradas iguais/em fase quanto com as demais terminadas em 50 Ω.
- **Estabilidade das nove sondas de campo: {yes(now['campos_estaveis'])}**, usando o limite já existente de 0,1 dB em dois passos consecutivos. Não confundir convergência de S com estabilidade de todos os campos.
- **Auditoria numérica conjunta: {yes(now['auditoria'])}.** A reciprocidade excedeu o limite; passividade, balanço de potência, recomposição dos campos e malha passaram nas verificações.

## Continuidade conferida

A solução foi copiada para uma pasta própria, incluindo os 66 arquivos de resultados locais. Os hashes do adaptativo, da malha e dos campos salvos foram conferidos antes da retomada. O HFSS reconheceu os seis passes existentes e o worker retomou com `-solve_adapt 7 -max_processors 14`. Nenhum novo ciclo inicial de malha foi executado.

O setup mudou somente de máximo 6/mínimo 2 para **máximo 8/mínimo 8**, para executar exatamente os dois passos solicitados. ΔS=0,05, dois passes consecutivos, geometria, materiais, fronteiras, parâmetros de malha e os nove identificadores de cache foram mantidos. Ao final, os históricos completos dos seis primeiros passes permaneceram idênticos; o projeto original e seus resultados também foram conferidos sem alteração. [Auditoria antes do solve](preparacao_auditada.json) · [Auditoria final](continuidade_auditada.json) · [Origem e hashes](origem.json).

## Condições físicas

Painel de seis níveis: C12 de quatro elementos + PCB simétrica de dois, refletor b=10 mm/90°, passo 48 mm. Transformadores PCB2 de **0,546717 mm × 13,151813 mm**, caminhos geométricos iguais de 39,490832 mm. Quatro cabos coaxiais físicos de 50 mm, perdas dos condutores e dielétricos incluídas. Quatro entradas **0,25 W / 0°**, total de 1 W. Potência por radiador não é uniforme entre as placas de quatro e dois elementos.

**5,17 GHz somente, sem sweep, 14 núcleos nos dois passos adicionais.** A análise não representa ganho MIMO por entrada isolada nem qualifica a banda. PCB, cabos, rede impressa e refletor são os mesmos do [ensaio de seis passes](../casamento_placa2/README.md).

## Comparação

| Grandeza | 6 passes | 8 passes |
|---|---:|---:|
{table}

Do passe 6 ao 8: ganho frontal **{delta['ganho_frontal_dBi']:+.4f} dB**, largura H **{delta['H_graus']:+.3f}°** e V **{delta['V_graus']:+.3f}°**. No último passo, o ganho frontal mudou **{now['delta_G_ultimo_passe_dB']:+.4f} dB** e a maior mudança das nove sondas foi **{now['delta_campo_max_ultimo_passe_dB']:.4f} dB**.

A maior mudança de campo ocorreu em **θ={probe['theta_graus']}° / φ={probe['phi_graus']}°**, perto do primeiro mínimo do corte vertical. O erro máximo de reciprocidade foi **{diag['residuo_reciprocidade']:.8g}**, entre {diag['par_reciprocidade'][0]} e {diag['par_reciprocidade'][1]}, acima do limite mantido em **1×10⁻⁵**. A matriz é passiva e o balanço de potência confere, mas essa auditoria foi reprovada. Simetrizar a matriz apenas como diagnóstico mudaria o VSWR ativo em no máximo {diag['sensibilidade_VSWR_ativo_max_ao_simetrizar']:.8g}; isso não estima o erro completo de malha, não corrige a solução e não foi aplicado aos dados entregues. [Diagnóstico numérico](diagnostico_numerico.json).

O maior VSWR ativo das quatro entradas do painel foi **{now['VSWR_todas_ativo_max']:.5f}**. A meta de casamento desta etapa é das duas entradas da PCB2. As metas anteriores de ganho 13 dBi, H99–121° e V16,2–19,8° continuam apresentadas no JSON do conjunto, sem aprovação implícita pelo casamento.

![Comparação dos cortes](comparacao_HV.png)

![Diagramas polares](polar_HV.png)

[HFSS atualizado](P2S13_Casamento2.aedt) · [Montagem FreeCAD](P2S13_Casamento2.FCStd) · [PCB2 preservada](../casamento_placa2/m00/placa2/2_elementos_simetrica.FCStd) · [Tabela CSV](comparacao.csv) · [Dados e verificações](resultado.json) · [Histórico adaptativo](historico_passes.json) · [Manifesto SHA-256](manifesto.json).

O nativo contém o modelo e os relatórios, porém a solução FEM completa exige as malhas/campos locais. O Git guarda o nativo, S4, campos distantes, diagramas e evidências compactas, sem `.aedtresults`, malhas, locks ou campos volumétricos. Trabalho local: `D:/dev/EMBRAER/P2S13/R03_Continuacao_M00`. Nenhum passo adicional além de oito foi programado.
'''
(OUT/'README.md').write_text(md,encoding='utf-8')
(ROOT/'entrega.json').write_text(json.dumps(dict(estado='CONCLUIDO',atualizado=datetime.now().astimezone().isoformat(),novos_passes=[7,8],malha_preservada=True,convergencia_S=now['convergiu_S'],VSWR_meta=now['VSWR_meta_numerica'],campos_estaveis=now['campos_estaveis'],casamento_validado=now['casamento_validado'],proximo_solve_automatico=False),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(str(OUT/'README.md'))
