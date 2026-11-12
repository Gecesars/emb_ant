"""Pesquisa dimensional PVC, explicacao do VSWR e resultados nominais rastreaveis."""
from pathlib import Path
import json
ROOT=Path('D:/dev/EMBRAER/P2S13/R16_Tubo_PVC');CASE=ROOT/'dn100'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
fit=read(ROOT/'encaixe_preliminar.json');cfg=read(CASE/'configuracao.json');t=cfg['radome'];ex=read(ROOT/'explicacao_VSWR_c09.json')
lines=['# P2S13 — tubo PVC e prioridade ao casamento','',
'Prioridade atual: menor VSWR nas duas entradas externas iguais e em fase. Aberturas H/V passam a ser apenas informativas. Frequência 5,17 GHz; sem sweep; 14 núcleos, até seis passes e ΔS alvo 0,05 por ciclo novo.','',
'## Tubos de construção civil localizados','',
'Referência dimensional: **Tigre Esgoto Série Normal, PVC rígido branco**, barras de 3 ou 6 m. O trecho da antena será cortado da parte reta, sem a bolsa. As dimensões abaixo são nominais de catálogo, não medidas no produto comprado.','',
'| Bitola DN | Diâmetro externo | Parede | Interno calculado | Folga radial conservadora |','|---|---:|---:|---:|---:|']
for x in fit['tubos']:lines.append(f"| {x['DN']} | {x['De_mm']:.1f} mm | {x['parede_mm']:.1f} mm | {x['Di_mm']:.1f} mm | {x['folga_radial_conservadora_mm']:.2f} mm |")
lines+=['',
'DN75 não comporta esta montagem. DN100 é o menor da tabela que cabe nominalmente; a folga de 1,39 mm é pequena e deve ser conferida com a ovalização, tolerâncias e fixação do tubo real. DN150 oferece mais espaço; DN200 é dimensionalmente desnecessário nesta montagem. A Série R 3 m consultada aparece como descontinuada no site do fabricante; não foi selecionada.','',
'![Comparação de encaixe DN100 e DN150](comparacao_encaixe.png)','',
'Fontes consultadas em 12/11/2026: [tabela oficial Série Normal 6 m](https://www.tigre.com.br/produto/tubo-serie-normal-6m), [ficha técnica Tigre](https://tigresite.s3.amazonaws.com/2023/07/FT_Esgoto-Serie-Normal_2023_final_compressed-1.pdf), [Série R 3 m](https://www.tigre.com.br/produto/tubo-serie-r-3m). A ficha cita NBR 5688; isso se refere ao uso hidráulico, não à qualificação como radome.','',
'## Modelo selecionado para o primeiro cálculo','',
f"Tubo DN100, De={t['De_mm']} mm, parede={t['espessura_mm']} mm, Di={t['Di_mm']} mm e comprimento **{t['comprimento_mm']} mm**. Eixo longitudinal X, centro Y=0 e Z={t['centro_z_mm']} mm. O comprimento do painel é 296 mm; ficam 27 mm livres em cada extremidade. O envelope conservador da montagem requer diâmetro {fit['diametro_conservador_mm']:.3f} mm. As coordenadas foram escolhidas para acomodar também os cabos e o divisor da montagem mecânica.",'',
'Tubo aberto, sem tampas, bolsa, anéis, cola, água ou conectores N. Esses componentes ainda não têm geometria definida neste estudo. O CAD contém 123 sólidos, sendo 122 originais e o tubo; nenhum sólido original foi alterado. A transparência na imagem é apenas para mostrar a montagem interna.','',
'![Montagem no tubo](dn100/visual/montagem_tubo_transparente.png)','',
'**Material eletromagnético preliminar:** εr=2,68 e tanδ=0,008, isotrópico. O iEMSL/Texas A&M publica essa referência para uma amostra de filme PVC medida entre 10,2 e 52,2 GHz. Aplicá-la em 5,17 GHz é uma hipótese de trabalho, não uma medição do PVC rígido branco Tigre; pigmentos, aditivos e lote podem alterar a resposta. A ficha do tubo não informa εr/tanδ em 5,17 GHz. Portanto nenhum resultado desta hipótese confirma por si só o desempenho de um tubo comercial. [Referência dielétrica](https://iemsl.engr.tamu.edu/services/material-characterization-services/material-characterization-examples/).','',
'O HFSS resolve separadamente a antena S6 com tubo e o divisor S8 com tubo, nas posições equivalentes da montagem. Os cabos de 134 mm continuam somente no Nexxim (133,82 mm entre planos EM, com perdas nominais). A cadeia usa duas entradas de 0,5 W / 0°. O método inclui o acoplamento entre radiadores, mas não o acoplamento espacial entre divisor e antena nem a radiação dos cabos/divisor no diagrama recomposto.','',
'## Por que o divisor isolado tinha VSWR próximo de 1,7','',
'A C09 c02 foi otimizada para a impedância complexa da antena vista através dos seis cabos iguais. Ao trocar essas cargas por seis terminações ideais de 50 Ω, mede-se outro problema de casamento. No HFSS, as entradas do divisor isolado ficaram próximas de **29 Ω**, e não 50 Ω. Isso explica o VSWR de aproximadamente 1,7. O ajuste anterior melhorou o conjunto carregado e piorou o divisor como componente genérico para cargas de 50 Ω. Não é possível concluir o VSWR do conjunto apenas pelo S11 isolado do divisor.','',
'| Condição anterior, sem tubo | VSWR A/B | Impedância A | Impedância B |','|---|---:|---:|---:|']
for key,title in [('divisor_saidas_50ohm','Divisor com saídas em 50 Ω'),('conjunto_ativo','Divisor + cabos + antena, entradas em fase'),('conjunto_outra_casada','Conjunto, outra entrada casada')]:
    a,b=ex[key];za=a['Z_ohm'];zb=b['Z_ohm'];lines.append(f"| {title} | {a['VSWR']:.4f} / {b['VSWR']:.4f} | {za[0]:.2f} {za[1]:+.2f}j Ω | {zb[0]:.2f} {zb[1]:+.2f}j Ω |")
lines+=['',
'Com VSWR=1,7, |Γ|=(1,7−1)/(1,7+1)=0,2593 e |Γ|²=6,72% da potência incidente é refletida. Isso não significa 1,7 dB de perda. Na c02 sem tubo, as duas portas ativas refletiam 0,709% e 1,028%, respectivamente. Os ramais permanecem nominalmente iguais; a carga real e seu acoplamento podem produzir pequenas diferenças de ondas nas saídas.','',
'## Resultado com tubo','']
rp=CASE/'circuito/resultado.json'
if rp.exists():
    r=read(rp);lines+=['As métricas abaixo pertencem ao PVC nominal descrito acima, em um único ponto de frequência.','',
        '| Métrica | Resultado |','|---|---:|',
        f"| VSWR ativo A / B | {r['VSWR_ativo'][0]:.5f} / {r['VSWR_ativo'][1]:.5f} |",
        f"| VSWR com outra entrada casada | {r['VSWR_outra_casada'][0]:.5f} / {r['VSWR_outra_casada'][1]:.5f} |",
        f"| Ganho frontal realizado | {r['cortes']['H']['ganho_frontal_dBi']:.4f} dBi |",
        f"| H / V, informativos | {r['cortes']['H']['abertura_graus']:.3f}° / {r['cortes']['V']['abertura_graus']:.3f}° |"]
    for block,c in r['convergencia'].items():lines.append(f"| {block}: passes / ΔS / convergiu | {c['passes']} / {c['delta_s']:.6f} / {c['convergiu']} |")
    if not all(c['convergiu'] for c in r['convergencia'].values()):
        lines+=['','**Resultado preliminar, sem aprovação de convergência completa.** A auditoria exige dois passes consecutivos com ΔS ≤0,05, além do valor final. O texto “Converged: Yes” do HFSS sozinho não satisfaz essa verificação. O limite de seis passes foi respeitado; nenhum passe adicional foi executado.']
    lines+=['',f"Estabilidade de campos observada: **{r['campos_monitorados']['estabilidade_observada']}**. Últimas variações: {r['campos_monitorados']['ultimos_deltas_max_dB']} dB. Nexxim pendente: **{r['nexxim_pendente']}**. Balanço de potência aprovado: **{r['potencia']['balanco_aprovado']}**.",'','![Diagramas nominais](dn100/circuito/polar_HV.png)']
    if not r['nexxim_pendente']:
        lines += ['',f"O Nexxim foi efetivamente resolvido; diferença máxima entre sua matriz S2 e a conexão independente: **{r['erro_Nexxim']:.3g}**. Essa conferência verifica a interligação dos blocos, sem substituir a convergência EM nem a caracterização do material comercial."]
else:
    state=read(CASE/'pipeline.json') if (CASE/'pipeline.json').exists() else {'estado':'PREPARADO'}
    lines+=['**Ainda não há resultado com tubo.** Estado observado: '+state['estado']+'. Os valores da C09 sem tubo não foram reutilizados como resultado do tubo.']
finished=[p for p in sorted(ROOT.glob('dn100_c*')) if (p/'circuito/resultado.json').exists() and not read(p/'circuito/resultado.json')['nexxim_pendente']]
if finished:
    adj=min(finished,key=lambda p:max(read(p/'circuito/resultado.json')['VSWR_ativo']));arp=adj/'circuito/resultado.json';selected=adj.name
    ar=read(arp);dp=read(adj/'divisor/configuracao.json')['parametros']
    lines+=['','## Ressintonia do divisor para o tubo — '+selected.upper(),'',
        'A C09 anterior foi preservada. Este candidato altera apenas as duas seções de transformação, da mesma forma nos seis ramais. A solução S6 com PVC é reutilizada por hash; não houve passe adicional na antena. O divisor ajustado foi novamente resolvido no HFSS com tubo, seguido por uma nova solução Nexxim.','',
        f"W1/W2 = **{dp['W1_mm']:.6f} / {dp['W2_mm']:.6f} mm**; L1/L2 = **{dp['L1_mm']:.6f} / {dp['L2_mm']:.6f} mm**. Comprimento total de cada ramal: {dp['comprimento_por_ramal_mm']:.9f} mm. Placa, terminais, cabos e tubo mantidos.",'',
        '| Condição | VSWR ativo A / B | Outra entrada casada A / B | Ganho frontal |',
        '|---|---:|---:|---:|']
    prev=read(Path('D:/dev/EMBRAER/P2S13/R15_Casamento_C09/c02/circuito/resultado.json'))
    rows=[('Sem tubo, C09 anterior',prev),('Com tubo, C09 anterior',r)]+[('Com tubo, '+p.name,read(p/'circuito/resultado.json')) for p in finished]
    for title,rr in rows:
        lines.append(f"| {title} | {rr['VSWR_ativo'][0]:.5f} / {rr['VSWR_ativo'][1]:.5f} | {rr['VSWR_outra_casada'][0]:.5f} / {rr['VSWR_outra_casada'][1]:.5f} | {rr['cortes']['H']['ganho_frontal_dBi']:.4f} dBi |")
    c=ar['convergencia']['divisor']
    lines+=['',f"Divisor selecionado {selected}: **{c['passes']} passes, ΔS={c['delta_s']:.6f}, convergência={c['convergiu']}**, 14 núcleos. Nexxim conferido com erro máximo {ar['erro_Nexxim']:.3g}; balanço de potência {ar['potencia']['balanco_aprovado']}.",'',
        f"**Compromisso de casamento:** com seis cargas de 50 Ω, o divisor selecionado isolado tem VSWR **{ar['divisor_casado']['A']['VSWR']:.4f} / {ar['divisor_casado']['B']['VSWR']:.4f}**. O objetivo minimizado foi o VSWR nas entradas do conjunto carregado pela antena, não um divisor universal para cargas de 50 Ω. A nova sintonia melhora esse conjunto e piora o casamento isolado.",'',
        f"VSWR ≤1,25 nas duas entradas ativas: **{ar['metas']['VSWR_ativo']}**. H/V informativos: {ar['cortes']['H']['abertura_graus']:.3f}° / {ar['cortes']['V']['abertura_graus']:.3f}°. Máximo vertical: {ar['pico_V_fino_graus']:+.4f}°; assimetria principal V: {ar['assimetria_principal_V_dB']:.4f} dB.",'',
        '**A ressalva de convergência/campos da antena e a hipótese de material PVC continuam válidas.** O melhor resultado entre os candidatos calculados não demonstra mínimo global de VSWR nem qualifica o tubo comercial.','',
        f'![Diagramas com tubo e divisor ajustado]({selected}/circuito/polar_HV.png)','',
        f'![Montagem selecionada no tubo]({selected}/visual/montagem_tubo_ajustada.png)','',
        f'[HFSS do divisor selecionado]({selected}/divisor/Divisor_Duplo3.aedt) · [Nexxim]({selected}/circuito/C09_PVC_Nexxim_sem_malhas.aedtz) · [Montagem FreeCAD]({selected}/visual/Antena_PVC_{selected.upper()}_PRELIMINAR.FCStd)']
lines+=['','## Arquivos','',
'[Configuração](dn100/configuracao.json) · [HFSS antena](dn100/antena/PCB_Tubo_DN100.aedt) · [HFSS divisor](dn100/divisor/Divisor_Tubo_DN100.aedt) · [Montagem FreeCAD](dn100/visual/Antena_PVC_DN100_PRELIMINAR.FCStd)','',
'Fontes R14/R15 preservadas; nenhum cabo longo no HFSS. Dados de solver volumétricos e malhas ficam apenas na pasta de trabalho local.','']
(ROOT/'README.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
print('DOCUMENTACAO_PVC_ATUALIZADA')
