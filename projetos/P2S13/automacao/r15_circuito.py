"""Reutilizar exclusivamente a antena intacta; auditar novo divisor e recombinar."""
from pathlib import Path
import os,json,hashlib
HERE=Path(__file__).parent;root=Path(os.environ['P2S13_R15_CASE'])
src=HERE/'r14_circuito.py';code=src.read_text(encoding='utf-8-sig')
old="ROOT=Path('D:/dev/EMBRAER/P2S13/R14_Compacto_Simetrico_SemRadome/c00');ANT=ROOT/'antena';DIV=ROOT/'divisor';OUT=ROOT/'circuito';OUT.mkdir(exist_ok=True)"
new="ROOT=Path(os.environ['P2S13_R15_CASE']);ANT=Path(read(ROOT/'configuracao.json')['antena_reutilizada']);DIV=ROOT/'divisor';OUT=ROOT/'circuito';OUT.mkdir(exist_ok=True)"
assert code.count(old)==1;code=code.replace(old,new)
old="cfg=read(ROOT/'configuracao.json');aa,an=run(ANT,'centro.s6p');da,dn=run(DIV,'divisor.s8p')"
new="""cfg=read(ROOT/'configuracao.json');aa=read(ANT/'auditoria_em.json');an=rf.Network(str(ANT/'centro.s6p'));da,dn=run(DIV,'divisor.s8p')
for file,digest in cfg['fontes_antena_sha256'].items():
    assert hashlib.sha256((ANT/file).read_bytes()).hexdigest()==digest
    assert aa['fontes_sha256'][file]==digest
"""
assert code.count(old)==1;code=code.replace(old,new).replace("revisao='R14_C09_sem_radome'","revisao=cfg['revisao']")
exec(compile(code,str(src),'exec'),dict(__file__=str(src),__name__='__main__',os=os))
p=root/'circuito/resultado.json';r=json.loads(p.read_text());cfg=json.loads((root/'configuracao.json').read_text())
r['antena_reutilizada']=dict(pasta=cfg['antena_reutilizada'],sha256=cfg['fontes_antena_sha256'],sem_novo_solve=True)
p.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
