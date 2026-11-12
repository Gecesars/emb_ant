"""Usar novo S6/ campos da antena e o S8 C02 preservado, sem extrapolacao."""
from pathlib import Path
import os,json,hashlib
HERE=Path(__file__).parent;root=Path(os.environ['P2S13_R16_CASE']);cfg=json.loads((root/'configuracao.json').read_text())
div=Path(cfg['divisor_reutilizado'])
for n,digest in cfg['fontes_divisor_sha256'].items():assert hashlib.sha256((div/n).read_bytes()).hexdigest()==digest
src=HERE/'r14_circuito.py';code=src.read_text(encoding='utf-8-sig')
code=code.replace("ROOT=Path('D:/dev/EMBRAER/P2S13/R14_Compacto_Simetrico_SemRadome/c00')",'ROOT=Path(os.environ["P2S13_R16_CASE"])')
code=code.replace("DIV=ROOT/'divisor'",'DIV=Path('+repr(str(div))+')')
code=code.replace("revisao='R14_C09_sem_radome'","revisao=cfg['revisao']")
code=code.replace('antena sem radome','refletor plano 90 mm com PVC').replace('sem radome e sem conectores N.','PVC nominal aberto; sem flanges, novos suportes e conectores N.')
exec(compile(code,str(src),'exec'),dict(__file__=str(src),__name__='__main__',os=os))
