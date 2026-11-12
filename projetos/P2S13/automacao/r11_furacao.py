from pathlib import Path
import pcbnew as k,os,json,hashlib
S=Path(os.environ['P2S13_DIV3_ROOT']);O=S/'kicad';name='divisor_duplo_1x3_C08'
b=k.LoadBoard(str(O/(name+'.kicad_pcb')));holes=[p for f in b.GetFootprints() for p in f.Pads() if p.GetDrillSize().x]
assert len(holes)==8 and all(p.GetAttribute()==k.PAD_ATTRIB_PTH for p in holes)
assert all(abs(k.ToMM(p.GetDrillSize().x)-1.1)<1e-9 for p in holes)
w=k.EXCELLON_WRITER(b);w.SetFormat(True,k.GENDRILL_WRITER_BASE.KEEP_ZEROS,3,6);w.SetOptions(False,False,k.VECTOR2I(0,0),False)
assert w.CreateDrillandMapFilesSet(str(O/'gerbers'),True,False)
(O/'precisao_furacao.json').write_text(json.dumps(dict(PTH=8,NPTH=0,diametro_acabado_mm=1.1,formato='3:6 mm',modificacao_CAM=False),indent=2))
