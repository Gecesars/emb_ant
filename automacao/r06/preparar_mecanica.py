"""Preparar a montagem R06 selecionada, preservando o historico R05."""
import argparse,csv,hashlib,json,shutil
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path)
root=parser.parse_args().root;repo=Path(__file__).resolve().parents[2]
config=json.loads((root/'configuracao_circuito.json').read_text(encoding='utf8'))
native=Path(config['geometria']);candidate=native.parent.parent
verification=json.loads(Path(config['verificacao']).read_text(encoding='utf8'))
images=json.loads((root/'imagens/manifesto_montagem.json').read_text(encoding='utf8'))
assert images['sha256']==hashlib.sha256(native.read_bytes()).hexdigest()
assert not verification['interferencias_mm3']
assert max(r['diferenca_simetrica_mm3'] for r in images['comparacao_fora_do_chicote'])<1e-6
out=root/'mecanica';out.mkdir(exist_ok=True)
sources=[]
def copy(source,name):
    target=out/name;shutil.copy2(source,target)
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    assert sha==hashlib.sha256(target.read_bytes()).hexdigest()
    sources.append(dict(fonte=str(source),arquivo=name,sha256=sha))

copy(native,'P1H_R06_compacta.FCStd')
for name in ['01_Refletor_dobrado.FCStd','01_Refletor_dobrado.step','02_Refletor_planificado.FCStd',
             '04_Refletor_CORTE_1a1.dxf','05_Refletor_marcacao_dobras.dxf','verificacao_chapa.json']:
    copy(repo/'freecad/mecanica_R05'/name,name)
for name in ['caminhos.json','enlaces.json','chicote_ajustado.json']:
    copy(candidate/'compacta'/name,name)
copy(Path(config['verificacao']),'verificacao_cad.json')
copy(root/'imagens/manifesto_montagem.json','comparacao_geometria.json')
copy(root/'imagens/montagem_frontal.png','frente.png')
copy(root/'imagens/montagem_traseira.png','traseira.png')

# A conectividade permanece igual; comprimentos e envelopes vem do CAD novo.
bounds=json.loads((root/'imagens/envelopes_cabos.json').read_text(encoding='utf8'))
with (repo/'freecad/mecanica_R05/chicote_26_cabos.csv').open(encoding='utf8',newline='') as f:
    rows=list(csv.DictReader(f))
for row in rows:
    name=row['cabo'];length=verification['comprimentos_mm'][name]
    expected=config['comprimentos_mm'][0 if name.startswith('IN_') else 1 if name.startswith('TR_') else 2]
    assert abs(length-expected)<1e-8
    row['eixo_entre_interfaces_mm']='%.6f'%length
    row['menor_Z_externo_mm']='%.6f'%bounds[name]
with (out/'chicote_26_cabos.csv').open('w',encoding='utf8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
record=dict(estado='Geometria verificada; RF refinado pendente',comprimentos_mm=config['comprimentos_mm'],
            total_coax_mm=sum(verification['comprimentos_mm'].values()),
            percurso_por_radiador_mm=sum(config['comprimentos_mm']),
            folga_minima_mm=verification['folga_minima_entre_capas_mm'],
            envelope_zmin_mm=min(bounds.values()),fontes=sources)
(out/'rastreabilidade.json').write_text(json.dumps(record,indent=2),encoding='utf8')
print('MECANICA_R06_PREPARADA',record['total_coax_mm'],record['folga_minima_mm'])
