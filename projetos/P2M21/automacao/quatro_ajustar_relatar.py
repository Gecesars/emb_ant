"""Relatorio e pacote compacto R11. Nao simula nem considera metas nao atendidas aprovadas."""
from pathlib import Path
import argparse,hashlib,json,shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from divisor_variantes_comparar import read_pattern

REPO=Path(__file__).resolve().parents[3]
ROOT=Path('D:/dev/EMBRAER/P2M21/R11_Divisor_Ajustes')
BASE=Path('D:/dev/EMBRAER/P2M21/R10_Quatro_Verticais')
DEST=REPO/'projetos/P2M21/quatro_elementos_ajuste'

def main(selected):
    folder=ROOT/selected
    for queue_name in ['fila_505254.json','fila_505254_reajustes.json','fila_alturas.json','fila_altura_reajuste.json']:
        queue_path=ROOT/queue_name
        if queue_path.exists():
            queue=json.loads(queue_path.read_text(encoding='utf-8-sig'))
            assert queue['estado'] in ['TRES_CASOS_CONCLUIDOS_REVISAR_RF','CASOS_CONCLUIDOS_REVISAR_RF'],queue
    assert not (folder/'P2M21_4_elementos.aedt.lock').exists(),'Aguardar fechamento do projeto antes de empacotar'
    r=json.loads((folder/'resultado.json').read_text(encoding='utf-8'))
    cfg=json.loads((folder/'configuracao.json').read_text(encoding='utf-8'))
    geo=json.loads((folder/'geometria.json').read_text(encoding='utf-8'))
    assert cfg['parametros']['simetria'] and cfg['max_passes']==6 and cfg['max_delta_s']==.05 and cfg['nucleos']==14
    assert r['limite_VSWR_exclusivo']==1.3
    records=[]
    for p in sorted(ROOT.glob('*/resultado.json')):
        rr=json.loads(p.read_text(encoding='utf-8'));cc=json.loads((p.parent/'configuracao.json').read_text())
        records.append(dict(nome=p.parent.name,passo_mm=cc['espacamento_vertical_mm'],altura_mm=cc.get('distancia_face_inferior_laminado_ao_refletor_mm',16.61),simetrica=bool(cc['parametros'].get('simetria',False)),resultado=rr))
    ROOT.joinpath('comparacao.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    old=json.loads((BASE/'resultado.json').read_text(encoding='utf-8'))
    fig,axs=plt.subplots(1,2,figsize=(11,6),sharey=True)
    for source,label,color in [(BASE,'Referencia R10','#999999'),(folder,selected,'#176a9b')]:
        for ax,axis in zip(axs,'HV'):
            t,e=read_pattern(source/('AB_'+axis+'.csv'));g=10*np.log10(np.sum(abs(e)**2,axis=1))
            ax.plot(t,g,label=label,color=color,lw=1.6)
    for ax,axis in zip(axs,'HV'):
        ax.set(xlim=(-90,90),ylim=(-20,16),xlabel='Angulo (graus)',title='Corte '+axis);ax.axvline(0,c='gray',lw=.7);ax.grid(alpha=.25);ax.legend()
    axs[0].set_ylabel('Ganho realizado total (dBi)')
    fig.suptitle('Quatro elementos — comparacao em 5,17 GHz\nFontes A e B = 0,5 W / 0°; cabos fisicos de 50 mm')
    fig.text(.5,.025,'Resultados numericos; consultar DeltaS, passes e limitacoes de cada ensaio.',ha='center')
    fig.tight_layout(rect=(0,.07,1,.89));fig.savefig(ROOT/'comparacao_diagramas.png',dpi=180);plt.close(fig)
    h,v=r['cortes']['H'],r['cortes']['V'];p=cfg['parametros']
    pcb_height=cfg.get('distancia_face_inferior_laminado_ao_refletor_mm',16.61)
    rows=[]
    for x in records:
        rr=x['resultado'];hh=rr['cortes']['H'];vv=rr['cortes']['V']
        rows.append(f"| {x['nome']} | {x['passo_mm']:g} | {x['altura_mm']:.3f} | {'sim' if x['simetrica'] else 'histórico descartado'} | {hh['ganho_frontal_dBi']:.3f} | {hh['pico_graus']:+.2f} / {vv['pico_graus']:+.2f} | {rr['VSWR_ativo'][0]:.3f} / {rr['VSWR_ativo'][1]:.3f} | {rr['VSWR_casado'][0]:.3f} / {rr['VSWR_casado'][1]:.3f} | {rr['SLL_V']['nivel_dB']:.2f} | {rr['delta_s']:.6f} | {rr['passes_consecutivos']}/{rr['consecutivos_exigidos']} |")
    dims=[]
    w0=geo['lines']['70.71067811865476']['w_mm'];l0=geo['lines']['70.71067811865476']['l90_mm']
    for pol in 'AB':dims.append(f"| {pol} | {w0*p.get('root_w_'+pol,1):.6f} | {l0*p.get('root_l_'+pol,1):.6f} | {w0*p.get('local_w_'+pol,1):.6f} | {l0*p.get('local_l_'+pol,1):.6f} |")
    status='METAS NUMÉRICAS ATENDIDAS' if r['aprovado'] else 'EM AJUSTE — NÃO LIBERADA'
    spacing=''
    if (ROOT/'espacamento_HFSS.json').exists():
        sd=json.loads((ROOT/'espacamento_HFSS.json').read_text())
        sr=[]
        for q in sd['resultados']:
            sr.append(f"| {q['passo_mm']:g} | {'reposto por meandros' if q['comprimentos_compensados'] else 'trajeto direto'} | {q['ganho_frontal_dBi']:.3f} | {q['VSWR_ativo'][0]:.3f} / {q['VSWR_ativo'][1]:.3f} | {q['SLL_V_dB']:.3f} | {100*q['DeltaS']:.3f}% | {q['consecutivos']}/2 |")
        spacing='''## Comparação de espaçamentos

O estudo comparou o módulo completo, incluindo acoplamento, divisores impressos e dois cabos físicos. A PCB e o refletor mantiveram as dimensões externas. Os caminhos dos quatro radiadores continuam iguais entre si em cada variante, com A/B espelhados. Ao reduzir o passo de 48 para 42 mm, o caminho impresso direto cai de 101,491 para 92,491 mm. A variante compensada repõe 9 mm com meandros iguais: 6 mm na raiz e 3 mm em cada ramo local. Isso preserva o comprimento geométrico, sem demonstrar igualdade de fase real nas descontinuidades.

| Passo mm | Caminho | G0 dBi | VSWR ativo A/B | SLL V dB | ΔS | Consecutivos |
|---:|---|---:|---:|---:|---:|---:|
'''+chr(10).join(sr)+'''

Esses ensaios não demonstram um espaçamento ótimo global nem isolam apenas o fator de arranjo: o deslocamento dos elementos altera o acoplamento e exige reposicionar as trilhas e retornos. A comparação ideal complementar usa quatro fontes pontuais iguais; não fornece ganho ou VSWR do módulo real. Os casos sem convergência completa permanecem preliminares.

![Comparação HFSS dos espaçamentos](espacamento_HFSS.png)

'''
    if (ROOT/'espacamento_505254.json').exists():
        nd=json.loads((ROOT/'espacamento_505254.json').read_text());nr=[]
        for q in nd['resultados']:
            nr.append(f"| {q['passo_mm']:g} | {q['ganho_frontal_dBi']:.3f} | {q['pico_H_graus']:+.2f} / {q['pico_V_graus']:+.2f} | {q['VSWR_ativo'][0]:.3f} / {q['VSWR_ativo'][1]:.3f} | {q['VSWR_casado'][0]:.3f} / {q['VSWR_casado'][1]:.3f} | {q['SLL_V_dB']:.3f} | {100*q['DeltaS']:.3f}% | {q['consecutivos']}/2 |")
        spacing+='''## Pedido adicional: 50, 52 e 54 mm

As três versões usam PCB comum de **70 × 202 mm** e refletor de **90 × 218 × 2 mm**, para comportar o maior espaçamento. As trilhas foram reposicionadas mantendo os quatro caminhos geometricamente iguais e a simetria A/B. Os transformadores de entrada foram pré-dimensionados individualmente por um modelo nominal de duas etapas de linha, calibrado na matriz S da referência de 48 mm. Esse modelo mantém cargas equivalentes congeladas e não prevê o novo acoplamento, as curvas ou as bordas. A tabela abaixo usa somente os resultados reais do HFSS completo.

| Passo mm | G0 dBi | Máximos H/V ° | VSWR ativo A/B | VSWR casado A/B | SLL V dB | ΔS | Consecutivos |
|---:|---:|---:|---:|---:|---:|---:|---:|
'''+chr(10).join(nr)+'''

A referência de 48 mm tem PCB/refletor menores (70 × 184 / 90 × 200 mm); sua comparação com as novas versões não isola apenas o passo. Adaptação interna nas três novas versões: 75%, sem refinamento inicial imposto; continuam limitadas a seis passes, ΔS alvo de 5% e 14 núcleos. Os primeiros casos usam base mista; os reajustes posteriores testam base de primeira ordem, registrada em cada configuração e resultado. A fase aplicada às duas entradas é sempre 0°. Igualdade geométrica dos caminhos não substitui a verificação da distribuição efetiva de corrente, campo e potência.

![Comparação de 50, 52 e 54 mm](espacamento_505254.png)

'''
    heights=''
    if (ROOT/'alturas_HFSS.json').exists():
        hd=json.loads((ROOT/'alturas_HFSS.json').read_text());hr=[]
        for q in hd['casos']:
            hr.append(f"| {q['distancia_laminado_mm']:.3f} | {q['ganho_frontal_dBi']:.3f} | {q['maximo_H_graus']:+.2f} / {q['maximo_V_graus']:+.2f} | {q['abertura_H_graus']:.2f} / {q['abertura_V_graus']:.2f} | {q['VSWR_ativo'][0]:.3f} / {q['VSWR_ativo'][1]:.3f} | {q['VSWR_casado'][0]:.3f} / {q['VSWR_casado'][1]:.3f} | {q['SLL_V_dB']:.3f} | {100*q['DeltaS']:.3f}% | {q['consecutivos']}/2 |")
        heights='''## Distância da PCB ao refletor: −10%, nominal e +10%

O espaçamento de **48 mm** foi selecionado como melhor base numérica entre os módulos testados: a referência de 16,610 mm atingiu simultaneamente ganho frontal ≥12 dBi e todos os VSWR <1,3. Isso não comprova um ótimo global nem elimina a incerteza dos resultados sem convergência completa. Os testes seguintes mantiveram o passo, o desenho das duas faces, as vias, os transformadores, os contornos, os materiais e o setup da referência de 48 mm. A condição nominal foi reutilizada, sem outra simulação.

A distância é medida **da face superior do refletor à face inferior do laminado**. O cobre inferior fica 0,035 mm mais perto. Os dois cabos mantêm 50 mm de comprimento e foram transladados em Z junto com a PCB; o refletor permanece fixo. A auditoria CAD confirmou 42 sólidos por variante, mesmos volumes e envelopes iguais após compensar a translação, sem interseções indevidas. A auditoria planar confirmou diferença nula no cobre, mesmas vias e oito caminhos geométricos de 101,491 mm. Isso preserva a excitação aplicada e a geometria das linhas, mas não impõe uma distribuição ideal de potência aos radiadores.

| Altura mm | G0 dBi | Máximos H/V ° | Aberturas H/V ° | VSWR ativo A/B | VSWR casado A/B | SLL V dB | ΔS | Consecutivos |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
'''+chr(10).join(hr)+'''

Todos os casos de altura usam base mista, adaptação interna de 50%, malha inicial automática, 14 núcleos, máximo de seis passes e ΔS alvo de 5%. Os valores acima são do HFSS completo em 5,17 GHz. Os planos e a rastreabilidade estão em `plano_alturas.json` e `auditoria_cad_alturas.json`.

![Comparação das alturas](alturas_HFSS.png)

'''
    if (ROOT/'v21_altura_menos10_casada/resultado.json').exists():
        retuned=json.loads((ROOT/'v21_altura_menos10_casada/resultado.json').read_text())
        pred=json.loads((ROOT/'v21_altura_menos10_casada/predimensionamento.json').read_text())
        heights+=f'''### Ajuste posterior do transformador na altura de 14,949 mm

Ensaio separado da comparação controlada acima: `v21_altura_menos10_casada`. Mantidos passo de 48 mm, altura de 14,949 mm, planos de retorno, radiadores, cabos, contornos e setup. Alteradas igualmente em A/B somente as seções transformadoras da raiz: largura **{pred['largura_mm']:.6f} mm** e comprimento **{pred['comprimento_mm']:.6f} mm**. O pré-dimensionamento usou a matriz S real da altura menor em um modelo nominal de linha com cargas congeladas; a previsão não foi usada como resultado final. A comparação do cobre confirmou alterações apenas nos sinais F.Cu A/B próximos à raiz, sem mudar retornos ou vias.

O HFSS completo desse ajuste resultou em **G0 {retuned['cortes']['H']['ganho_frontal_dBi']:.5f} dBi**, VSWR ativo **{retuned['VSWR_ativo'][0]:.5f} / {retuned['VSWR_ativo'][1]:.5f}**, VSWR casado **{retuned['VSWR_casado'][0]:.5f} / {retuned['VSWR_casado'][1]:.5f}**, SLL vertical **{retuned['SLL_V']['nivel_dB']:.3f} dB**. Máximos H/V **{retuned['cortes']['H']['pico_graus']:+.2f}° / {retuned['cortes']['V']['pico_graus']:+.2f}°**. Terminou em {retuned['passes']} passes, ΔS **{100*retuned['delta_s']:.4f}%**, {retuned['passes_consecutivos']}/2 consecutivos; convergência completa: **{retuned['convergiu']}**. Esse caso não deve ser confundido com a variante de altura sem reajuste.

'''
    decision=''
    if (ROOT/'selecao_final.json').exists():
        choice=json.loads((ROOT/'selecao_final.json').read_text())
        decision='## Escolha entre os casos testados\n\n'+choice['justificativa']+'\n\n'+choice['limites']+'\n\n'
    md=f'''# Quatro elementos — divisores, espaçamento e refletor R11

**{status}.** Variante apresentada: **{selected}**. {r['passes']} passes em 5,17 GHz, ΔS final **{r['delta_s']:.6f}** ({100*r['delta_s']:.4f}%). HFSS indicou convergência: {r['hfss_indicou_convergencia']}; passes consecutivos abaixo do alvo: **{r['passes_consecutivos']} de {r['consecutivos_exigidos']}**. Convergência completa conforme o setup: **{r['convergiu']}**. Atingir o limite de seis passes ou somente o último ΔS não substitui os dois passes configurados.

{decision}

## Pedido vigente

Quatro radiadores verticais, passo de {cfg['espacamento_vertical_mm']:g} mm na variante apresentada; dois divisores 1:4 impressos; dois cabos físicos iguais de 50 mm. Fontes **A = B = 0,5 W / 0°**, 1 W total. Divisores e retornos acrescentados espelhados, sem compensações distintas entre polarizações. Meta de ganho frontal realizado total ≥12 dBi, VSWR **<1,3** nas duas entradas, máximos H/V em 0° e minimização dos lóbulos secundários verticais. Somente 5,17 GHz, sem GUI, 14 núcleos e no máximo seis passes, alvo ΔS = 0,05. Não houve varredura de frequência.

## Resultado

| Grandeza | Resultado |
|---|---:|
| Ganho realizado total frontal | {h['ganho_frontal_dBi']:.5f} dBi |
| Máximo H / V | {h['pico_graus']:+.2f}° / {v['pico_graus']:+.2f}° |
| Abertura H / V a −3 dB | {h['abertura_graus']:.3f}° / {v['abertura_graus']:.3f}° |
| VSWR ativo A / B, ambas ligadas | {r['VSWR_ativo'][0]:.5f} / {r['VSWR_ativo'][1]:.5f} |
| VSWR A / B, outra entrada casada em 50 Ω | {r['VSWR_casado'][0]:.5f} / {r['VSWR_casado'][1]:.5f} |
| Maior lóbulo secundário vertical frontal | {r['SLL_V']['nivel_dB']:.3f} dB, em {r['SLL_V']['angulo_graus']:+.2f}° |
| Potência aceita, incidente total de 1 W | {r['potencia_aceita_W']:.6f} W |
| Eficiência de radiação / total | {100*r['eficiencia_radiacao']:.3f}% / {100*r['eficiencia_total']:.3f}% |

Frente = +Z; H é φ = 90° (YZ), V é φ = 0° (XZ). Grade angular de 0,25°. Os máximos são os pontos de maior ganho nos cortes frontais, sem girar o sistema de coordenadas. O lóbulo principal vertical é delimitado pelos primeiros mínimos; o SLL é o maior máximo local no hemisfério frontal fora desse intervalo. A referência R10 tinha SLL vertical de −4,101 dB.

## Geometria e transformadores

PCB {cfg['placa_largura_altura_mm'][0]} × {cfg['placa_largura_altura_mm'][1]} mm, núcleo RO4350B 0,76 mm (εr 3,66; tanδ 0,0037), cobre físico 35 µm, ENIG nominal Au 0,0254 µm / NiP 4,5 µm a 1,5 MS/m. Refletor de alumínio {cfg['refletores_mm'][0]} × {cfg['refletores_mm'][1]} × 2 mm; face inferior do núcleo a Z = {pcb_height:.3f} mm em relação ao topo do refletor. Radiadores e vias originais preservados. Sem suportes plásticos ou conectores N. Os cabos incluem cobre e PTFE com perdas nominais, conforme a referência R10.

Nas trilhas planas, a dimensão transversal é a largura. Dimensões iguais nas duas polarizações:

| Polarização | Largura raiz mm | Comprimento raiz mm | Largura local mm | Comprimento local mm |
|---|---:|---:|---:|---:|
{chr(10).join(dims)}

As duas árvores usam uma divisão 1:2 na raiz e duas divisões 1:2 locais. Não são Wilkinson e não há resistores de isolamento. Os parâmetros completos dos planos de massa e das linhas estão em `selecionada/configuracao.json`; a geometria 2D e a auditoria de simetria estão em `selecionada/geometria.json`. A igualdade conferida se refere aos novos divisores e faixas de retorno; o cobre e as transições por vias dos radiadores originais não foram substituídos.

## Ensaios preservados

As variantes anteriores à instrução de manter os divisores espelhados ficaram apenas como histórico. O limite de VSWR foi posteriormente reduzido de 1,5 para 1,3. Os valores abaixo permitem aplicar o requisito atual sem reinterpretar aprovação antiga.

| Variante | Passo mm | Altura mm | Divisores espelhados | G0 dBi | Máximos H/V ° | VSWR ativo A/B | VSWR casado A/B | SLL V dB | ΔS | Consecutivos |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

{spacing}

{heights}

## Verificação e limites

CAD e contatos conferidos antes do solve. Malha da variante apresentada: **{r['major']} Major e {r['minor']} Minor**. Matriz passiva: {r['passivo']}; maior valor singular {r['max_singular']:.7f}; resíduo de reciprocidade {r['residuo_reciprocidade']:.4g}. A recomposição complexa dos campos individuais reproduz A+B com erro relativo máximo {max(r['erros_recomposicao'].values()):.3g}. O balanço da potência aceita entre a matriz S e as grandezas de ganho difere em {r['erro_potencia_W']:.3g} W. Os 14 núcleos foram confirmados nos registros de solução de matriz de todos os passes.

O solver usa Classic, base {'mista' if p.get('basis_order',-1)==-1 else 'de primeira ordem' if p.get('basis_order')==1 else str(p['basis_order'])}, residual iterativo 1e−5, malha inicial automática sem MeshLink, operações locais ou LambdaRefine. Adaptação interna da variante: {p.get('adapt',20)}% por passe. Essa adaptação não aumenta o limite de seis passes. ΔS não é um limite rigoroso do erro físico do ganho ou do apontamento; não houve ensaio independente de estabilidade de malha. Não se qualifica a banda completa, o painel 16×2 ou o ganho MIMO por entrada. Sondas locais de Ez, quando disponíveis, são integrais aproximadas para diagnóstico relativo e não potência por radiador.

![Comparação com R10](comparacao_diagramas.png)

![PCB nas duas faces](selecionada/layout.png)

![Diagramas polares](selecionada/polar_HV.png)

[Projeto HFSS](selecionada/P2M21_4_elementos.aedt) · [CAD](selecionada/4_elementos.FCStd) · [Dados completos](selecionada/resultado.json) · [Touchstone](selecionada/centro.s2p)

O pacote contém nativo e dados compactos; exclui `.aedtresults`, malhas, g3derr, campos volumétricos e locks. Os campos FEM restauráveis permanecem no estudo local em `{folder.as_posix()}`. Sem os resultados locais, o nativo conserva o modelo e exige novo solve para recuperar os campos no AEDT. Não houve compra, nova cotação, email ou liberação de fabricação nesta etapa.
'''
    (ROOT/'README.md').write_text(md,encoding='utf-8')
    DEST.mkdir(parents=True,exist_ok=True)
    selections=['P2M21_4_elementos.aedt','4_elementos.FCStd','configuracao.json','geometria.json','resultado.json','malha.json','HFSS_14nucleos.acf',
        'hfss_validacao.json','convergencia.txt','centro.s2p','qualificacao.json','mensagens.json','criar_cad.py','criar_hfss.py','resolver.py',
        'layout.png','diagramas_HV.png','polar_HV.png','polar_HV.pdf','cad/intersecoes.json','cad/portas.json','cad/folhas_solidas.json','cad/manifesto.json','cad/enig_hfss.json']
    selections += [m+'_'+a+'.csv' for m in ['AB','A','B'] for a in 'HV']
    selections += [p.name for p in folder.glob('*_processo.json')]
    selections += [x for x in ['sondas_resumo.json','sondas.py','predimensionamento.json'] if (folder/x).exists()]
    selections += [x for x in ['caminhos_alimentacao.json'] if (folder/x).exists()]
    pairs=[(folder/f,DEST/'selecionada'/f) for f in selections]
    pairs += [(ROOT/f,DEST/f) for f in ['README.md','comparacao.json','comparacao_diagramas.png','estudo.json','diretriz_simetria.json','diagnostico_referencia.json']]
    pairs += [(ROOT/f,DEST/f) for f in ['espacamento_ideal.json','espacamento_ideal.png'] if (ROOT/f).exists()]
    pairs += [(ROOT/f,DEST/f) for f in ['espacamento_HFSS.json','espacamento_HFSS.png','comparacao_geometrica_espacamento.json'] if (ROOT/f).exists()]
    pairs += [(ROOT/f,DEST/f) for f in ['espacamento_505254.json','espacamento_505254.png','fila_505254.json','fila_505254_reajustes.json','selecoes_505254.json'] if (ROOT/f).exists()]
    pairs += [(ROOT/f,DEST/f) for f in ['plano_alturas.json','auditoria_cad_alturas.json','alturas_HFSS.json','alturas_HFSS.png','fila_alturas.json','fila_altura_reajuste.json','selecao_final.json'] if (ROOT/f).exists()]
    for x in records:
        name=x['nome'];source=ROOT/name
        for f in ['resultado.json','configuracao.json','convergencia.txt','centro.s2p']+[m+'_'+a+'.csv' for m in ['AB','A','B'] for a in 'HV']:
            pairs.append((source/f,DEST/'ensaios'/name/f))
        if name != selected and name in ['v13_passo50_ajustado','v14_passo52_ajustado','v15_passo54_ajustado','v16_passo50_reajustado','v17_passo52_reajustado','v18_passo54_reajustado','v19_altura_menos10','v20_altura_mais10','v21_altura_menos10_casada','v09_transformadores']:
            extras=[f for f in ['predimensionamento.json','caminhos_alimentacao.json'] if (source/f).exists()]
            for f in ['P2M21_4_elementos.aedt','4_elementos.FCStd','geometria.json','layout.png','diagramas_HV.png','polar_HV.png','polar_HV.pdf','HFSS_14nucleos.acf','hfss_validacao.json','malha.json','qualificacao.json','cad/intersecoes.json','criar_cad.py','criar_hfss.py','resolver.py','sondas.py']+extras:
                pairs.append((source/f,DEST/'ensaios'/name/f))
    manifest=[]
    for src,dst in pairs:
        dst.parent.mkdir(parents=True,exist_ok=True);data=src.read_bytes()
        if dst.suffix in ('.md','.py'):data=data.replace(b'\r\n',b'\n')
        dst.write_bytes(data)
        manifest.append(dict(arquivo=dst.relative_to(DEST).as_posix(),sha256=hashlib.sha256(data).hexdigest(),origem_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),bytes=len(data)))
    (DEST/'manifesto.json').write_text(json.dumps(dict(selecionada=selected,aprovado=r['aprovado'],arquivos=manifest),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=status,selecionada=selected,arquivos=len(manifest),bytes=sum(x['bytes'] for x in manifest)),ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('selecionada');a=parser.parse_args();main(a.selecionada)
