"""Extrai faces de cobre e raios PTH/vias do CAD M00 realmente usado pela R12."""
from pathlib import Path
import json,hashlib
import FreeCAD as A,Part
R=Path('D:/dev/EMBRAER/emb_ant');S=R/'projetos/P2S13/casamento_placa2/m00/placa2'
O=R/'projetos/P2S13/kicad/conjunto_R12/placa2_M00'
read=lambda p:json.loads(p.read_text(encoding='utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
n=S/'2_elementos_simetrica.FCStd';before=sha(n);d=A.openDocument(str(n));rec=read(S/'cad/folhas_solidas.json');rows=[]
for name,m in rec.items():
 sh=d.getObject(name).Shape;z=m['base_z_mm']+m['exposto']*m['espessura_mm']
 faces=[f for f in sh.Faces if abs(f.BoundBox.ZMin-z)<1e-7 and abs(f.BoundBox.ZMax-z)<1e-7]
 assert len(faces)==1,(name,len(faces));f=faces[0];outer=f.OuterWire
 pts=lambda w:[[v.x,v.y] for v in w.discretize(Deflection=1e-6)]
 rows.append(dict(objeto=name,camada=name[0],rede=name[2:].rsplit('_Cu',1)[0],exterior=pts(outer),furos=[pts(w) for w in f.Wires if not w.isSame(outer)],area_CAD_mm2=f.Area))
barrels=[]
for obj in d.Objects:
 if obj.Name.startswith(('Via_','PTH_')):
  radii=sorted(set(round(f.Surface.Radius,8) for f in obj.Shape.Faces if isinstance(f.Surface,Part.Cylinder)))
  assert len(radii)==2,(obj.Name,radii)
  barrels.append(dict(objeto=obj.Name,diametro_acabado_mm=2*radii[0],diametro_externo_mm=2*radii[1],metalizacao_mm=radii[1]-radii[0],altura_mm=obj.Shape.BoundBox.ZLength))
A.closeDocument(d.Name);assert before==sha(n)
(O/'faces_cad.json').write_text(json.dumps(dict(faces=rows,barrels=barrels,fonte_fcstd_sha256=before,fonte_geometria_sha256=sha(S/'geometria.json'),deflexao_mm=1e-6),indent=2)+'\n',encoding='utf8')
print('Faces CAD:',len(rows),'Barris:',barrels)
