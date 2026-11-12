"""Sintonia local para a carga com PVC; estimativa, nao substitui novo HFSS."""
from pathlib import Path
import os,sys,types
HERE=Path(__file__).parent
BASE=Path('D:/dev/EMBRAER/P2S13/R16_Tubo_PVC/dn100')
ANCHOR=Path(os.environ.get('P2S13_R16_ANCHOR',str(BASE)))
OUT=Path(os.environ.get('P2S13_R16_GUIDE',str(BASE.parent/'guia_dn100_c01')))
os.environ['P2S13_MODEL_DEST']=str(OUT)
os.environ['P2S13_R15_ANCHOR']=str(ANCHOR)
p=HERE/'r15_guia.py';s=p.read_text()
s=s.replace("BASE=Path('D:/dev/EMBRAER/P2S13/R14_Compacto_Simetrico_SemRadome/c00')",'BASE=Path('+repr(str(BASE))+')')
s=s.replace("ROOT=Path('D:/dev/EMBRAER/P2S13/R15_Casamento_C09')",'ROOT=Path('+repr(str(OUT))+')')
m=types.ModuleType('r15_guia');m.__file__=str(p);sys.modules['r15_guia']=m
exec(compile(s,str(p),'exec'),m.__dict__)
p=HERE/'r15_modelo.py';s=p.read_text()
s=s.replace("residual=sd0-dual(one(x0,p)) if ANCHOR!=BASE else np.zeros((8,8),complex)","residual=sd0-dual(one(x0,p))")
s=s.replace("bounds=[(.35,1.5),(1.2,4.5),(6.8,12.5)] if ANCHOR==BASE else [(x0[0]*.85,x0[0]*1.15),(x0[1]*.85,x0[1]*1.15),(x0[2]-.4,x0[2]+.4)]", "bounds=[(.6,1.6),(1.3,4.5),(7.0,12.0)]")
if ANCHOR!=BASE:s=s.replace("bounds=[(.6,1.6),(1.3,4.5),(7.0,12.0)]", "bounds=[(max(.35,x0[0]*.75),x0[0]*1.25),(x0[1]*.75,x0[1]*1.25),(x0[2]-.6,x0[2]+.6)]")
s=s.replace("cost=300*np.sum(np.maximum(np.r_[ga,gm]-.07,0)**2)+np.sum(ga**2+gm**2)","cost=300*max(ga)**2+np.sum(ga**2)+.05*np.sum(gm**2)")
s=s.replace("residuo_S8_local_preservado=ANCHOR!=BASE","residuo_S8_local_preservado=True")
exec(compile(s,str(p),'exec'),dict(__file__=str(p),__name__='__main__'))
