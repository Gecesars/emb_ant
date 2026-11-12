"""Nexxim com S6/S8 do novo tubo: nenhuma extrapolacao do caso sem PVC."""
from pathlib import Path
import os,json
root=Path(os.environ['P2S13_R16_CASE']);os.environ['P2S13_R15_CASE']=str(root);os.environ.pop('P2S13_GUIA',None)
p=Path(__file__).with_name('r15_nexxim.py');code=p.read_text()
code=code.replace('C09_Ajuste_Nexxim','C09_PVC_Nexxim').replace('C09_Confirmacao_HFSS','C09_PVC_Confirmacao')
code=code.replace('antena S6 preservada','antena S6 recalculada com tubo PVC').replace('Sem radome;5.17GHz','Tubo PVC nominal;5.17GHz')
code=code.replace("max(vs)<=1.25 and result['convergencia']['divisor']['convergiu']","max(vs)<=1.25 and all(c['convergiu'] for c in result['convergencia'].values())")
exec(compile(code,str(p),'exec'),dict(__file__=str(p),__name__='__main__'))
