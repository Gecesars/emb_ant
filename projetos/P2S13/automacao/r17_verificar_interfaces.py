"""Conferir contatos nominais e reabertura STEP, sem modificar a montagem."""
from pathlib import Path
import FreeCAD as A,Part,json
r=Path('D:/dev/EMBRAER/P2S13/R17_Flanges_Refletor/mecanica');d=A.openDocument(str(r/'Antena_DN100_R17_PRELIMINAR.FCStd'))
objs=[o for o in d.Objects if o.isDerivedFrom('Part::Feature')];tube=next(o for o in objs if 'PVC' in o.Name)
pairs=[('Refletor_Al2mm','Flange_Inferior'),('Refletor_Al2mm','Flange_Superior'),('Junta_Inferior',tube.Name),('Junta_Superior',tube.Name),('Junta_Inferior','Flange_Inferior'),('Junta_Superior','Flange_Superior'),('N_A_Corpo','Flange_Inferior'),('N_A_Porca_arruela','Flange_Inferior'),('N_B_Corpo','Flange_Inferior'),('N_B_Porca_arruela','Flange_Inferior')]
contacts=[dict(a=a,b=b,distancia_mm=d.getObject(a).Shape.distToShape(d.getObject(b).Shape)[0]) for a,b in pairs]
step=Part.read(str(r/'Antena_DN100_R17_PRELIMINAR.step'));v=sum(o.Shape.Volume for o in objs)
out=dict(contatos=contacts,objetos=len(objs),solidos=sum(len(o.Shape.Solids) for o in objs),STEP_valido=step.isValid(),
 volume_nativo_mm3=v,volume_STEP_mm3=step.Volume,erro_relativo_volume_STEP=abs(step.Volume-v)/v,
 observacao_STEP='FCStd/BREP e a autoridade geometrica. Volume STEP reimportado reportado, nao alegado identico bit a bit.')
(r/'verificacao_interfaces.json').write_text(json.dumps(out,indent=2),encoding='utf-8');A.closeDocument(d.Name)
print(json.dumps(out,indent=2),flush=True)
assert out['STEP_valido'] and all(c['distancia_mm']<1e-6 for c in contacts)
