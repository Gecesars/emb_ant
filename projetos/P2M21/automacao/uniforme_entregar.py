"""Organizar resultados numericamente auditados, sem malha; revisar PNG antes da entrega."""
from pathlib import Path
import json,hashlib

repo=Path(__file__).resolve().parents[3]
root=Path('D:/dev/EMBRAER/P2M21/R02_Malha_Uniforme17')
dest=repo/'projetos/P2M21/ensaio_uniforme'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
cfg=read(root/'configuracao.json');data=read(root/'antena/auditoria_banda.json')
assert data['aprovado'] and data['n_pontos']==17
assert read(root/'qualificacao.json')['estado']=='CALCULOS_CONCLUIDOS_REVISAR'
items=[]
def copy(source,target):
    payload=source.read_bytes();digest=hashlib.sha256(payload).hexdigest()
    target=dest/target;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(payload)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
    items.append(dict(caminho=target.relative_to(repo).as_posix(),bytes=len(payload),sha256=digest,fonte=str(source)))
for name in ['configuracao.json','qualificacao.json','resultados_centro.csv','resultados_banda.csv','ganho_aberturas_17pontos.png']:
    copy(root/name,Path(name))
for name in ['preparacao.json','verificacao_preparacao.json','convergencia_centro.txt','convergencia_banda.txt',
             'auditoria_centro.json','auditoria_banda.json','malha_centro.json','malha_banda.json',
             'historico_centro.json','historico_banda.json','mensagens_centro.json','mensagens_banda.json',
             'centro.s64p','banda.s64p',cfg['native']]:
    copy(root/'antena'/name,Path('hfss')/name)
for stage in ['centro','banda']:
    for source in (root/'antena'/stage).glob('*/*.csv'):
        copy(source,Path('campos')/stage/source.parent.name/source.name)
assert len(list((dest/'campos/banda').glob('*/*.csv')))==34
rows=data['pontos'];center=rows[8];conv=data['convergencia']
def fmt(x,n=2):return f'{x:.{n}f}'.replace('.',',')
head=(dest/'README.md').read_text(encoding='utf8').split('## Resultados verificados')[0]
head=head.replace('**Estado: cálculo em andamento, sem resultado novo aprovado.** Esta página será atualizada após a auditoria.',
 '**Estado: cálculo e auditoria dos 17 pontos concluídos.** Os resultados abaixo usam a excitação uniforme direta solicitada.')
table='\n'.join('| '+ ' | '.join([fmt(r['frequencia_GHz']),fmt(r['ganho_frontal_total_realizado_dBi']),fmt(r['abertura_H_graus']),fmt(r['abertura_V_graus'])])+' |' for r in rows)
summary=f'''\n## Resultados verificados

No centro, **5,17 GHz**: ganho frontal realizado total **{fmt(center['ganho_frontal_total_realizado_dBi'])} dBi**, H **{fmt(center['abertura_H_graus'])}°** e V **{fmt(center['abertura_V_graus'])}°**.

Nos 17 pontos, o ganho varia de **{fmt(data['ganho_min_dBi'])} a {fmt(data['ganho_max_dBi'])} dBi**, H de **{fmt(data['H_min_graus'])} a {fmt(data['H_max_graus'])}°** e V de **{fmt(data['V_min_graus'])} a {fmt(data['V_max_graus'])}°**. A meta de 21 dBi com alimentação direta uniforme foi **{'atendida' if data['meta_21dBi_todos_pontos'] else 'não atendida'} em todos os pontos**. Isso não equivale ao ganho por entrada MIMO com divisores.

| Frequência (GHz) | Ganho realizado total (dBi) | Horizontal (°) | Vertical (°) |
|---:|---:|---:|---:|
{table}

![Ganho e aberturas nos 17 pontos](ganho_aberturas_17pontos.png)

O centro convergiu em **{conv['passes']} passes**, ΔS final **{conv['delta_s']:.6g}**, com **{conv['consecutivos']} passes consecutivos** dentro de 0,04. A auditoria da nova malha encontrou **{data['malha_major']} reparos graves** e **{data['malha_minor']} reparos menores**. Os campos amostrados por passe e seus deltas estão em [histórico](hfss/historico_centro.json).

A matriz S64 tem valor singular máximo {data['max_valor_singular']:.8g} e erro máximo de reciprocidade {data['erro_reciprocidade']:.3g}. A potência aceita obtida da matriz foi conferida contra a relação entre ganho realizado e ganho referido à potência aceita, em todas as frequências.

[Tabela completa, potências e apontamento](resultados_banda.csv) · [Auditoria da banda](hfss/auditoria_banda.json) · [Matriz S64](hfss/banda.s64p) · [Projeto HFSS](hfss/{cfg['native']})
'''
(dest/'README.md').write_text(head+summary,encoding='utf8')
(root/'relatorio_resultados.md').write_text(head+summary,encoding='utf8')
(dest/'manifesto.json').write_text(json.dumps(dict(estado='AUDITADO_NUMERICAMENTE_REVISAO_VISUAL_PENDENTE',arquivos=items),ensure_ascii=False,indent=2),encoding='utf8')
print('PACOTE',len(items),'arquivos',sum(i['bytes'] for i in items),'bytes; revisar grafico antes de liberar.')
