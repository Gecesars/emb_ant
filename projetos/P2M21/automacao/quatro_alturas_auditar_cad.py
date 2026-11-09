"""Executar no FreeCAD headless; confere translação sem alterar os documentos."""
from pathlib import Path
import FreeCAD as A
import json

root=Path('D:/dev/EMBRAER/P2M21/R11_Divisor_Ajustes')
plan=json.loads((root/'plano_alturas.json').read_text())
source=root/plan['fonte'];baseline_height=plan['altura_nominal_mm']
base=A.openDocument(str(source/'4_elementos.FCStd'))
manifest=json.loads((source/'cad/manifesto.json').read_text())
results=[]
for name in plan['variantes'][1:]:
    cfg=json.loads((root/name/'configuracao.json').read_text())
    height=cfg['distancia_face_inferior_laminado_ao_refletor_mm']
    d=A.openDocument(str(root/name/'4_elementos.FCStd'));rows=[]
    for n in manifest:
        a=base.getObject(n).Shape;b=d.getObject(n).Shape
        dz=0 if n=='Refletor_Al2mm' else height-baseline_height
        aa=a.optimalBoundingBox(False,False);bb=b.optimalBoundingBox(False,False)
        err=max(abs(getattr(bb,k)-getattr(aa,k)-(dz if k.startswith('Z') else 0)) for k in ['XMin','XMax','YMin','YMax','ZMin','ZMax'])
        dv=abs(a.Volume-b.Volume)
        assert err<1e-6 and dv<1e-6,(name,n,err,dv)
        rows.append(dict(objeto=n,delta_z_mm=dz,erro_envelope_mm=err,erro_volume_mm3=dv))
    results.append(dict(variante=name,aprovado=True,objetos=len(rows),verificacoes=rows))
    A.closeDocument(d.Name)
A.closeDocument(base.Name)
(root/'auditoria_cad_alturas.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
print([(r['variante'],r['aprovado'],r['objetos']) for r in results])
