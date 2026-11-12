"""Arquivar apenas nativos e evidencias compactas do ensaio PVC."""
from pathlib import Path
import json,hashlib,shutil,zipfile
ROOT=Path('D:/dev/EMBRAER/P2S13/R16_Tubo_PVC');CASE=ROOT/'dn100'
OUT=Path('D:/dev/EMBRAER/emb_ant/projetos/P2S13/tubo_pvc')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
r=read(CASE/'circuito/resultado.json');assert not r['nexxim_pendente']
assert read(CASE/'circuito/verificacao_nexxim.json')['matriz_conferida']
assert r['potencia']['balanco_aprovado']
entries=[]
def cp(src,rel):
    assert src.is_file(),src
    assert not any(x in str(rel).lower() for x in ['.aedtresults','.g3derr','.lock','__pycache__'])
    dst=OUT/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    sha=hashlib.sha256(src.read_bytes()).hexdigest();assert hashlib.sha256(dst.read_bytes()).hexdigest()==sha
    entries.append(dict(arquivo=str(rel).replace('\\','/'),origem=str(src),bytes=dst.stat().st_size,sha256=sha))
def group(base,rel,files):
    for n in files:cp(base/n,Path(rel)/n)
group(ROOT,Path('.'),['README.md','envelopes_montagem.json','encaixe_preliminar.json','explicacao_VSWR_c09.json','comparacao_encaixe.png'])
group(CASE,Path('dn100'),['configuracao.json','pipeline.json'])
for block,native,net in [('antena','PCB_Tubo_DN100.aedt','centro.s6p'),('divisor','Divisor_Tubo_DN100.aedt','divisor.s8p')]:
    base=CASE/block;rel=Path('dn100')/block
    group(base,rel,[native,net,'configuracao.json','HFSS_14nucleos.acf','tubo_criado.json','auditoria_em.json',
        'convergencia.txt','convergencia_metadados.txt','perfil_recursos.txt','mensagens.json'])
    if block=='antena':
        group(base,rel,['historico_campos.json','potencia.json','ordem_fontes.json'])
        files=list(base.glob('*.csv'));assert len(files)==27
        for p in sorted(files):cp(p,rel/p.name)
base=CASE/'circuito';rel=Path('dn100/circuito')
group(base,rel,['C09_PVC_Nexxim.aedt','C09_PVC_Nexxim_sem_malhas.aedtz','resultado.json','verificacao_nexxim.json',
    'antena.s6p','divisor.s8p','coaxial.s2p','conjunto.s2p','nexxim.s2p','ondas.npz','polar_HV.png','diagrama_H.csv','diagrama_V.csv','diagrama_V_fino.csv'])
with zipfile.ZipFile(base/'C09_PVC_Nexxim_sem_malhas.aedtz') as z:
    assert not any('.aedtresults' in n.lower() or '.lock' in n.lower() or '.mesh' in n.lower() for n in z.namelist())
group(CASE/'visual',Path('dn100/visual'),['Antena_PVC_DN100_PRELIMINAR.FCStd','auditoria_cad.json','montagem_tubo_transparente.png'])
for ADJ in sorted(ROOT.glob('dn100_c*')):
    rel=Path(ADJ.name);ar=read(ADJ/'circuito/resultado.json')
    assert not ar['nexxim_pendente'] and ar['potencia']['balanco_aprovado']
    assert read(ADJ/'circuito/verificacao_nexxim.json')['matriz_conferida']
    group(ADJ,rel,['configuracao.json','alteracoes.json','pipeline.json'])
    group(ADJ/'divisor',rel/'divisor',['Divisor_Duplo3.aedt','Divisor_Duplo3.FCStd','configuracao.json','igualdade_ramais.json',
        'HFSS_14nucleos.acf','tubo_criado.json','geometria_importada.json','hfss_validacao.json','divisor.s8p','auditoria_em.json',
        'convergencia.txt','convergencia_metadados.txt','perfil_recursos.txt','mensagens.json'])
    for p in sorted((ADJ/'divisor/cad').glob('*')):
        if p.suffix in ('.json','.step'):cp(p,rel/'divisor/cad'/p.name)
    files=['C09_PVC_Nexxim.aedt','C09_PVC_Nexxim_sem_malhas.aedtz','resultado.json','verificacao_nexxim.json',
        'antena.s6p','divisor.s8p','coaxial.s2p','conjunto.s2p','nexxim.s2p','ondas.npz','polar_HV.png','diagrama_H.csv','diagrama_V.csv','diagrama_V_fino.csv']
    group(ADJ/'circuito',rel/'circuito',files)
    with zipfile.ZipFile(ADJ/'circuito/C09_PVC_Nexxim_sem_malhas.aedtz') as z:
        assert not any('.aedtresults' in n.lower() or '.lock' in n.lower() or '.mesh' in n.lower() for n in z.namelist())
    group(ADJ/'visual',rel/'visual',['Antena_PVC_'+ADJ.name.upper()+'_PRELIMINAR.FCStd','auditoria_cad.json'])
    if (ADJ/'visual/montagem_tubo_ajustada.png').exists():cp(ADJ/'visual/montagem_tubo_ajustada.png',rel/'visual/montagem_tubo_ajustada.png')
    guide=ROOT/('guia_'+ADJ.name)
    for p in sorted(guide.glob('*.json')):cp(p,Path(guide.name)/p.name)
if (ROOT/'estado_final.json').exists():cp(ROOT/'estado_final.json',Path('estado_final.json'))
(OUT/'manifesto.json').write_text(json.dumps(dict(arquivos=entries,material_comercial_validado=False,sem_malhas=True),indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(dict(arquivos=len(entries),bytes=sum(x['bytes'] for x in entries))))
