"""Extrai as faces de cobre do CAD para comparacao planar independente."""
from pathlib import Path
import os,json,hashlib
import FreeCAD as A,Part
S=Path(os.environ['P2S13_DIV3_ROOT']);O=S/'kicad';cfg=json.loads((S/'configuracao.json').read_text());data=json.loads((O/'leitura_kicad.json').read_text());V=A.Vector
native=S/'Divisor_Duplo3.FCStd';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=sha(native)
d=A.openDocument(str(native));h=cfg['h'];cu=cfg['cu'];rows=[]
items=[('Sinal_A','F.Cu','SIG_A',h+cu),('Sinal_B','F.Cu','SIG_B',h+cu),('Terra','B.Cu','GND',-cu)]
items += [('Ilha_inferior_'+p['name'],'B.Cu','SIG_'+p['name'][-1],-cu) for p in cfg['portas']]
for name,layer,net,z in items:
    sh=d.getObject(name).Shape
    faces=[f for f in sh.Faces if abs(f.BoundBox.ZMin-z)<1e-7 and abs(f.BoundBox.ZMax-z)<1e-7]
    assert len(faces)==1,(name,len(faces))
    f=faces[0];outer=f.OuterWire
    pts=lambda w:[[v.x,v.y] for v in w.discretize(Deflection=1e-6)]
    rows.append(dict(objeto=name,camada=layer,rede=net,exterior=pts(outer),furos=[pts(w) for w in f.Wires if not w.isSame(outer)],area_CAD_mm2=f.Area))
A.closeDocument(d.Name);assert before==sha(native)
(O/'faces_cad.json').write_text(json.dumps(dict(faces=rows,fonte_fcstd_sha256=before,fonte_config_sha256=sha(S/'configuracao.json'),leitura_KiCad_sha256=sha(O/'leitura_kicad.json'),deflexao_discretizacao_mm=1e-6)))
print('FACES_CAD_EXPORTADAS',len(rows))
