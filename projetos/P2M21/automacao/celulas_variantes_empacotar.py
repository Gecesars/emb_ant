"""Arquiva apenas projetos fechados e evidencias compactas revisadas; sem malhas."""
from pathlib import Path
import json,hashlib,shutil
REPO=Path(__file__).resolve().parents[3];WORK=Path('D:/dev/EMBRAER/P2M21')
DEST=REPO/'projetos/P2M21/comparacao_colunas_niveis'
CASES=['R15_Oito_Celulas_8passes','R16_Oito_Celulas_78mm','R17_Dez_Celulas_78mm']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def copy(source,dest,manifest):
    assert source.is_file() and source.stat().st_size<100*1024**2,source
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest);assert sha(source)==sha(dest)
    manifest.append(dict(origem=str(source),arquivo=dest.relative_to(DEST).as_posix(),bytes=source.stat().st_size,sha256=sha(source)))
def main():
    manifest=[]
    for case in CASES[:2]:
        root=WORK/case;cfg=json.loads((root/'configuracao.json').read_text());r=json.loads((root/'resultado.json').read_text())
        assert json.loads((root/'qualificacao.json').read_text())['estado']=='ANALISE_CONCLUIDA' and r['fisica_ok']
        assert not (root/(cfg['native']+'.lock')).exists()
        qa=json.loads((root/'revisao_visual.json').read_text());assert qa['aprovado'] and all(sha(root/x['arquivo'])==x['sha256'] for x in qa['arquivos'])
        dest=DEST/case
        names=[cfg['native'],cfg.get('cad_native','P2M21_8celulas.FCStd'),'configuracao.json','qualificacao.json','resultado.json','historico_passes.json','convergencia.txt','HFSS_14nucleos.acf','malha.json','solver_efetivo.json','recursos_matriz.json','ordem_fontes.json','mensagens.json','centro.s%dp'%len(cfg['portas']),'comparacao.json','comparacao.csv','polar_HV.png','acoplamento_vswr.png','comparacao_diagramas.png','revisao_visual.json']
        names+=list(p.name for p in root.glob('*.csv'))
        names+=[n for n in ['origem.json','preparacao_auditada.json','continuidade_auditada.json','preservacao_R14.json','antes_convergencia.txt','hfss_validacao.json','estimativa.json','montagem_duas_faces.png','revisao_geometria.json'] if (root/n).exists()]
        for n in sorted(set(names)):copy(root/n,dest/n,manifest)
        if (root/'cad').exists():
            for p in (root/'cad').glob('*.json'):copy(p,dest/'cad'/p.name,manifest)
        res=(root/cfg['native']).with_suffix('.aedtresults')
        for p in res.rglob('*'):
            if p.is_file() and p.suffix in ['.profile','.EMConvData','.ExprCache']:
                relative=p.relative_to(res)
                copy(p,dest/'evidencias'/relative.with_name(relative.name+'.txt'),manifest)
        h,v=r['cortes']['H'],r['cortes']['V']
        text=f'''# {case}

Resultado em 5,17 GHz, {len(cfg['celulas'])} placas / {cfg['radiadores']} radiadores. {len(cfg['portas'])} portas iguais em fase, {cfg['potencia_por_porta_W']} W por porta, 1 W total. 14 nucleos, sem GUI, sem sweep. Cabos fisicos de 50 mm com perdas nominais; sem rede externa.

O ganho realizado inclui as perdas dieletricas do RO4350B (tan(delta) nominal 0,0037), inclusive nos dois divisores 1:4 impressos de cada PCB, as perdas dos condutores/cabos modelados e o descasamento. A futura distribuicao externa de duas entradas para as placas ainda nao faz parte deste modelo.

**Convergiu: {r['convergiu']}. Validado numericamente: {r['validado_numericamente']}.** {r['passes']} passes; DeltaS {r['delta_s']:.8f}; alvo 0,05; estabilidade das nove sondas: {r['estavel_nove_sondas']}. Ganho frontal total {h['ganho_frontal_dBi']:.5f} dBi.

| Corte | Abertura -3dB | Maximo | SLL frontal |
|---|---:|---:|---:|
| H | {h['abertura_graus']:.4f} graus | {h['pico_graus']:+.2f} graus | {h['SLL']['nivel_dB']:.4f} dB |
| V | {v['abertura_graus']:.4f} graus | {v['pico_graus']:+.2f} graus | {v['SLL']['nivel_dB']:.4f} dB |

VSWR ativo maximo {max(x for x in r['VSWR_ativo'] if x is not None):.5f}; com outras portas casadas {max(x for x in r['VSWR_casado'] if x is not None):.5f}. Matriz passiva e reciproca, potencia e recomposicao de campos conferidas em resultado.json. O ganho se refere a todas as fontes coerentes, nao a uma entrada MIMO independente.

![Diagramas polares E/Emax](polar_HV.png)

O nativo AEDT preserva a geometria e configuracao; as malhas/campos FEM restauraveis permanecem somente na pasta local de trabalho. Para usar outro caso de excitacao no HFSS, ajustar EditSources conforme oito_celulas_resolver.py. Os nomes dos relatorios nao fixam sozinhos as fontes; o arquivo foi salvo com todas ativas.
'''
        (dest/'README.md').write_text(text,encoding='utf-8',newline='\n')
    # O terceiro ensaio foi interrompido pelo usuario; nunca criar resultado RF substituto.
    root=WORK/CASES[2];dest=DEST/CASES[2]
    interrupted=json.loads((root/'interrupcao_usuario.json').read_text())
    assert interrupted['estado']=='INTERROMPIDO_A_PEDIDO_DO_USUARIO'
    cfg=json.loads((root/'configuracao.json').read_text())
    for n in [cfg['native'],cfg['cad_native'],'configuracao.json','qualificacao.json','interrupcao_usuario.json','hfss_validacao.json','revisao_geometria.json','ordem_fontes.json','HFSS_14nucleos.acf','montagem_duas_faces.png']:
        copy(root/n,dest/n,manifest)
    for p in (root/'cad').glob('*.json'):copy(p,dest/'cad'/p.name,manifest)
    (dest/'README.md').write_text('# R17 — interrompida pelo usuario\n\nDez placas / 40 radiadores, passo entre colunas 78 mm. Simulacao interrompida durante o segundo passe em 10/11/2026. Nao ha ganho, VSWR ou diagrama final. O nativo preserva a geometria preparada; nenhum solver deve ser retomado sem nova instrucao. A mecanica preliminar foi concluida na R18.\n',encoding='utf-8')
    root=WORK/'comparacao_colunas_niveis'
    for n in ['plano.json','pipeline.json','regressao_analisador.json']:copy(root/n,DEST/n,manifest)
    (DEST/'README.md').write_text('''# Historico dos ensaios — interrompido a pedido do usuario

Os testes foram encerrados em 10/11/2026 para concluir a [mecanica PRELIMINAR R18](../mecanica_preliminar_R18/README.md). Nao ha solver ativo nem retomada automatica.

| Caso | Ganho frontal total | H / V | DeltaS | Estado |
|---|---:|---:|---:|---|
| [R15: oito placas, 72 mm, oito passes](R15_Oito_Celulas_8passes/README.md) | 19,84687 dBi | 24,3513 / 3,7484 graus | 0,05001533 | Nao convergido |
| [R16: oito placas, 78 mm, seis passes](R16_Oito_Celulas_78mm/README.md) | 19,47983 dBi | 22,9569 / 3,7125 graus | 0,10314416 | Nao convergido |
| [R17: dez placas, 78 mm](R17_Dez_Celulas_78mm/README.md) | Sem resultado final | Sem resultado final | — | Interrompido no segundo passe |

Todos os valores calculados acima sao preliminares, em 5,17 GHz, com todas as entradas iguais e em fase, 1 W total, cabos fisicos de 50 mm e divisores impressos incluidos. Nao incluem a futura distribuicao externa de duas entradas. O alargamento de 72 para 78 mm nao comprovou melhora de ganho ou lobulos; a falta de convergencia impede uma conclusao de projeto. A R14 original e seus resultados permanecem preservados byte a byte, conforme preservacao_R14.json. Nenhum sweep foi executado.

O manifesto preserva nativos e evidencias compactas; malhas e campos FEM ficam somente no diretorio local de trabalho. O lock remanescente da interrupcao nao e copiado.
''',encoding='utf-8',newline='\n')
    (DEST/'manifesto.json').write_text(json.dumps(dict(arquivos=manifest,malhas_incluidas=False,campos_volumetricos_incluidos=False),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    prohibited=[p for p in DEST.rglob('*') if p.is_file() and (p.suffix in ['.g3derr','.lock','.adp','.ngmesh'] or '.aedtresults' in str(p))]
    assert not prohibited,prohibited
    print('PACOTE_VERIFICADO',len(manifest),sum(e['bytes'] for e in manifest))
if __name__=='__main__':main()
