"""Compara os ensaios reais R13 e empacota evidencia compacta, sem resultados FEM."""
from pathlib import Path
import argparse,json,hashlib,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from divisor_variantes_comparar import read_pattern,profile_matrix_solves
from quatro_banda_estimar import ROOT,BASE,VSWR_TARGET

REPO=Path(__file__).resolve().parents[3]
DEST=REPO/'projetos/P2M21/quatro_elementos_casamento_banda'

def read(path):return json.loads(path.read_text(encoding='utf-8'))

def band_result(folder):
    """Conserva o pior valor entre Fast e conferencias discretas disponiveis."""
    b=read(folder/'banda_auditada.json')
    discrete=b.get('conferencia_discrete',{})
    for key in ['pior_VSWR_ativo','pior_VSWR_casado']:
        b[key]=max(b[key],discrete.get(key,1.))
    if (folder/'pico_auditado.json').exists():
        peak=read(folder/'pico_auditado.json');b['conferencia_pico']=peak
        b['pior_VSWR_ativo']=max(b['pior_VSWR_ativo'],max(peak['VSWR_ativo']))
        b['pior_VSWR_casado']=max(b['pior_VSWR_casado'],max(peak['VSWR_casado']))
        b['ativos_ate_meta'] &= peak['ativos_ate_meta']
        b['casados_ate_meta'] &= peak['casados_ate_meta']
        b['todos_VSWR_ate_meta'] &= peak['todos_VSWR_ate_meta']
    return b

def main(package=False):
    ref=read(BASE/'resultado.json')
    folders=sorted(p.parent for p in ROOT.glob('c*/resultado.json'))
    cases=[(p,read(p/'resultado.json'),read(p/'diagrama_comparado.json')) for p in folders]
    finals=[(p,band_result(p)) for p,r,d in cases if d['permitir_fast'] and (p/'banda_auditada.json').exists()]
    best=min(finals,key=lambda x:x[1]['pior_VSWR_ativo']) if finals else None
    matching=[(p,band_result(p),d) for p,r,d in cases
        if (p/'banda_auditada.json').exists() and r['convergiu'] and r['fisica_ok']
        and all(ok for key,ok in d['verificacoes'].items() if not key.startswith('apontamento_'))]
    best_matching=min(matching,key=lambda x:x[1]['pior_VSWR_ativo']) if matching else None
    rows=[]
    for name,r in [('R12 referencia',ref)]+[(p.name,r) for p,r,d in cases]:
        h,v=r['cortes']['H'],r['cortes']['V']
        rows.append(f"| {name} | {r['passes']} | {r['delta_s']:.6f} | {'Sim' if r['convergiu'] else 'Nao'} | {h['ganho_frontal_dBi']:.4f} | {r['VSWR_ativo'][0]:.4f}/{r['VSWR_ativo'][1]:.4f} | {r['VSWR_casado'][0]:.4f}/{r['VSWR_casado'][1]:.4f} | {h['pico_graus']:+.2f}/{v['pico_graus']:+.2f} | {h['abertura_graus']:.3f}/{v['abertura_graus']:.3f} | {r['SLL_V']['nivel_dB']:.3f} |")
    bandrows=[];dimensionrows=[];extra_dimensions=[];audits=[]
    for p,r,d in cases:
        g=read(p/'geometria.json');par=g['parametros'];w=g['lines']['70.71067811865476']['w_mm'];l=g['lines']['70.71067811865476']['l90_mm']
        w50=g['lines']['50']['w_mm']
        dim=[w*par.get('root_w_A',1),l*par.get('root_l_A',1),w*par.get('local_w_A',1),l*par.get('local_l_A',1),w50*par.get('root_post_w_A',1.),w50*par.get('local_post_w_A',1.)]
        dimensionrows.append(f"| {p.name} | "+' | '.join(f'{x:.6f}' for x in dim)+f" | {par.get('dipolo_escala_externa',1.):.4f} | {r['basis_order']} |")
        for idx in (2,3,4):
            length=l*par.get('root_seg%d_l_A'%idx,0.)
            if length:extra_dimensions.append(f"| {p.name} | {idx} | {w50*par.get('root_seg%d_w_A'%idx,1.):.6f} | {length:.6f} |")
        failed=[k for k,v in d['verificacoes'].items() if not v]
        audits.append(f"- **{p.name}**: Major/Minor={r['major']}/{r['minor']}; passiva={r['passivo']}; reciprocidade={r['residuo_reciprocidade']:.3g}; recomposicao A+B={max(r['erros_recomposicao'].values()):.3g}; potencia aceita={r['potencia_aceita_W']:.6f} W. Barreiras nao atendidas: {', '.join(failed) if failed else 'nenhuma'}.")
        if (p/'sexto_continuidade_auditada.json').exists():
            continuation=read(p/'sexto_continuidade_auditada.json');change=continuation['comparacao5_6']
            audits.append(f"  Confirmacao do quinto ao sexto passe total, sem reiniciar: historico dos cinco primeiros identico={continuation['primeiros_cinco_identicos']}; variacao G={change['ganho_dB']:+.6f} dB, H={change['abertura_H_graus']:+.6f} grau, V={change['abertura_V_graus']:+.6f} grau. O estado de cinco passes esta preservado em passe5/. A convergencia de DeltaS nao implica estabilidade exata dos campos.")
        for fn in ['triagem3_auditada.json','banda_auditada.json']:
            if not (p/fn).exists():continue
            b=read(p/fn)
            for e in b['extremos']:
                bandrows.append(f"| {p.name} | {b['tipo']} {b['pontos']} | {e['condicao']} | {e['minimo']:.5f} | {e['maximo']:.5f} | {e['frequencia_max_GHz']:.3f} |")
    status='Nenhuma nova variante tem confirmacao Fast da banda completa e todos os criterios centrais atendidos.'
    if best:
        p,b=best;status=f"Melhor variante entre as confirmadas nesta rodada: **{p.name}**, pior VSWR ativo **{b['pior_VSWR_ativo']:.5f}** e casado **{b['pior_VSWR_casado']:.5f}**. Meta operacional A+B em fase <= {VSWR_TARGET}: **{'Sim' if b['ativos_ate_meta'] else 'Nao'}**. Condicao com outra entrada em 50 ohms <= {VSWR_TARGET}: **{'Sim' if b['casados_ate_meta'] else 'Nao'}**. Nao constitui prova de otimo global."
    elif best_matching:
        p,b,d=best_matching
        failed=[key for key,ok in d['verificacoes'].items() if not ok]
        status=f"Melhor casamento de banda calculado nesta rodada: **{p.name}**, pior VSWR ativo **{b['pior_VSWR_ativo']:.5f}** e casado **{b['pior_VSWR_casado']:.5f}**, em Fast com conferencia discreta. Meta operacional A+B em fase <= {VSWR_TARGET}: **{'Sim' if b['ativos_ate_meta'] else 'Nao'}**. Condicao com outra entrada em 50 ohms <= {VSWR_TARGET}: **{'Sim' if b['casados_ate_meta'] else 'Nao'}**. Pendencias dos criterios centrais: **{', '.join(failed)}**. O casamento calculado nao aprova essas pendencias e nao constitui prova de otimo global ou validacao experimental."
    overview=''
    selected=best[0] if best else (best_matching[0] if best_matching else None)
    if selected:
        sr=read(selected/'resultado.json');sb=band_result(selected)
        sh,sv=sr['cortes']['H'],sr['cortes']['V'];sn=selected.name
        overview=f'''## Resultado selecionado

| Grandeza | Resultado |
|---|---|
| Maior VSWR ativo A/B na banda Fast | {sb['extremos'][0]['maximo']:.5f} / {sb['extremos'][1]['maximo']:.5f} |
| Maior VSWR com outra entrada casada A/B | {sb['extremos'][2]['maximo']:.5f} / {sb['extremos'][3]['maximo']:.5f} |
| Ganho frontal realizado total, 5,17 GHz | {sh['ganho_frontal_dBi']:.4f} dBi |
| Aberturas H / V, 5,17 GHz | {sh['abertura_graus']:.3f} / {sv['abertura_graus']:.3f} graus |
| Maximos H / V, 5,17 GHz | {sh['pico_graus']:+.2f} / {sv['pico_graus']:+.2f} graus |
| Maior lobulo secundario V, 5,17 GHz | {sr['SLL_V']['nivel_dB']:.3f} dB |
| Adaptacao / DeltaS final | {sr['passes']} passes / {100*sr['delta_s']:.3f}% |

O apontamento acima e o observado na grade de 0,25 grau, sem arredondar para zero. Em H, o ganho em zero esta {sh['ganho_pico_dBi']-sh['ganho_frontal_dBi']:.6f} dB abaixo do maximo, mas o limite de apontamento continua registrado separadamente. As larguras e a forma principal foram preservadas dentro dos limites de trabalho; o lobo secundario vertical foi reduzido em relacao a R12. A meta de casamento nao elimina a ressalva de apontamento. As curvas de VSWR abrangem a banda; ganho e diagramas foram calculados somente no centro.

[HFSS editavel]({sn}/P2M21_4_elementos.aedt) · [FreeCAD]({sn}/4_elementos.FCStd) · [Polares E/Emax em PDF]({sn}/polar_HV.pdf) · [Dimensoes dos transformadores]({sn}/transformadores_detalhe.png)

![Casamento na banda]({sn}/vswr_banda_detalhe.png)

![Diagramas polares selecionados]({sn}/polar_HV.png)
'''
        if 'conferencia_pico' in sb:
            peak=sb['conferencia_pico']
            overview+=f"\nConferencia adicional do pior ponto ativo Fast: **Discrete em {peak['frequencia_GHz']:.3f} GHz**, VSWR ativo A/B **{peak['VSWR_ativo'][0]:.5f}/{peak['VSWR_ativo'][1]:.5f}**, casado **{peak['VSWR_casado'][0]:.5f}/{peak['VSWR_casado'][1]:.5f}**. Diferenca maxima de S para o Fast: {peak['diferenca_S_max']:.6g}. Solucao com 14 nucleos, sem novos passes ou campos fora do centro. O resumo considera o maior valor entre Fast, Discrete3 e esta conferencia.\n"
    visuals=[]
    for p,r,d in cases:
        visuals.append(f"### {p.name}\n\nConvergencia: {r['convergiu']}. Criterios dos diagramas: {d['permitir_fast']}.\n\n![PCB]({p.name}/layout.png)\n\n![Comparacao dos diagramas]({p.name}/comparacao_diagramas.png)\n\n![Diagramas polares]({p.name}/polar_HV.png)")
        for n in ['vswr_triagem3.png','vswr_banda.png','vswr_banda_detalhe.png']:
            if (p/n).exists():visuals.append(f'![VSWR]({p.name}/{n})')
        if (p/'dipolos_detalhe.png').exists():visuals.append(f'![Detalhe dos dipolos]({p.name}/dipolos_detalhe.png)')
        if (p/'transformadores_detalhe.png').exists():visuals.append(f'![Dimensoes dos transformadores]({p.name}/transformadores_detalhe.png)')
    md=f'''# P2M21 — ajuste de casamento na banda R13

{status}

Meta atualizada pelo usuario em 9/11: **VSWR <= {VSWR_TARGET} em toda a banda**, nas duas entradas. A avaliacao operacional usa ambas em fase; a condicao com a outra entrada casada tambem e registrada. Os limites historicos da R12 permanecem nos respectivos documentos; a comparacao R13 usa a meta atual.

{overview}

## Condicoes

Quatro radiadores verticais, passo 48 mm, PCB de 70 x 184 mm e face inferior a 14,949 mm do refletor de aluminio de 90 x 200 x 2 mm. Duas entradas iguais, A=B=0,5 W/0 graus. Dois divisores impressos 1:4; RO4350B 0,76 mm, cobre 35 um e ENIG nominal. Dois cabos fisicos de 50 mm com perdas, sem conector N ou apoios plasticos. As dimensoes novas dos divisores sao iguais nas duas polarizacoes. Oito percursos geometricos de trilha iguais, 101,490832 mm cada, alem dos cabos.

Propriedades nominais preservadas da referencia: RO4350B com permissividade 3,66 e tangente de perdas 0,0037; PTFE dos cabos com 2,03636 e 0,000276831. O cobre impresso usa condutividade efetiva 28,6886 MS/m, incorporando a aproximacao Groiss para rugosidade de 0,5 um, avaliada em 5,25 GHz e mantida fixa na faixa. Sobre as faces expostas, a impedancia em camadas representa NiP de 4,5 um (1,5 MS/m) e ouro de 0,0254 um (41 MS/m), sem shell elements. O aluminio usa 20 MS/m. Sao hipoteses do modelo, nao propriedades medidas da placa fabricada; os nativos, `cad/enig_hfss.json` e `automacao/r05/enig_solido.py` preservam os valores e a implementacao.

Cada nova geometria usa HFSS sem GUI, 14 nucleos, maximo de seis passes, alvo DeltaS=0,05 e dois passes consecutivos. Malha Classic automatica, sem MeshLink ou refinamentos locais iniciais. O campo de segunda ordem da C02 e variantes que o herdam aumenta o numero de funcoes por tetraedro; nao acrescenta passes. A R12 historica, preservada, tem oito passes. DeltaS mede a mudanca entre solucoes; nao e uma garantia de erro fisico percentual.

O modelo equivalente MLine serviu somente para selecionar dimensoes. Reproduzir os dados usados na sua calibracao nao valida as previsoes. A primeira mudanca grande nos dois estagios nao se confirmou no HFSS e foi rejeitada. Os resultados abaixo sao extraidos das simulacoes completas, com acoplamento, rede impressa e cabos.

Como as correcoes idealizadas de linhas melhoraram mais o centro que as bordas, a selecao C10 passou a usar tambem secantes das matrizes S complexas e campos de tres ensaios HFSS (C07/C08/C09). Essa aproximacao afim cobre apenas duas direcoes geometricas amostradas e pode extrapolar; suas previsoes continuam identificadas como nao validadas. Somente a nova simulacao completa confirma o resultado. Larguras nominalmente fixas em 5 mm foram tratadas como fixas no seletor quando as diferencas numericas eram inferiores a 0,00001 mm, evitando restricoes artificiais; isso nao modifica os dados HFSS das fontes.

A C10 reduziu o pior VSWR ativo discreto para 1,297245, mas nao confirmou a previsao de 1,197945: continuou acima da meta em 5,25 GHz. O arquivo `c10_raiz_secantes/previsao_conferida.json` confronta as matrizes e os valores previstos com os efetivamente calculados. A busca seguinte ampliou a direcao geometrica, reduzindo tambem a largura da primeira secao. Estimativas de novos candidatos nunca substituem os resultados HFSS nas tabelas.

Na C11, reduzir a primeira largura melhorou as bordas, mas elevou o pior VSWR ativo central para 1,330511. A selecao C12 combina quatro respostas reais (C08/C09/C10/C11), agora com tres direcoes geometricas independentes, buscando equilibrar essas respostas. A generalizacao do seletor preservou numericamente a proposta anterior quando recebeu novamente suas tres fontes originais.

## Dimensoes dos transformadores

| Variante | Raiz largura mm | Raiz comprimento mm | Local largura mm | Local comprimento mm | Pos-raiz largura mm | Pos-local largura mm | Fator externo dipolos | BasisOrder |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(dimensionrows)}

Os segmentos posteriores usam a largura nominal de 50 ohms (1,623415 mm) quando nao modificados. Se a largura for ajustada, passam a integrar o casamento e nao devem ser descritos como linhas de 50 ohms. Os comprimentos geometricos totais continuam iguais; a confirmacao eletromagnetica inclui a mudanca de fase eletrica e as descontinuidades.

Secoes adicionais em serie na raiz, quando presentes, terminam antes da curva. Todas sao iguais nos ramos e polarizacoes, mantendo os divisores locais e os radiadores da fonte.
O parametro `root_flat_sections` usa juntas planas, com mudancas de largura nas cotas nominais. Os modelos historicos usam extremidades quadradas que se sobrepoem; o seletor novo considera suas fronteiras efetivas ao retirar a rede historica. Isso continua sendo uma aproximacao de circuito. A C06 foi interrompida antes de qualquer solve para corrigir essas transicoes; nao ha resultado RF dessa geometria.

| Variante | Secao na raiz | Largura mm | Comprimento mm |
|---|---:|---:|---:|
{chr(10).join(extra_dimensions) if extra_dimensions else '| Nenhuma | — | — | — |'}

O fator externo opcional modifica apenas a distancia dos contornos dos dipolos alem de +/-4 mm do centro local, preservando a regiao central, as conexoes e vias. Nao e uma escala global da antena nem uma previsao de deslocamento da ressonancia. `alteracao_dipolos.json` registra as areas e a verificacao do nucleo preservado. Os recortes dos retornos acompanham os novos contornos para manter as folgas. As trilhas de sinal da C03 sao identicas as da R12.

## Ganho e diagramas somente em 5,17 GHz

| Caso | Passes | DeltaS | Convergiu | G0 dBi | VSWR ativo A/B | VSWR casado A/B | Maximos H/V graus | Aberturas H/V graus | SLL V dB |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

Frente +Z, H=phi90 graus, V=phi0 graus, grade angular 0,25 grau. VSWR ativo considera as duas entradas simultaneamente; VSWR casado considera a outra entrada terminada em 50 ohms. Ganho realizado normalizado a 1 W incidente total. Valores de candidatos nao convergidos sao preliminares.

Para preservar os diagramas em relacao a R12, a triagem exige ganho frontal >=12 dBi, variacao da abertura <=5%, diferenca de forma no lobo principal alinhado <=0,75 dB, piora do maior lobulo secundario vertical <=0,5 dB e picos |H|<=0,5 grau e |V|<=1,5 grau. A comparacao de forma usa somente o lobo principal da referencia, delimitado pelos primeiros minimos, e os pontos acima de -10 dB. Esses limites de trabalho nao significam maximos exatamente em zero. Todos constam de `diagrama_comparado.json`. Quando apenas o apontamento reprova, uma varredura explicitamente diagnostica pode medir o VSWR sem aprovar o apontamento; o registro `fast_diagnostico.json` ou `triagem_diagnostica.json` conserva essa ressalva. Os demais limites nao sao dispensados.

Uma falha no auditor inicial fazia a mascara >=-10 dB incluir tambem o lobo secundario vertical da R12 entre 37 e 44,75 graus. Assim, reduzir esse lobo podia ser interpretado como deformacao do principal. A mascara foi corrigida para excluir secundarios; nenhum limite numerico mudou. O diagnostico anterior permanece em `diagrama_comparado_antes_correcao_mascara.json`, e `correcao_mascara_lobo_principal.json` registra valores, angulos e hashes. Na C08 de seis passes, o erro principal V correto e 0,398753 dB, em vez de 1,130560 dB calculado sobre os dois lobos. A verificacao do maior secundario continua independente; outros lobos podem mudar, conforme os graficos completos.

Uma triagem adicional de tres frequencias pode ser usada exclusivamente para calibrar o modelo de um candidato rejeitado, desde que a solucao esteja convergida e fisicamente consistente. Esse uso exige a marca `CALIBRACAO_DE_CANDIDATO_REJEITADO`; nao aprova a geometria nem libera a confirmacao Fast. Os limites de aceitacao dos diagramas permanecem os mesmos.

## Casamento entre 5,09 e 5,25 GHz

Referencia R12 Fast: pior VSWR ativo A=2,27960 e B=2,01420, ambos em 5,09 GHz. Triagem Discrete tem somente tres solucoes (5,09/5,17/5,25 GHz) e nao qualifica os intervalos. A confirmacao Fast produz 161 pontos de saida, com passo de 1 MHz, na malha adaptada em 5,17 GHz. Nao sao 161 adaptacoes independentes. Nenhum diagrama fora do centro foi solicitado ou calculado nesta etapa.

O Fast usa a solucao central para construir a resposta na faixa e conserva a malha adaptada. A conferencia com solucoes Discrete verifica a concordancia em frequencias selecionadas; nao substitui um estudo de tolerancias de fabricacao. [Metodo Fast na documentacao Ansys](https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v251/en/Subsystems/HFSS/Content/HFSS/FastFrequencySweeps.htm).

| Caso | Varredura/pontos | Condicao | VSWR minimo | VSWR maximo | Frequencia max GHz |
|---|---|---|---:|---:|---:|
{chr(10).join(bandrows) if bandrows else '| Nenhuma varredura nova concluida | — | — | — | — | — |'}

## Auditorias

{chr(10).join(audits)}

## Imagens e curvas dos candidatos

{chr(10).join(visuals)}

Os nativos HFSS/FreeCAD, dados S2P, cortes distantes, configuracoes e evidencias acompanham o pacote. No FreeCAD, os corpos sao solidos Part::Feature; as dimensoes sao reproduzidas pelos scripts e JSON, sem arvore nativa de esbocos restringidos. Malhas, `.aedtresults`, campos volumetricos, locks e temporarios ficam somente no estudo local. Reabrir o nativo sem os resultados permite editar o projeto; recuperar os campos FEM em outra maquina exige novo solve. A geometria e os resultados historicos R12 foram preservados. Este estudo nao qualifica o painel 16x2 ou desempenho MIMO por entrada.
'''
    (ROOT/'README.md').write_text(md,encoding='utf-8')
    (ROOT/'comparacao.json').write_text(json.dumps(dict(melhor_confirmada=best[0].name if best else None,melhor_casamento_banda=best_matching[0].name if best_matching else None,candidatos=[p.name for p,r,d in cases],estado=status),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if not package:return
    assert read(ROOT/'estudo.json')['estado'].startswith('CONCLUIDO'), 'Estudo ainda em andamento'
    assert not list(ROOT.glob('c*/P2M21_4_elementos.aedt.lock')), 'Existe projeto de candidato aberto'
    assert cases and all(not (p/'P2M21_4_elementos.aedt.lock').exists() for p,r,d in cases)
    reviewed={x['arquivo']:x for x in read(ROOT/'revisao_pdf.json')['arquivos']}
    for pdf in list(ROOT.glob('c*/polar_HV.pdf'))+list(ROOT.glob('c*/passe5/polar_HV.pdf')):
        review=reviewed[pdf.relative_to(ROOT).as_posix()]
        assert review['revisao_visual'] and review['paginas']==1 and review['sha256']==hashlib.sha256(pdf.read_bytes()).hexdigest()
    for review in read(ROOT/'revisao_imagens_finais.json')['arquivos']:
        assert review['revisao_visual'] and review['sha256']==hashlib.sha256((ROOT/review['arquivo']).read_bytes()).hexdigest()
    allow=['P2M21_4_elementos.aedt','4_elementos.FCStd','configuracao.json','geometria.json','HFSS_14nucleos.acf','layout.png','caminhos_alimentacao.json','convergencia.txt','centro.s2p','banda_fast.s2p','triagem3.s2p','resultado.json','malha.json','qualificacao.json','diagramas_HV.png','polar_HV.png','polar_HV.pdf','comparacao_diagramas.png','diagrama_comparado.json','banda_auditada.json','triagem3_auditada.json','vswr_banda.csv','vswr_banda.png','vswr_triagem3.csv','vswr_triagem3.png','alteracoes_geometricas.json','proposta_usada.json','cad_validacao.json','criar_cad.py','criar_hfss.py','resolver.py','mensagens_fast.json','mensagens_triagem3.json','antes_fast_convergencia.txt','apos_fast_convergencia.txt','antes_triagem3_convergencia.txt','apos_triagem3_convergencia.txt']+[m+'_'+a+'.csv' for m in ['AB','A','B'] for a in 'HV']
    pairs=[(p/n,DEST/p.name/n) for p,r,d in cases for n in allow if (p/n).exists()]
    pairs +=[(p/n,DEST/p.name/n) for p,r,d in cases for n in ['hfss_validacao.json','comparacao_AB.json','mensagens.json'] if (p/n).exists()]
    pairs +=[(p/n,DEST/p.name/n) for p,r,d in cases for n in ['alteracao_dipolos.json','dipolos_detalhe.png','transformadores_detalhe.png','dimensoes_transformadores.json','transicoes_auditadas.json','triagem_diagnostica.json','fast_diagnostico.json','triagem_recursos.json','fast_recursos.json','diagrama_comparado_antes_correcao_mascara.json'] if (p/n).exists()]
    pairs +=[(p/'vswr_banda_detalhe.png',DEST/p.name/'vswr_banda_detalhe.png') for p,r,d in cases if (p/'vswr_banda_detalhe.png').exists()]
    pairs +=[(p/'previsao_conferida.json',DEST/p.name/'previsao_conferida.json') for p,r,d in cases if (p/'previsao_conferida.json').exists()]
    pairs +=[(p/n,DEST/p.name/n) for p,r,d in cases for n in ['pico_planejado.json','pico_fast.s2p','pico_auditado.json','pico_dispensa.json','mensagens_pico.json','antes_pico_convergencia.txt','apos_pico_convergencia.txt'] if (p/n).exists()]
    pairs +=[(p/'cad'/n,DEST/p.name/'cad'/n) for p,r,d in cases for n in ['intersecoes.json','manifesto.json','folhas_solidas.json','portas.json','enig_hfss.json','reabertura.json'] if (p/'cad'/n).exists()]
    continuation_files=['sexto_origem.json','sexto_preparacao_auditada.json','sexto_continuidade_auditada.json','sexto_executado.json','antes_sexto_convergencia.txt','sexto_preparar.py','sexto_resolver.py']
    pairs +=[(p/n,DEST/p.name/n) for p,r,d in cases for n in continuation_files if (p/n).exists()]
    for p,r,d in cases:
        frozen=p/'passe5'
        if frozen.exists():
            pairs +=[(f,DEST/p.name/'passe5'/f.relative_to(frozen)) for f in frozen.rglob('*') if f.is_file() and (f.name in allow or (f.parent.name=='metadados' and f.name.endswith('.EMConvData.txt')))]
    for p,r,d in cases:
        records=[]
        for src in p.rglob('*.profile'):
            data=src.read_bytes()
            records.append(dict(arquivo=src.name,sha256=hashlib.sha256(data).hexdigest(),matrix_solve=profile_matrix_solves(data.decode(errors='replace'))))
        evidence=p/'evidencia_recursos_centro.json'
        evidence.write_text(json.dumps(dict(perfis=records,nucleos_por_passe_auditados=r['nucleos_por_passe']),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        pairs.append((evidence,DEST/p.name/evidence.name))
        pairs +=[(src,DEST/p.name/'metadados'/(src.name+'.txt')) for src in p.rglob('*.EMConvData')]
    pairs +=[(ROOT/n,DEST/n) for n in ['README.md','comparacao.json','estudo.json','revisao_pdf.json','revisao_imagens_finais.json']]
    pairs +=[(ROOT/n,DEST/n) for n in ['auditoria_compatibilidade_builder.json','auditoria_builder_multissecao.json','correcao_mascara_lobo_principal.json'] if (ROOT/n).exists()]
    pairs +=[(p,DEST/p.name) for p in ROOT.glob('estimativa_*.json')]
    manifest=[]
    for src,dst in pairs:
        data=src.read_bytes()
        if src.suffix in ['.py','.md']:data=data.replace(b'\r\n',b'\n')
        dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
        manifest.append(dict(arquivo=dst.relative_to(DEST).as_posix(),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    (DEST/'manifesto.json').write_text(json.dumps(dict(arquivos=manifest,melhor_confirmada=best[0].name if best else None,melhor_casamento_banda=best_matching[0].name if best_matching else None),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PACOTE_R13',len(manifest),sum(x['bytes'] for x in manifest))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--empacotar',action='store_true');x=a.parse_args();main(x.empacotar)
