"""Pacote R17 auditavel, sem malhas/resultados volumetricos/locks."""
from pathlib import Path
import json,shutil,hashlib,zipfile
ROOT=Path('D:/dev/EMBRAER/P2S13/R17_Flanges_Refletor');REPO=Path('D:/dev/EMBRAER/emb_ant')
DEST=REPO/'projetos/P2S13/mecanica_R17';RF=REPO/'projetos/P2S13/comparacao_refletor_R17'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
assert read(ROOT/'plano90/pipeline.json')['estado']=='CONCLUIDO_REVISAR'
assert read(ROOT/'documentacao/revisao_visual.json')['aprovado']
mech=read(ROOT/'mecanica/verificacao_cad.json');assert mech['validos'] and not mech['intersecoes']
assert all(x['distancia_mm']<1e-6 for x in read(ROOT/'mecanica/verificacao_interfaces.json')['contatos'])
rf=read(ROOT/'plano90/antena/auditoria_em.json');assert rf['passes']==6 and rf['fisicamente_consistente'] and rf['malha']['reparos_major']==0
assert read(ROOT/'plano90/circuito/verificacao_nexxim.json')['matriz_conferida']
manifest=[]
def cp(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    sha=hashlib.sha256(src.read_bytes()).hexdigest();assert hashlib.sha256(dst.read_bytes()).hexdigest()==sha
    manifest.append(dict(arquivo=str(dst.relative_to(REPO)).replace('\\','/'),origem=str(src),bytes=src.stat().st_size,sha256=sha))
for f in (ROOT/'mecanica').iterdir():
    if f.is_file() and f.suffix.lower() in ['.fcstd','.step','.json']:cp(f,DEST/f.name)
for f in (ROOT/'mecanica/imagens').glob('*.png'):cp(f,DEST/'imagens'/f.name)
for f in (ROOT/'documentacao').iterdir():
    if f.is_file() and f.suffix.lower() in ['.pdf','.dxf','.csv','.png','.json']:cp(f,DEST/'documentacao'/f.name)
cp(ROOT/'alternativa_plana/mecanica/Refletor_Al2mm.step',DEST/'alternativa_plana/Refletor_plano_alternativo.step')
for folder in ['antena','circuito']:
    for f in (ROOT/'plano90'/folder).iterdir():
        if f.is_file() and f.suffix.lower() in ['.aedt','.aedtz','.json','.txt','.csv','.png','.npz','.s6p','.s8p','.s2p','.acf']:
            cp(f,RF/'plano90'/folder/f.name)
for name in ['configuracao.json','pipeline.json']:
    cp(ROOT/'plano90'/name,RF/'plano90'/name)
cp(ROOT/'decisao_refletor.txt',RF/'decisao_refletor.txt')
old=Path('D:/dev/EMBRAER/P2S13/R16_Tubo_PVC/dn100_c02/circuito')
for name in ['resultado.json','diagrama_H.csv','diagrama_V.csv','verificacao_nexxim.json']:cp(old/name,RF/'referencia_dobrada_R16'/name)
for f in [REPO/'projetos/P2M21/mecanica_preliminar_R18/referencias/82-6784.stp']:cp(f,DEST/'referencias'/f.name)
# ZIP de entrega mecanica; o manifesto externo valida todos os bytes copiados.
zip_path=ROOT/'documentacao/P2S13_R17_Mecanica_PRELIMINAR.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    if (DEST/'README.md').exists():z.write(DEST/'README.md','README.md')
    for item in manifest:
        f=REPO/item['arquivo']
        if f.is_relative_to(DEST):z.write(f,f.relative_to(DEST))
cp(zip_path,DEST/'P2S13_R17_Mecanica_PRELIMINAR.zip')
assert not any(any(s in x['arquivo'].lower() for s in ['.aedtresults','.g3derr','.lock']) for x in manifest)
(DEST/'manifesto_arquivos.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('R17_PACOTE',len(manifest),'arquivos',sum(x['bytes'] for x in manifest),'bytes')
