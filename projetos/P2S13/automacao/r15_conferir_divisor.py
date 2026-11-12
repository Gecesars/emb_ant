"""Conferir que somente duas folhas de sinal mudaram e registrar envelopes exatos."""
import FreeCAD as A,json,os
from pathlib import Path
BASE=Path('D:/dev/EMBRAER/P2S13/R14_Compacto_Simetrico_SemRadome/c00/divisor')
ROOT=Path(os.environ['P2S13_DIV3_ROOT'])
a=A.openDocument(str(BASE/'Divisor_Duplo3.FCStd'));b=A.openDocument(str(ROOT/'Divisor_Duplo3.FCStd'))
man=json.loads((ROOT/'cad/manifesto.json').read_text());changed=[];geometry={}
for name in man:
    sh=a.getObject(name).Shape;t=b.getObject(name).Shape
    if sh.cut(t).Volume+t.cut(sh).Volume>1e-7:changed.append(name)
    bb=t.optimalBoundingBox(False,False)
    geometry[name]=dict(volume_mm3=t.Volume,bbox_mm=[getattr(bb,k) for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax']])
assert set(changed)=={'Sinal_A','Sinal_B'}
(ROOT/'cad/geometria_esperada.json').write_text(json.dumps(geometry,indent=2))
(ROOT/'cad/conferencia_alteracoes.json').write_text(json.dumps(dict(objetos=52,alterados=changed,inalterados=50,portas_fixas=True),indent=2))
A.closeDocument(a.Name);A.closeDocument(b.Name);print('CONFERENCIA_CAD_OK')
