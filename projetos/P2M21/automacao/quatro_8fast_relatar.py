"""Relatorio e pacote R12; somente apos centro8 e Fast auditados."""
from pathlib import Path
import json,hashlib,csv,shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from divisor_variantes_comparar import read_pattern
from quatro_8fast_auditar import ROOT,F,B

REPO=Path(__file__).resolve().parents[3];DEST=REPO/'projetos/P2M21/quatro_elementos_8passes_fast'
def main():
    state=json.loads((ROOT/'qualificacao.json').read_text());assert state['estado'] in ['CENTRO8_E_FAST_CONCLUIDOS_REVISAR','CONCLUIDO_CONVERGIDO_COM_METAS_PENDENTES']
    assert not (F/'P2M21_4_elementos.aedt.lock').exists()
    r=json.loads((F/'resultado.json').read_text());old=json.loads((B/'resultado.json').read_text())
    fa=json.loads((ROOT/'auditoria_fast.json').read_text());cont=json.loads((ROOT/'continuidade_auditada.json').read_text())
    assert cont['primeiros_seis_identicos'] and r['passes']==8 and fa['aprovado_fisica']
    fig,axs=plt.subplots(1,2,figsize=(11,5.4),sharey=True)
    for source,label in [(B,'6 passes — referência R11'),(F,'8 passes — continuação R12')]:
        for ax,axis in zip(axs,'HV'):
            t,e=read_pattern(source/('AB_'+axis+'.csv'));g=10*np.log10(np.sum(abs(e)**2,axis=1));ax.plot(t,g,label=label,lw=1.7)
    for ax,axis in zip(axs,'HV'):
        ax.set(xlim=(-90,90),ylim=(-20,16),xlabel='Ângulo (graus)',title='Corte '+axis);ax.grid(alpha=.25);ax.axvline(0,c='gray',lw=.7);ax.legend()
    axs[0].set_ylabel('Ganho realizado total (dBi)')
    fig.suptitle(f"Continuação da mesma malha — 5,17 GHz — A=B=0,5 W / 0°\nΔS6={100*old['delta_s']:.3f}% | ΔS8={100*r['delta_s']:.3f}% | convergiu8: {r['convergiu']}")
    fig.tight_layout(rect=(0,0,1,.87));fig.savefig(ROOT/'comparacao6_8.png',dpi=170);plt.close(fig)
    rows=[]
    for label,x in [('Seis passes (R11)',old),('Oito passes (R12)',r)]:
        h=x['cortes']['H'];v=x['cortes']['V']
        rows.append(f"| {label} | {h['ganho_frontal_dBi']:.5f} | {x['VSWR_ativo'][0]:.5f} / {x['VSWR_ativo'][1]:.5f} | {x['VSWR_casado'][0]:.5f} / {x['VSWR_casado'][1]:.5f} | {h['pico_graus']:+.2f} / {v['pico_graus']:+.2f} | {h['abertura_graus']:.3f} / {v['abertura_graus']:.3f} | {x['SLL_V']['nivel_dB']:.3f} | {100*x['delta_s']:.4f}% | {x['passes_consecutivos']}/2 |")
    bandrows=[]
    for mode,ports in fa['VSWR'].items():
        for x in ports:bandrows.append(f"| {mode} {x['porta']} | {x['minimo']:.5f} | {x['maximo']:.5f} | {x['frequencia_max_GHz']:.3f} | {len(x['pontos_reprovados_1_3'])} |")
    h=r['cortes']['H'];v=r['cortes']['V'];d=cont['comparacao6_8']
    converged='SIM' if r['convergiu'] else 'NÃO'
    md=f'''# P2M21 — continuação de oito passes e sweep Fast R12

**Convergência central: {converged}.** Foram executados somente os passes adicionais **7 e 8**, preservando os seis anteriores e a malha da variante R11 `v21_altura_menos10_casada`. Resultado central: **{h['ganho_frontal_dBi']:.5f} dBi**, VSWR ativo **{r['VSWR_ativo'][0]:.5f}/{r['VSWR_ativo'][1]:.5f}**, ΔS final **{100*r['delta_s']:.4f}%**, {r['passes_consecutivos']}/2 passes consecutivos abaixo de 5%. A conclusão do sweep Fast não significa qualificação do ganho em toda a banda.

## Configuração preservada

Quatro radiadores, passo **48 mm**, distância entre face inferior do laminado e topo do refletor **14,949 mm**; RO4350B 0,76 mm, cobre de 35 µm e ENIG nominal. Dois divisores 1:4 impressos espelhados, transformadores de raiz com **0,656371 mm de largura × 9,000142 mm de comprimento**. Dois cabos físicos de 50 mm, com as perdas nominais do modelo; sem suportes plásticos. Fontes **A=B=0,5 W/0°**, 1 W incidente total. Sem GUI, **14 núcleos**, Classic/base mista, adaptação de 50%, residual iterativo de 1e−5, sem refinamentos locais ou LambdaRefine iniciais.

O limite foi alterado de 6 para 8 e o mínimo para 8 para executar exatamente dois passes adicionais. Geometria, materiais, fronteiras e operações de malha permaneceram iguais. Ao editar, o AEDT normalizou o default inativo `Target` de 0,3333 para 0,6667; `DoLambdaRefine=false` e `SetLambdaTarget=false` permaneceram. A auditoria interrompeu antes de qualquer solve para investigar: os cinco arquivos críticos de malha/campos estavam idênticos byte a byte, e a execução posterior confirmou início no passe 7 e histórico 1–6 idêntico. Não houve reinício do zero ou alteração do alvo ΔS.

## Ganho e diagramas somente em 5,17 GHz

| Caso | G0 dBi | VSWR ativo A/B | VSWR casado A/B | Máximos H/V ° | Aberturas H/V ° | SLL vertical dB | ΔS | Consecutivos |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

Frente=+Z, H=φ90° (YZ), V=φ0° (XZ), grade angular de 0,25°. SLL é o maior máximo local no hemisfério frontal fora dos primeiros mínimos do lóbulo principal. Entre 6 e 8 passes: ΔG0 **{d['ganho_frontal_dB']:+.5f} dB**, ΔaberturaH **{d['abertura_H_graus']:+.3f}°**, ΔaberturaV **{d['abertura_V_graus']:+.3f}°**. Essas diferenças descrevem a estabilidade observada; não são uma estimativa rigorosa de erro físico.

Metas centrais: ganho≥12 dBi **{r['metas']['ganho12']}**; VSWR ativo<1,3 **{r['metas']['VSWR_ativo']}**; VSWR casado<1,3 **{r['metas']['VSWR_casado']}**; máximos H/V exatamente0° na grade **{r['metas']['maximos_zero_na_grade']}**. Convergência de S não garante por si só estabilidade de todos os detalhes do diagrama.

![Comparação dos passes](comparacao6_8.png)

![Diagramas polares E/Emax](centro/polar_HV.png)

## Sweep Fast: 5,09 a 5,25 GHz

**161 pontos de saída, espaçados de 1 MHz**, portas referidas a 50 Ω, sem geração de diagramas fora do centro. O Fast usa a malha adaptada e o método ALPS; seus pontos não são 161 adaptações independentes. [Documentação do Fast no AEDT2024R2](https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v242/en/Subsystems/HFSS/Content/HFSS/FastFrequencySweeps.htm). Os diagramas acima vêm de `Centro : LastAdaptive`, em 5,17 GHz. A matriz do Fast no centro difere da adaptativa por no máximo **{fa['diferenca_S_centro_fast_adaptativo']:.3g}** em valor absoluto complexo.

| Condição/entrada | VSWR mínimo | VSWR máximo | Frequência do máximo GHz | Pontos com VSWR≥1,3 |
|---|---:|---:|---:|---:|
{chr(10).join(bandrows)}

Todos os VSWR ativos e casados abaixo de 1,3 nos 161 pontos: **{fa['todos_VSWR_menores_1_3']}**. O sweep foi concluído sem novos passes adaptativos; o histórico antes/depois é idêntico. Ganho e aberturas fora de 5,17 GHz **não foram avaliados**, conforme solicitado.

![VSWR na banda](vswr_banda_fast.png)

## Auditorias e arquivos

Malha central: **{r['major']} Major/{r['minor']} Minor**. Matriz central passiva/recíproca, resíduo de reciprocidade **{r['residuo_reciprocidade']:.3g}**; erro da recomposição complexa de A+B **{max(r['erros_recomposicao'].values()):.3g}**. Potência aceita **{r['potencia_aceita_W']:.6f} W**, eficiência de radiação **{100*r['eficiencia_radiacao']:.3f}%**. No Fast, maior valor singular **{fa['maior_singular']:.7f}**, maior resíduo de reciprocidade **{fa['residuo_reciprocidade']:.3g}**. O alvo ΔS foi conferido no setup e na exportação; os 14 núcleos foram conferidos nos passes.

[HFSS com setup e Fast](centro/P2M21_4_elementos.aedt) · [CAD](centro/4_elementos.FCStd) · [Polar PDF](centro/polar_HV.pdf) · [S2P Fast](centro/banda_fast.s2p) · [VSWR CSV](vswr_banda_fast.csv) · [Resultado central](centro/resultado.json) · [Auditoria da continuidade](continuidade_auditada.json).

Os nativos, Touchstones, cortes distantes e evidências compactas acompanham o relatório. Malhas, `.aedtresults`, campos volumétricos e locks permanecem somente no estudo local `{F.as_posix()}`. O nativo sem resultados permite editar o modelo; recuperar campos FEM em outra máquina exige novo solve. A referência R11 foi preservada. Esta etapa não qualifica o painel 16×2, desempenho MIMO por entrada, fabricação ou banda de ganho.
'''
    (ROOT/'README.md').write_text(md,encoding='utf-8')
    files=['P2M21_4_elementos.aedt','4_elementos.FCStd','configuracao.json','geometria.json','HFSS_14nucleos.acf','layout.png','caminhos_alimentacao.json','convergencia.txt','centro.s2p','banda_fast.s2p','resultado.json','malha.json','qualificacao.json','diagramas_HV.png','polar_HV.png','polar_HV.pdf']+[m+'_'+a+'.csv' for m in ['AB','A','B'] for a in 'HV']
    pairs=[(F/f,DEST/'centro'/f) for f in files]
    compact=['README.md','qualificacao.json','origem.json','preparacao_auditada.json','continuidade_auditada.json','auditoria_fast.json','sweep_configurado.json','antes_convergencia.txt','apos_fast_convergencia.txt','vswr_banda_fast.csv','vswr_banda_fast.png','comparacao6_8.png','mensagens_centro.json','mensagens_fast.json','cache_preservado.json']
    pairs +=[(ROOT/f,DEST/f) for f in compact]
    if (ROOT/'fast_recursos.json').exists():pairs.append((ROOT/'fast_recursos.json',DEST/'fast_recursos.json'))
    if (ROOT/'revisao_entrega.json').exists():pairs.append((ROOT/'revisao_entrega.json',DEST/'revisao_entrega.json'))
    pairs +=[(p,DEST/'referencia6'/p.name) for p in B.iterdir() if p.is_file() and p.suffix not in ['.aedt']]
    pairs +=[(p,DEST/'metadados'/(p.name+'.txt')) for p in (F/'P2M21_4_elementos.aedtresults').rglob('*.EMConvData')]
    manifest=[]
    for src,dst in pairs:
        dst.parent.mkdir(parents=True,exist_ok=True);data=src.read_bytes()
        if dst.suffix in ['.py','.md']:data=data.replace(b'\r\n',b'\n')
        dst.write_bytes(data);manifest.append(dict(arquivo=dst.relative_to(DEST).as_posix(),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
    (DEST/'manifesto.json').write_text(json.dumps(dict(arquivos=manifest,passes=8,passes_adicionais=2,convergiu=r['convergiu'],fast_pontos=161),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PACOTE_R12',len(manifest),sum(x['bytes'] for x in manifest))

if __name__=='__main__':main()
