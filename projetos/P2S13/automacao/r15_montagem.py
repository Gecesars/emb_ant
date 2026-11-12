"""Atualizar somente Sinal_A/B na copia da montagem, preservando cabos/antenas."""
import os,json
from pathlib import Path
import FreeCAD as A
ROOT=Path(os.environ['P2S13_R15_CASE']);BASE=Path('D:/dev/EMBRAER/P2S13/R14_Compacto_Simetrico_SemRadome/c00')
OUT=ROOT/'visual';OUT.mkdir(exist_ok=True);target=OUT/'Antena_C09_Ajustada_PRELIMINAR.FCStd';assert not target.exists()
cfg=json.loads((ROOT/'configuracao.json').read_text());d=A.openDocument(str(BASE/'visual/Antena_C09_SemRadome_PRELIMINAR.FCStd'))
div=A.openDocument(str(ROOT/'divisor/Divisor_Duplo3.FCStd'));man=json.loads((BASE/'cad/manifesto.json').read_text())
old={n:d.getObject(n).Shape.copy() for n in man}
assert len(old)==122
for name in ['Sinal_A','Sinal_B']:
    sh=div.getObject(name).Shape.copy();sh.rotate(A.Vector(),A.Vector(1,0,0),180);sh.translate(A.Vector(0,0,cfg['divisor_translacao_z_mm']))
    d.getObject('D_'+name).Shape=sh
d.Label='C09 '+ROOT.name+' ajustada — sem radome — PRELIMINAR';d.recompute()
changed=[]
for n,sh in old.items():
    t=d.getObject(n).Shape;assert t.isValid() and len(t.Solids)==1
    delta=sh.cut(t).Volume+t.cut(sh).Volume
    if delta>1e-7:changed.append(n)
assert sorted(changed)==['D_Sinal_A','D_Sinal_B'],changed
bad=[]
for n in changed:
    sh=d.getObject(n).Shape
    for other in old:
        if other==n:continue
        t=d.getObject(other).Shape
        if sh.BoundBox.intersect(t.BoundBox):
            v=sh.common(t).Volume
            if v>1e-7:bad.append([n,other,v])
assert not bad,bad
d.saveAs(str(target));A.closeDocument(div.Name);A.closeDocument(d.Name)
re=A.openDocument(str(target));assert len(man)==122 and all(re.getObject(n).Shape.isValid() and len(re.getObject(n).Shape.Solids)==1 for n in man)
(OUT/'conferencia_montagem.json').write_text(json.dumps(dict(solidos=122,alterados=changed,inalterados=120,intersecoes_novas=bad,ramais_cabos_antena_preservados=True),indent=2))
A.closeDocument(re.Name);print('MONTAGEM_C01_VALIDADA')
