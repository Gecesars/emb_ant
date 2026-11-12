"""Pacote seletivo R15: nenhuma malha, campo volumetrico ou lock."""
from pathlib import Path
import hashlib,json,os,shutil,zipfile
ROOT=Path('D:/dev/EMBRAER/P2S13/R15_Casamento_C09')
REPO=Path('D:/dev/EMBRAER/emb_ant')
OUT=REPO/'projetos/P2S13/casamento_c09'
CASE=Path(os.environ['P2S13_R15_CASE'])
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
res=read(CASE/'circuito/resultado.json')
assert res['casamento_confirmado_HFSS_Nexxim'] and not res['nexxim_pendente']
assert max(res['VSWR_ativo'])<=1.25
assert res['convergencia']['divisor']['passes']<=6
assert (ROOT/'README.md').exists() and (CASE/'visual/conferencia_montagem.json').exists()
manifest=[]
def cp(src,rel):
    assert src.is_file(),src
    assert not any(t in str(rel).lower() for t in ['.aedtresults','.g3derr','.lock','__pycache__'])
    dst=OUT/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    a=hashlib.sha256(src.read_bytes()).hexdigest();b=hashlib.sha256(dst.read_bytes()).hexdigest();assert a==b
    manifest.append(dict(arquivo=str(rel).replace('\\','/'),origem=str(src),bytes=dst.stat().st_size,sha256=a))
def group(base,rel,names):
    for n in names:cp(base/n,Path(rel)/n)
group(ROOT,Path('.'),['README.md','selecionado.json','layout_comparado.png','comparacao_VSWR.png'])
cases=list(dict.fromkeys(['c01',CASE.name]))
for case in cases:
    base=ROOT/case
    group(base,Path(case),['configuracao.json','alteracoes.json','HFSS_14nucleos.acf','pipeline.json'])
    group(base/'divisor',Path(case)/'divisor',[
        'Divisor_Duplo3.aedt','Divisor_Duplo3.FCStd','configuracao.json','divisor.s8p',
        'auditoria_em.json','convergencia.txt','convergencia_metadados.txt','perfil_recursos.txt',
        'geometria_importada.json','hfss_validacao.json','igualdade_ramais.json','mensagens.json'])
    for src in sorted((base/'divisor/cad').iterdir()):
        if src.suffix.lower() in ('.json','.step'):cp(src,Path(case)/'divisor/cad'/src.name)
    group(base/'circuito',Path(case)/'circuito',[
        'C09_Ajuste_Nexxim.aedt','C09_Ajuste_Nexxim_sem_malhas.aedtz',
        'antena.s6p','divisor.s8p','coaxial.s2p','conjunto.s2p','nexxim.s2p',
        'resultado.json','verificacao_nexxim.json','diagrama_H.csv','diagrama_V.csv',
        'diagrama_V_fino.csv','ondas.npz','polar_HV.png'])
    with zipfile.ZipFile(base/'circuito/C09_Ajuste_Nexxim_sem_malhas.aedtz') as z:
        assert not any('.aedtresults' in n.lower() or '.lock' in n.lower() or 'mesh' in n.lower() for n in z.namelist()),z.namelist()
    if case==CASE.name:
        group(base/'visual',Path(case)/'visual',['Antena_C09_Ajustada_PRELIMINAR.FCStd','conferencia_montagem.json'])
        for src in sorted((base/'visual').glob('*.png')):cp(src,Path(case)/'visual'/src.name)
for name,base in [('guia_c01',ROOT),('guia_c02',ROOT/'guia_c02')]:
    group(base,Path('guias')/name,['guia_passiva.json'])
    group(base/'guia_nexxim',Path('guias')/name/ 'nexxim',[
        'C09_Ajuste_Nexxim.aedt','C09_Ajuste_Nexxim_sem_malhas.aedtz',
        'antena.s6p','divisor.s8p','coaxial.s2p','conjunto.s2p','nexxim.s2p','verificacao_nexxim.json'])
(OUT/'manifesto.json').write_text(json.dumps(dict(versao_selecionada=CASE.name,arquivos=manifest,
    antena_preservada=res['antena_reutilizada'],sem_malhas=True),indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(dict(destino=str(OUT),arquivos=len(manifest),bytes=sum(x['bytes'] for x in manifest))))
