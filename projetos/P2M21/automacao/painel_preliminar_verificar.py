"""Conferencia geometrica R18, sem solver; ignora containers que agregam shapes."""
import FreeCAD as A, Part, json, hashlib
from pathlib import Path
root=Path('D:/dev/EMBRAER/P2M21/R18_Mecanica_Preliminar')
native=root/'P2M21_R18_PRELIMINAR.FCStd'
d=A.openDocument(str(native));shapes=[o for o in d.Objects if o.isDerivedFrom('Part::Feature') and o.Name!='Reserva_distribuicao_2x10']
critical=[o for o in shapes if o.Name.startswith(('Grampo_','N_')) or o.Name=='Refletor_Al2mm']
assert all(o.Shape.isValid() for o in shapes)
inter=[];tested=0
for a in critical:
 ba=a.Shape.BoundBox
 for b in shapes:
  if a==b or (b in critical and b.Name<a.Name):continue
  bb=b.Shape.BoundBox
  if any(min(getattr(ba,k+'Max'),getattr(bb,k+'Max'))-max(getattr(ba,k+'Min'),getattr(bb,k+'Min'))<1e-6 for k in 'XYZ'):continue
  tested+=1;vol=a.Shape.common(b.Shape).Volume
  if vol>1e-5:inter.append(dict(a=a.Name,b=b.Name,volume_mm3=vol))
source=Path('D:/dev/EMBRAER/P2M21/R17_Dez_Celulas_78mm/P2M21_10celulas_78mm.FCStd')
src=A.openDocument(str(source));identity=[]
for o in src.Objects:
 if not o.isDerivedFrom('Part::Feature') or o.Name=='Refletor_Al2mm':continue
 n=d.getObject(o.Name);dv=abs(n.Shape.Volume-o.Shape.Volume);da=abs(n.Shape.Area-o.Shape.Area)
 assert dv<1e-7 and da<1e-7 and len(n.Shape.Faces)==len(o.Shape.Faces)
 identity.append(o.Name)
assert len(identity)==410
A.closeDocument(src.Name)
dim=json.loads((root/'dimensoes.json').read_text());sheet=d.getObject('Refletor_Al2mm').Shape
for p in dim['fixacoes_pom']:assert not sheet.isInside(A.Vector(p['x'],p['y'],-1),1e-6,True)
for y in [-24,24]:assert not sheet.isInside(A.Vector(-487,y,-40),1e-6,True)
report=dict(estado='PRELIMINAR',formas=len(shapes),solidos_validos=True,pares_testados=tested,intersecoes=inter,
 geometria_celulas_preservada=len(identity),furos_M2_passantes=40,recortes_N_passantes=2,reaberto=True,
 exclusoes='Containers App::DocumentObjectGroup e reserva de espaco nao sao componentes fisicos; excluidos da colisao.',
 limitacoes='Verificacao nominal de geometria, sem analise de tolerancias, resistencia mecanica, vedacao ou RF da R18.',
 fonte_cad_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),conector_step_sha256=hashlib.sha256(Path('D:/dev/EMBRAER/82-6784.stp').read_bytes()).hexdigest())
(root/'verificacao_cad.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not inter,inter
for name,file in [('Refletor_Al2mm','Refletor_dobrado_PRELIMINAR'),('Grampo_09','Grampo_POM_PRELIMINAR')]:
 nd=A.newDocument(file);p=nd.addObject('Part::Feature',file);p.Shape=d.getObject(name).Shape.copy();nd.recompute();nd.saveAs(str(root/(file+'.FCStd')));p.Shape.exportStep(str(root/(file+'.step')));A.closeDocument(nd.Name)
A.closeDocument(d.Name)
print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
