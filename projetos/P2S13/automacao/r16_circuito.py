"""Conectar no circuito os dois blocos novamente resolvidos com PVC."""
from pathlib import Path
import os,json
HERE=Path(__file__).parent;root=Path(os.environ['P2S13_R16_CASE']);src=HERE/'r14_circuito.py'
code=src.read_text(encoding='utf-8-sig')
code=code.replace("ROOT=Path('D:/dev/EMBRAER/P2S13/R14_Compacto_Simetrico_SemRadome/c00')",'ROOT=Path(os.environ["P2S13_R16_CASE"])')
cfg=json.loads((root/'configuracao.json').read_text())
if cfg.get('antena_reutilizada'):
    import hashlib
    ant=Path(cfg['antena_reutilizada'])
    for name,digest in cfg['fontes_antena_sha256'].items():
        assert hashlib.sha256((ant/name).read_bytes()).hexdigest()==digest
    code=code.replace("ANT=ROOT/'antena'","ANT=Path("+repr(str(ant))+")")
code=code.replace("revisao='R14_C09_sem_radome'","revisao=cfg['revisao']")
code=code.replace('C09 compacto —','C09 '+root.name+' —')
code=code.replace('antena sem radome','antena com tubo PVC nominal')
code=code.replace('sem radome e sem conectores N.','PVC nominal nos dois blocos; tubo aberto, sem tampas, bolsas ou conectores N. Propriedades PVC nao medidas no tubo comercial.')
exec(compile(code,str(src),'exec'),dict(__file__=str(src),__name__='__main__',os=os))
p=root/'circuito/resultado.json';r=json.loads(p.read_text());cfg=json.loads((root/'configuracao.json').read_text())
r['tubo']=cfg['radome'];r['abertura_apenas_informativa']=True
r['material_comercial_validado']=False
if cfg.get('antena_reutilizada'):r['antena_reutilizada']=dict(pasta=cfg['antena_reutilizada'],sha256=cfg['fontes_antena_sha256'],sem_novo_solve=True)
p.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
