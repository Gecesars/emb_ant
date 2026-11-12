"""Atualizar duas folhas de sinal na montagem PVC; manter outros 121 solidos."""
from pathlib import Path
import os,json,FreeCAD as A
ROOT=Path('D:/dev/EMBRAER/P2S13/R16_Tubo_PVC');CASE=Path(os.environ.get('P2S13_R16_CASE',str(ROOT/'dn100_c01')));OUT=CASE/'visual';OUT.mkdir(exist_ok=True)
target=OUT/('Antena_PVC_'+CASE.name.upper()+'_PRELIMINAR.FCStd');assert not target.exists()
d=A.openDocument(str(ROOT/'dn100/visual/Antena_PVC_DN100_PRELIMINAR.FCStd'))
v=A.openDocument(str(CASE/'divisor/Divisor_Duplo3.FCStd'))
old={o.Name:o.Shape.copy() for o in d.Objects if o.isDerivedFrom('Part::Feature') and not o.Shape.isNull()};assert len(old)==123
c=json.loads((CASE/'configuracao.json').read_text())
for n in ['Sinal_A','Sinal_B']:
    s=v.getObject(n).Shape.copy();s.rotate(A.Vector(),A.Vector(1,0,0),180);s.translate(A.Vector(0,0,c['divisor_translacao_z_mm']))
    d.getObject('D_'+n).Shape=s
changed=[];bad=[]
for n,s in old.items():
    t=d.getObject(n).Shape;assert t.isValid() and len(t.Solids)==1
    if s.cut(t).Volume+t.cut(s).Volume>1e-7:changed.append(n)
assert sorted(changed)==['D_Sinal_A','D_Sinal_B']
for n in changed:
    s=d.getObject(n).Shape
    for m in old:
        if m==n:continue
        t=d.getObject(m).Shape
        if s.BoundBox.intersect(t.BoundBox):
            vol=s.common(t).Volume
            if vol>1e-7:bad.append([n,m,vol])
assert not bad,bad
d.Label='Antena PVC '+CASE.name.upper()+' — PRELIMINAR';d.recompute();d.saveAs(str(target))
A.closeDocument(v.Name);A.closeDocument(d.Name)
d=A.openDocument(str(target));assert len([o for o in d.Objects if o.isDerivedFrom('Part::Feature') and not o.Shape.isNull()])==123
assert all(d.getObject(n).Shape.isValid() for n in old);A.closeDocument(d.Name)
(OUT/'auditoria_cad.json').write_text(json.dumps(dict(solidos=123,alterados=changed,inalterados=121,intersecoes_novas=bad,antena_tubo_cabos_preservados=True),indent=2))
print('MONTAGEM_PVC_C01_CONFERIDA')
