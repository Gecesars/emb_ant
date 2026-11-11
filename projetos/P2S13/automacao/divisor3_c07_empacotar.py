"""ZIP de Gerber/NPTH C07 com DFM pendente explicitamente preservado."""
from pathlib import Path
import json,hashlib,zipfile
R=Path(__file__).resolve().parents[3];O=R/'projetos/P2S13/kicad/divisor_duplo_1x3_C07'
S=R/'projetos/P2S13/divisor_duplo_1x3_correcao/c07_centro';N='divisor_duplo_1x3_C07'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
v=read(O/'verificacao.json');native=read(O/'leitura_kicad.json');cad=read(O/'conferencia_cad_hfss.json')
assert v['conversao_geometrica_aprovada'] and not v['liberado_fabricacao_padrao_JLC']
assert v['DRC_erros']==9 and v['DRC_desconectados']==0 and v['DRC_avisos']==25
assert sha(O/(N+'.kicad_pcb'))==native['native_sha256']
assert cad['fonte_fcstd_sha256']==sha(S/'Divisor_Duplo3.FCStd') and cad['fonte_hfss_sha256']==sha(S/'Divisor_Duplo3.aedt')
for name,digest in v['hashes_CAM'].items():assert sha(O/'gerbers'/name)==digest,name
files=[O/'gerbers'/(N+'-'+s) for s in ['F_Cu.gtl','B_Cu.gbl','F_Mask.gts','B_Mask.gbs','Edge_Cuts.gm1','NPTH.drl','PTH.drl']]
files.append(O/'FABRICACAO_JLCPCB.txt')
zp=O/(N+'_Gerbers_JLCPCB.zip')
with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files:z.write(p,p.name)
with zipfile.ZipFile(zp) as z:
    assert z.testzip() is None and len(z.namelist())==8
    for p in files:assert hashlib.sha256(z.read(p.name)).hexdigest()==sha(p)
allowed={'.kicad_pcb','.kicad_pro','.json','.md','.txt','.csv','.svg','.png','.zip','.gtl','.gbl','.gts','.gbs','.gm1','.drl','.gbrjob'}
artifacts=[p for p in sorted(O.rglob('*')) if p.is_file() and p.name!='manifesto.json' and p.suffix in allowed]
manifest=dict(data='2026-11-11',revisao='C07 / KiCad R01',origem=str(S.relative_to(R)).replace('\\','/'),
    conversao_geometrica_aprovada=True,liberacao_JLC_padrao=False,DRC_erros=9,DRC_avisos=25,
    fontes=[dict(arquivo=n,sha256=sha(S/n)) for n in ['Divisor_Duplo3.aedt','Divisor_Duplo3.FCStd','configuracao.json','resultado.json']],
    pacote=zp.name,sha256_zip=sha(zp),arquivos_zip=8,
    arquivos=[dict(arquivo=str(p.relative_to(O)).replace('\\','/'),bytes=p.stat().st_size,sha256=sha(p)) for p in artifacts])
(O/'manifesto.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(zip=str(zp),sha256=sha(zp),artefatos=len(artifacts),bytes=sum(p.stat().st_size for p in artifacts)),indent=2))
