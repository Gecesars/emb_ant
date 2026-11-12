"""Arquiva apenas artefatos de engenharia R11 fechados e auditados, sem malhas."""
from pathlib import Path
import json,hashlib,shutil,os,zipfile
ROOT=Path(os.environ['P2S13_ROOT']);BASE=ROOT.parent
REPO=Path(__file__).resolve().parents[3]
DEST=REPO/'projetos/P2S13/fabricavel_radome'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cfg=read(ROOT/'configuracao.json');r=read(ROOT/'resultado.json');div=Path(cfg['fonte_divisor'])
assert read(ROOT/'pipeline.json')['estado']=='CONCLUIDO_AGUARDA_AUDITORIA'
assert not list(ROOT.glob('*.aedt.lock')),'Native ainda aberto'
assert not list(div.glob('*.aedt.lock')),'Divisor ainda aberto'
report=read(ROOT/'relatorio_manifesto.json')
assert report['revisao_visual']=='APROVADA',report
assert report['sha256']==sha(ROOT/'Relatorio_R11_C08_Radome.pdf')
assert report['resultado_sha256']==sha(ROOT/'resultado.json')
assert r['fontes_sha256'][cfg['native']]==sha(ROOT/cfg['native'])
items=[]
def copy(src,rel):
    assert src.is_file(),src
    assert not any(x in src.name.lower() for x in ['.lock','.g3derr','.mesh','.profile','.fcstd1','.fcbak'])
    target=DEST/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
    s=sha(src);assert sha(target)==s
    items.append(dict(origem=str(src),arquivo=str(target.relative_to(REPO)).replace('\\','/'),sha256=s,bytes=target.stat().st_size))
def named(folder,names,relbase):
    for n in names:
        p=folder/n
        if p.exists():copy(p,relbase/n)
for root,rel in [(div,Path(div.name)),(ROOT,Path(ROOT.name))]:
    for p in root.glob('*.aedt'):copy(p,rel/p.name)
    for p in root.glob('*.FCStd'):copy(p,rel/p.name)
    for pattern in ['*.s2p','*.s8p','ALL_*.csv','POL_*.csv','IN_*.csv','diagrama_*.csv']:
        for p in root.glob(pattern):copy(p,rel/p.name)
    named(root,[
       'configuracao.json','HFSS_14nucleos.acf','resultado.json','historico_passes.json','recursos_matriz.json',
       'convergencia.txt','convergencia_campos.json','conferencia_perfil.json','auditoria_solver_matricial.json','malha.json','hfss_validacao.json','geometria_importada.json',
       'potencia.json','potencia_conferida.json','ordem_fontes.json','mensagens.json','pipeline.json','qualificacao.json',
       'polar_HV.png','simetria_vertical.png','Relatorio_R11_C08_Radome.pdf','relatorio_manifesto.json',
       'validacao.json','nominal.json','geometria.json'],rel)
    named(root/'cad',[
       'manifesto.json','folhas_solidas.json','portas.json','conexoes.json','antena_preservada.json','intersecoes.json',
       'reabertura.json','geometria_esperada.json','enig_hfss.json','substrato_coordenadas_globais.json'],rel/'cad')
    if (root/'imagens').is_dir():
        for p in (root/'imagens').glob('*.png'):copy(p,rel/'imagens'/p.name)
named(BASE,['README.md'],Path('.'))
copy(BASE/'fontes/referencia_370HR.json',Path('fontes/referencia_370HR.json'))
k=div/'kicad';kr=Path(div.name)/'kicad'
for pattern in ['*.kicad_pcb','*.kicad_pro']:
    for p in k.glob(pattern):copy(p,kr/p.name)
named(k,['verificacao.json','conferencia_cad_hfss.json','leitura_kicad.json','drc.json','precisao_furacao.json','faces_cad.json'],kr)
for sub,ext in [('gerbers',None),('preview','.png')]:
    for p in (k/sub).iterdir():
        if p.is_file() and (ext is None or p.suffix==ext):copy(p,kr/sub/p.name)
zipname=k/'C08_Gerbers_PARA_REVISAO_RF.zip'
with zipfile.ZipFile(zipname,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted((k/'gerbers').iterdir()):
        if p.is_file():z.write(p,p.name)
    z.writestr('LEIA_ANTES_DE_FABRICAR.txt',
      'C08 — pacote CAM geometricamente conferido.\nO status RF consta no relatorio R11 e nao e comprovado pelo DRC.\n'
      'ZYF300CA-C core1.52mm, Cu35um, ENIG, sem mascara, oitoPTH acabados1.10mm.\n'
      'Nao comprar/fabricar uma revisao reprovada sem nova decisao de engenharia.\n')
copy(zipname,kr/zipname.name)
manifest=dict(estado='QUALIFICADO_NOMINAL' if r['validacao_nominal'] else 'ESTUDO_NAO_QUALIFICADO',
     escopo=cfg['escopo'],resultado_sha256=sha(ROOT/'resultado.json'),artefatos=items,
     exclusoes=['aedtresults','malhas','g3derr','campos volumetricos','locks','tessellacao de visualizacao'])
DEST.mkdir(parents=True,exist_ok=True)
(DEST/'manifesto.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps(dict(destino=str(DEST),arquivos=len(items),bytes=sum(x['bytes'] for x in items),estado=manifest['estado']),indent=2))
