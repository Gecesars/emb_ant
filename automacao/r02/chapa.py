"""Gerar o dobrado, o plano e os DXFs R02 com os oito furos dos dois divisores."""
import json
import os
import sys
from pathlib import Path

repo=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(repo/"freecad/mecanica_R01/fonte"))
import dimensoes as dim

out=Path(os.environ["P1H_R02"])/"compacta"
out.mkdir(exist_ok=True,parents=True)
old=dim.ref_bolts()
new=[(dim.PIN+cx+dx,y) for cx in (-131.5,131.5) for dx in (-21.5,21.5) for y in (-6.5,6.5)]
dim.ref_bolts=lambda:old+new
dim.SAIDA=out
if "--dxf" in sys.argv:
    import exportar_corte
    exportar_corte.main()
else:
    import construir as m
    flat=m.flat()
    folded=m.folded()
    result=dict(volume_dobrado_mm3=folded.Volume,volume_planificado_mm3=flat,novos_furos_mm=new,diametro_furos_mm=2.8)
    (out/"verificacao.json").write_text(json.dumps(result,indent=2),encoding="utf8")
