"""Gera pacote de fabricacao, rastreabilidade e aceite atual sem alterar a fonte RF."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json

REPO=Path(__file__).resolve().parents[3]
OUT=REPO/'projetos/P2M21/kicad/4_elementos'
SOURCE=REPO/'projetos/P2M21/quatro_elementos_casamento_banda/c12_raiz_intermediaria'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

native=read(OUT/'verificacao.json'); cam=read(OUT/'verificacao_gerbers.json')
assert native['aprovado_geometria'] and cam['aprovado']
assert native['drc_erros']==0 and native['drc_desconectados']==0
for name,value in cam['hashes'].items():assert sha(OUT/'gerbers'/name)==value,name
assert sha(OUT/'4_elementos.kicad_pcb')==read(OUT/'leitura_kicad.json')['native_sha256']
r=read(SOURCE/'resultado.json')
b=read(SOURCE/'banda_auditada.json')
save(OUT/'aceite_atual.json',dict(data='2026-11-10',fonte='C12 R13 preservada; nao houve novo solve',
    instrucao_usuario='Ate +/-0,5 graus nos dois cortes',tolerancia_apontamento_graus=.5,
    cortes={axis:dict(pico_graus=c['pico_graus'],atende=abs(c['pico_graus'])<=.5) for axis,c in r['cortes'].items()},
    VSWR_meta=1.25,VSWR_banda_atende=b['todos_VSWR_ate_meta'],
    conjunto_RF_aprovado=False,motivo='Maximo horizontal +0,75 graus excede +/-0,5 graus',
    conversao_geometrica_aprovada=True))
files=[OUT/'gerbers'/('4_elementos-'+s) for s in ['F_Cu.gtl','B_Cu.gbl','F_Mask.gts','B_Mask.gbs','Edge_Cuts.gm1','PTH.drl','NPTH.drl']]
files.append(OUT/'FABRICACAO_JLCPCB.txt')
zip_path=OUT/'4_elementos_gerbers_JLCPCB.zip'
with ZipFile(zip_path,'w',ZIP_DEFLATED) as z:
    for p in files:z.write(p,p.name)
with ZipFile(zip_path) as z:
    assert z.testzip() is None and len(z.namelist())==8
    for p in files:assert hashlib.sha256(z.read(p.name)).hexdigest()==sha(p)
sources=['geometria.json','criar_cad.py','4_elementos.FCStd','P2M21_4_elementos.aedt',
         'cad/reabertura.json','cad/intersecoes.json','cad/enig_hfss.json',
         'resultado.json','banda_auditada.json','pico_auditado.json','dimensoes_transformadores.json']
artifacts=[p for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='manifesto.json' and p.suffix not in ('.kicad_prl','.lock')]
manifest=dict(revisao='4_elementos R01 / HFSS R13 C12',data='2026-11-10',
    fonte=str(SOURCE.relative_to(REPO)).replace('\\','/'),
    fontes=[dict(arquivo=s,sha256=sha(SOURCE/s)) for s in sources],
    pacote_zip=zip_path.name,pacote_sha256=sha(zip_path),
    arquivo_job_somente_evidencia=True,
    arquivos=[dict(arquivo=str(p.relative_to(OUT)).replace('\\','/'),bytes=p.stat().st_size,sha256=sha(p)) for p in artifacts])
save(OUT/'manifesto.json',manifest)
print(json.dumps(dict(pacote=str(zip_path),arquivos_zip=len(files),sha256=sha(zip_path),artefatos=len(artifacts)),indent=2))
