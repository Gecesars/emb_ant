"""Novo divisor para o S6 com PVC, preservando antena, tubo, cabos e terminais."""
from pathlib import Path
import os,json,hashlib
HERE=Path(__file__).parent;ROOT=Path('D:/dev/EMBRAER/P2S13/R16_Tubo_PVC')
BASE=ROOT/'dn100';CASE=Path(os.environ.get('P2S13_R16_CASE',str(ROOT/'dn100_c01')))
os.environ['P2S13_R15_CASE']=str(CASE);os.environ['P2S13_MODEL_DEST']=str(ROOT/('guia_'+CASE.name))
assert not CASE.exists()
p=HERE/'r15_preparar.py';exec(compile(p.read_text(),str(p),'exec'),dict(__file__=str(p),__name__='__main__'))
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
c=read(BASE/'configuracao.json');c.update(revisao='R16_PVC_'+CASE.name.upper(),antena_reutilizada=str(BASE/'antena'),
    fontes_antena_sha256={n:hashlib.sha256((BASE/'antena'/n).read_bytes()).hexdigest() for n in ['PCB_Tubo_DN100.aedt','centro.s6p','configuracao.json']})
c['modelos_RF_ativos']['divisor']='divisor/Divisor_Duplo3.aedt'
c['modelos_RF_ativos']['antena']=str(BASE/'antena/PCB_Tubo_DN100.aedt')
save(CASE/'configuracao.json',c)
d=read(CASE/'divisor/configuracao.json');d.update(radome=c['radome'],radome_presente=True,bloco='divisor',
    pipe_center_z_local_mm=c['divisor_translacao_z_mm']-c['radome']['centro_z_mm'])
save(CASE/'divisor/configuracao.json',d)
