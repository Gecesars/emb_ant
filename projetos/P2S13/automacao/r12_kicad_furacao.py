"""Exporta furação M00 com resolução XY de 1 nm, sem alterar furos nominais."""
from pathlib import Path
import pcbnew as k,json
R=Path(__file__).resolve().parents[3];O=R/'projetos/P2S13/kicad/conjunto_R12/placa2_M00'
b=k.LoadBoard(str(O/'2_elementos.kicad_pcb'))
w=k.EXCELLON_WRITER(b);w.SetFormat(True,k.GENDRILL_WRITER_BASE.KEEP_ZEROS,3,6)
w.SetOptions(False,False,k.VECTOR2I(0,0),False)
assert w.CreateDrillandMapFilesSet(str(O/'gerbers'),True,False)
(O/'precisao_furacao.json').write_text(json.dumps(dict(PTH=6,NPTH=0,diametros_acabados_mm={'0.4':4,'1.1':2},formato='3:6 mm',modificacao_CAM=False),indent=2)+'\n',encoding='utf8')
print('Furacao exportada 3:6; 4 vias 0.4 mm + 2 entradas 1.1 mm.')
