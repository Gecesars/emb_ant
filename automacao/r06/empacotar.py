"""Copiar apenas nativos e evidencias necessarias para a entrega R06, sem malhas."""
import argparse,hashlib,json,shutil
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path)
args=parser.parse_args();root=args.root;repo=Path(__file__).resolve().parents[2]
dest=repo/'resultados/r06';records=[]
def load(path):return json.loads(path.read_text(encoding='utf8'))
assert load(root/'circuito/resultado.json')['corrigida']['criterios_numericos_atendidos']
assert load(root/'antena/auditoria_convergencia.json')['convergencia_aprovada']
assert load(root/'circuito/comparacao_malhas.json')['estabilidade_local_aprovada']
assert load(root/'circuito/verificacao_nexxim.json')['matriz_s_independente_conferida']
assert (root/'relatorio/P1H_R06_Relatorio.pdf').is_file()

def copy(source,target):
    assert source.is_file(),source
    assert source.suffix.lower() not in ('.g3derr','.mesh','.field','.fld','.profile','.log')
    assert not any(p.endswith('.aedtresults') for p in source.parts),source
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)
    a=hashlib.sha256(source.read_bytes()).hexdigest();b=hashlib.sha256(target.read_bytes()).hexdigest()
    assert a==b
    records.append(dict(fonte=str(source),arquivo=target.relative_to(repo).as_posix(),sha256=a,bytes=target.stat().st_size))

copy(root/'antena/PCB_R06.aedt',repo/'hfss/antenas/P1H_R06_PCB.aedt')
for side in ['inferior','superior']:
    folder=root/('divisor_'+side)
    copy(folder/('Divisor_'+side+'.aedt'),repo/'hfss/alimentacao/r06'/('Divisor_'+side+'.aedt'))
copy(root/'circuito/P1H_R06_Circuito_sem_malhas.aedtz',repo/'hfss/circuito/R06/P1H_R06_Circuito_sem_malhas.aedtz')
copy(root/'configuracao_circuito.json',dest/'configuracao_circuito.json')
metrics=load(root/'circuito/resultado.json')['corrigida']
mechanics=load(root/'mecanica/rastreabilidade.json')
assert metrics['comprimentos_fisicos_mm']==mechanics['comprimentos_mm']
for source in sorted((root/'mecanica').iterdir()):
    if source.is_file() and source.suffix.lower() in ['.fcstd','.step','.dxf','.pdf','.json','.csv','.png','.md']:
        copy(source,repo/'freecad/mecanica_R06'/source.name)
for folder,native in [('antena','PCB_R06.FCStd'),('divisor_inferior','Divisor_Inferior.FCStd'),('divisor_superior','Divisor_Superior.FCStd')]:
    copy(root/folder/native,repo/'freecad/modelos_RF_R06'/folder/native)
    for source in sorted((root/folder/'cad').iterdir()):
        if source.suffix in ['.step','.json']:copy(source,repo/'freecad/modelos_RF_R06'/folder/'cad'/source.name)
for folder in ['antena','antena_malha_inicial']:
    for name in ['antena.s20p','Centro_H.csv','Centro_V.csv','convergencia.txt','auditoria_convergencia.json','malha.json']:
        copy(root/folder/name,dest/folder/name)
    patterns=sorted((root/folder/'padroes').glob('*.csv'));assert len(patterns)==40
    for source in patterns:copy(source,dest/folder/'padroes'/source.name)
for side,count in [('inferior',18),('superior',12)]:
    folder='divisor_'+side
    for name in ['divisor.s%dp'%count,'convergencia.txt','malha.json']:
        copy(root/folder/name,dest/folder/name)
for source in sorted((root/'circuito').iterdir()):
    if source.is_file() and source.suffix in ['.json','.csv','.s2p','.npz']:
        copy(source,dest/'circuito'/source.name)
for source in sorted((root/'circuito/componentes').iterdir()):
    if source.is_file() and (source.suffix=='.json' or source.suffix.startswith('.s')):
        copy(source,dest/'circuito/componentes'/source.name)
old=root.parent/'R05_Correcao/cupons'
for name in ['Bobina_r090','Controle_fechado']:
    for file in ['cupom.s2p','convergencia.txt']:
        copy(old/name/file,dest/'cupons'/name/file)
copy(old/'Controle_fechado/Controle_fechado.aedt',repo/'hfss/alimentacao/r06/Controle_acessos_bobina.aedt')
for folder,suffixes in [('imagens',['.png','.json']),('cotacao',['.jpg','.txt']),('fabricacao',['.json'])]:
    for source in sorted((root/folder).iterdir()):
        if source.is_file() and source.suffix in suffixes:copy(source,dest/folder/source.name)
copy(root/'relatorio/P1H_R06_Relatorio.pdf',dest/'P1H_R06_Relatorio.pdf')
manifest=dict(estado='qualificacao_numerica_em_5.17GHz',sem_malhas=True,artefatos=records)
(dest/'manifesto_entrega.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print('PACOTE_CONFERIDO',len(records),'arquivos',sum(r['bytes'] for r in records),'bytes')
