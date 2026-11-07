"""Refletor R05 parametrico, dobrado e planificado, com corte 1:1 independente."""
import json
import os
import sys
from pathlib import Path

repo=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(repo/'freecad/mecanica_R01/fonte'))
import dimensoes as dim

output=Path(os.environ['P1H_REFLETOR_R05'])
output.mkdir(parents=True,exist_ok=True)
old=dim.ref_bolts()
new=[(dim.PIN+center+offset,y) for center in (-131.5,131.5) for offset in (-21.5,21.5) for y in (-6.5,6.5)]
dim.ref_bolts=lambda:old+new
dim.MEIA_FACE=20
dim.LADO_FLAT=dim.MEIA_FACE+dim.BA+dim.PROF_NERV-dim.RO
dim.SAIDA=output
if '--dxf' in sys.argv:
    import exportar_corte
    exportar_corte.main()
else:
    import construir
    import Part
    flat=construir.flat()
    folded=construir.folded()
    reference=Part.read(os.environ['P1H_REFLETOR_STEP'])
    difference=folded.cut(reference).Volume+reference.cut(folded).Volume
    assert difference<1e-5,difference
    result=dict(volume_dobrado_mm3=folded.Volume,volume_planificado_mm3=flat,
        largura_face_mm=40,espessura_mm=dim.T,raio_interno_mm=dim.RI,fator_K=dim.K,
        novos_furos_mm=new,diametro_furos_mm=2.8,diferenca_simetrica_com_geometria_RF_mm3=difference)
    (output/'verificacao.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print('REFLETOR_PARAMETRICO_OK',result)
