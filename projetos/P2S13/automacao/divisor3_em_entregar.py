"""Relatorio das duas geometrias do divisor, nativos e evidencias sem malhas."""
from pathlib import Path
import json,hashlib,shutil,zipfile
REPO=Path(__file__).resolve().parents[3];BASE=Path('D:/dev/EMBRAER/P2S13/R08_Divisor_HFSS');FINAL=BASE/'c01_juncao'
OUT=REPO/'projetos/P2S13/divisor_duplo_1x3_hfss';OUT.mkdir(exist_ok=True)
r=json.loads((FINAL/'resultado.json').read_text());old=json.loads((BASE/'resultado.json').read_text());cfg=json.loads((FINAL/'configuracao.json').read_text())
nx=json.loads((FINAL/'circuito/verificacao_nexxim.json').read_text());diag=json.loads((FINAL/'diagnostico_divisao.json').read_text())
assert nx['matriz_conferida'] and nx['erro_absoluto_max']<2e-6
assert cfg['juncao_corrigida'] and max(diag['sobreposicao_linha_central_com_juncao_entrada_segundo_estagio_mm'].values())<1e-6
hist=json.loads((FINAL/'historico_passes.json').read_text());status=lambda b:'sim' if b else 'não'
rows=[]
for label,x in [('Inicial — junção lateral',old),('C01 — junção corrigida',r)]:
    rows.append('| %s | %d / %.6f | %d/2 | %.4f / %.4f | %.4f | %.3f / %.3f |'%(label,x['passes'],x['delta_s'],x['consecutivos'],*x['VSWR_ativo'],x['cortes']['H']['ganho_frontal_dBi'],x['cortes']['H']['abertura_graus'],x['cortes']['V']['abertura_graus']))
traces=[t for t in cfg['traces'] if t['name'].startswith('A_')]
table=['| %s | %.3f | %.3f | %.3f |'%(t['name'][2:],t['Z_ohm'],t['width_mm'],t['length_mm']) for t in traces]
waves=['| %s | %.6f | %+.3f |'%(name,p,f) for name,p,f in zip(r['ordem_S8_circuito'][2:],r['ondas_incidentes_antena_potencia_W'],r['ondas_incidentes_antena_fase_relativa_graus'])]
md=f'''# P2S13 — divisor duplo 1:3 físico no HFSS

Rodada de **11/11/2026**, somente **5,17 GHz**, sem sweep. Foram construídas duas redes 1:3 espelhadas, simuladas juntas como uma PCB de oito portas, e conectadas à matriz S6 real das três placas de dois elementos. Duas fontes externas de **0,5 W / 0°**, total 1 W. A antena R06 permaneceu inalterada; os seis cabos físicos de 50 mm e suas perdas já estão no S6 e não foram duplicados.

**Resultado da C01:** ganho frontal realizado **{r['cortes']['H']['ganho_frontal_dBi']:.4f} dBi**, H **{r['cortes']['H']['abertura_graus']:.3f}°**, V **{r['cortes']['V']['abertura_graus']:.3f}°**. VSWR ativo A/B **{r['VSWR_ativo'][0]:.4f}/{r['VSWR_ativo'][1]:.4f}**; outra entrada casada em 50 Ω **{r['VSWR_outra_casada'][0]:.4f}/{r['VSWR_outra_casada'][1]:.4f}**. Meta VSWR≤1,25 nos quatro casos: **{status(r['meta_VSWR_1p25'])}**. Meta anterior de ganho≥13 dBi: **{status(r['meta_ganho_13dBi'])}**. A qualificação completa continua pendente das limitações numéricas e físicas abaixo.

## Geometria construída e correção

A implementação plana usa, em cada polarização, um Wilkinson desigual que divide em 1/3 e 2/3, seguido de um Wilkinson igual no ramo de 2/3. Transformadores levam as saídas intermediárias para 50 Ω. O ramo de 1/3 recebe compensação de fase. Essa arquitetura substitui o Wilkinson 1:3 com três resistores em triângulo do estudo de circuito, cuja interligação exigiria cruzamentos no layout. Há dois resistores por polarização: 106,066 Ω e 100 Ω.

A PCB tem **220 × 64 mm**, ZYF300CA-C de núcleo **1,52 mm**, εr=2,94, tanδ=0,0016, cobre físico de 35 µm e ENIG nominal. A largura cresceu de 60 para 64 mm para acomodar as trilhas com margem à borda. As seis saídas mantêm X=−93,491/+2,509/+98,509 mm e Y=±18 mm, alinhadas aos cabos existentes. O modelo tem 40 sólidos válidos; o CAD reaberto confere e não há interpenetração volumétrica entre peças. Os sólidos são BREP gerados a partir de configuração e scripts; não se trata de uma PCB KiCad ou Gerber liberado.

A primeira geometria revelou uma junção de entrada lateral cobrindo **3,792 mm da linha central E1** e zero em E2. Essa sobreposição fazia parte do metal comum de entrada e alterava o comprimento efetivo de um ramo, sem curto entre as duas polarizações. Na C01, a entrada do segundo estágio foi deslocada para chegar pela esquerda, com **zero sobreposição de linha central em E1 e E2**. Recalcularam-se os percursos e o ajuste comum de entrada; ambos continuam idênticos nas polarizações A/B. A geometria inicial e seus resultados foram preservados em `inicial`.

![Layout físico corrigido](c01_juncao/layout.png)

| Trecho de cada polarização | Z nominal (Ω) | Largura (mm) | Linha central (mm) |
|---|---:|---:|---:|
{chr(10).join(table)}

Os números de linha são valores de síntese, não impedâncias uniformes garantidas em curvas/junções. A soma da fase de BYPASS+OUT1 é projetada como equivalente a DELAY+90°+OUT3, menos uma onda guiada de 50 Ω; por isso os comprimentos físicos de saída não são iguais. A igualdade de fase nominal foi calculada somente no centro. O HFSS determina a fase efetiva, com franjamento, curvas, acoplamento e transições. Não há verificação de banda.

Os resistores são um modelo nominal de montagem flip-chip **CH0402F**, com corpo de 1,0×0,6×0,5 mm, pads de 0,65 mm e vão de 0,4 mm, conforme dimensões de referência do [fabricante Vishay](https://www.vishay.com/docs/53014/ch.pdf). A resistência é uma boundary Lumped RLC resistiva entre os pads; o corpo usa alumina εr=9,8/tanδ=0,0001 **assumidos**. Não foi importado Touchstone de componente real, nem validadas tolerância, dissipação máxima ou disponibilidade do valor exato. O cobre inclui rugosidade nominal de 0,5 µm; ENIG Au 0,0254 µm / NiP 4,5 µm, σNiP=1,5 MS/m, conforme os estudos anteriores. Os terminais locais incluem pino, solda SAC305 e curto acesso PTFE. São oito portas lumped de 50 Ω, com polaridade sinal→massa compatível com o S6.

## Execução e convergência

Foram executadas **duas geometrias distintas, cada uma limitada a seis passes**; não houve continuação além do sexto passe nem sweep de frequência. Ambas usaram 14 núcleos em todos os passes adaptativos, HFSS 2024 R2 headless, Classic, sem operações locais de pré-refinamento, sem MeshLink, sem refinamento lambda, BasisOrder1 e solver iterativo com residual1×10⁻⁵. O critério foi ΔS≤0,05 por dois passes consecutivos. As geometrias são diferentes, portanto a segunda rodada começou com sua própria malha.

| Geometria | Passes / ΔS | Consecutivos | VSWR ativo A/B | G frontal (dBi) | H / V (°) |
|---|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

Na C01, a malha final tem **{hist[-1]['tetraedros']} tetraedros**. Último ΔS **{r['delta_s']:.8f}**; contador **{r['consecutivos']}/2**; auditoria de convergência completa: **{status(r['convergiu'])}**. O texto exportado pelo HFSS escreve `Converged : Yes` quando o último passe atende ao alvo, mesmo quando o contador ainda é 1/2. O indicador genérico não substitui a exigência de dois passes. O [histórico](c01_juncao/historico_passes.json), o [arquivo nativo de convergência](c01_juncao/convergencia.txt) e os [recursos por passe](c01_juncao/recursos_matriz.json) ficam disponíveis.

Reparos Major/Minor C01: **{r['malha_major']}/{r['malha_minor']}**. Isso não implica que todos os tetraedros tenham qualidade ideal; os cabeçalhos compactos dos avisos estão em [malha.json](c01_juncao/malha.json), sem os triângulos do g3derr. Maior singular do S8 **{r['passividade_divisor']:.7f}**, e erro máximo de reciprocidade **{r['reciprocidade_divisor']:.7g}**; referência estrita de reciprocidade dos estudos anteriores: 1×10⁻⁵.

## Circuito carregado e diagramas

O S8 completo do HFSS foi reordenado por nome de porta para IN_A, IN_B, R1_A/B, R2_A/B, R3_A/B. Conectou-se ao S6 sem simetrizar, extrapolar ou alterar matrizes. A solução usa todas as reflexões múltiplas e o acoplamento conduzido, e recompõe os campos complexos de cada porta da antena. A interconexão foi conferida por solução matricial, scikit-rf Circuit e **Ansys Circuit/Nexxim**, erro máximo **{nx['erro_absoluto_max']:.3g}**. As redes são todas de um ponto real: 5,17 GHz.

| Porta da antena | Potência incidente (W) | Fase relativa a R2_A (°) |
|---|---:|---:|
{chr(10).join(waves)}

Mesmo com as duas fontes externas iguais/em fase, as reflexões e a distribuição física produzem dispersão de amplitude **{r['dispersao_amplitude_dB']:.3f} dB** e fase **{r['dispersao_fase_graus']:.3f}°** nas seis entradas da antena. Não confundir a condição das fontes com alimentação efetiva uniforme nas seis portas. [Diagnóstico em cargas de 50 Ω e com antena](c01_juncao/diagnostico_divisao.json).

![Potência e fase](c01_juncao/distribuicao.png)

Para 1 W incidente, o circuito devolve **{r['potencia_refletida_W']:.6f} W** às fontes, entrega **{r['potencia_aceita_antena_W']:.6f} W** líquidos ao modelo da antena e tem diferença de potência **{r['perda_divisor_dissipacao_mais_radiacao_W']:.6f} W** no divisor. Essa diferença inclui dissipação nos materiais/resistores e radiação do divisor; não foi separada por mecanismo. O ganho reportado é o campo radiado pela antena recomposto e referido à potência incidente nas duas entradas externas.

Máximos H/V: **{r['cortes']['H']['pico_graus']:+.2f}°/{r['cortes']['V']['pico_graus']:+.2f}°**. O corte H continua com topo amplo e dois máximos próximos; a troca do lado do maior pico não representa sozinha uma grande alteração do feixe. SLL vertical frontal: **{r['cortes']['V']['SLL']['nivel_dB']:.3f} dB**, referência ao máximo do corte.

![Diagramas polares](c01_juncao/polar_HV.png)

![Comparação com alimentação direta](c01_juncao/comparacao_HV.png)

## Limites e arquivos

A radiação direta da placa distribuidora e o acoplamento espacial entre distribuidora, refletor e antena **não são somados** na recomposição de blocos separados. O S8 incorpora a potência perdida por radiação do divisor como redução da potência entregue. O S6 da antena conserva as pendências anteriores de estabilidade dos nove campos e reciprocidade; seu hash permanece `{r['S6_sha256']}`. As metas numéricas de centro não constituem qualificação do produto ou aprovação para fabricação. A análise sem sweep não comprova comportamento em 5,09–5,25 GHz.

[HFSS físico C01](c01_juncao/Divisor_Duplo3.aedt) · [FreeCAD C01](c01_juncao/Divisor_Duplo3.FCStd) · [S8 EM](c01_juncao/divisor.s8p) · [S2 do conjunto](c01_juncao/conjunto.s2p) · [Resultado completo](c01_juncao/resultado.json) · [Circuito portátil Nexxim](c01_juncao/circuito/P2S13_Divisor_EM_sem_malhas.aedtz).

O AEDTZ contém os Touchstones externos e pode ser restaurado em outro diretório; o `.aedt` simples conserva caminhos locais. Nativos, CAD, campos distantes derivados e evidências compactas estão no [manifesto](manifesto.json); a solução FEM completa permanece local, sem `.aedtresults`, malhas, g3derr ou locks no Git. O caso inicial também foi arquivado para não ocultar a correção. Nenhuma nova simulação foi agendada.

Reprodução pelos scripts `divisor3_em_*.py` em `../automacao`. Para C01: `P2S13_DIV3_ROOT={FINAL.as_posix()}` e `P2S13_DIV3_JUNCAO=1` na preparação, em pasta vazia. A criação recusa sobrescrever nativo existente. O CAD é gerado em FreeCADCmd isolado; a criação/solve HFSS usa a mesma variável de diretório. Trabalhos originais permanecem preservados.
'''
(OUT/'README.md').write_text(md,encoding='utf8')
records=[]
direct=['Divisor_Duplo3.aedt','Divisor_Duplo3.FCStd','HFSS_14nucleos.acf','configuracao.json','hfss_validacao.json','estado.json',
        'convergencia.txt','historico_passes.json','recursos_matriz.json','mensagens.json','malha.json','resultado.json','diagnostico_divisao.json',
        'divisor.s8p','divisor_ordenado.s8p','conjunto.s2p','referencia_linhas.s4p','diagrama_H.csv','diagrama_V.csv','layout.png','polar_HV.png','comparacao_HV.png','distribuicao.png']
for folder,sub in [(BASE,'inicial'),(FINAL,'c01_juncao')]:
    assert not (folder/'Divisor_Duplo3.aedt.lock').exists()
    paths=[folder/n for n in direct]+list((folder/'cad').glob('*.json'))+list((folder/'cad').glob('*.step'))
    paths+=[p for p in (folder/'circuito').iterdir() if p.is_file() and p.suffix in ['.aedt','.aedtz','.s8p','.s6p','.s2p','.json']]
    for p in paths:
        assert p.is_file(),p
        if p.suffix=='.aedtz' and zipfile.is_zipfile(p):
            with zipfile.ZipFile(p) as z:assert not any('.aedtresults' in n or n.endswith(('.ngmesh','.g3derr','.lock')) for n in z.namelist())
        dest=OUT/sub/p.relative_to(folder);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        h=hashlib.sha256(p.read_bytes()).hexdigest();assert hashlib.sha256(dest.read_bytes()).hexdigest()==h
        records.append(dict(arquivo=dest.relative_to(REPO).as_posix(),fonte=str(p),sha256=h,bytes=p.stat().st_size))
(OUT/'manifesto.json').write_text(json.dumps(dict(artefatos=records,total_bytes=sum(x['bytes'] for x in records)),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('ENTREGA_PRONTA',len(records),'arquivos')
