"""Excellon KiCad com coordenadas 3:6 e diametro nominal sem truncar a 3 casas.
KiCad 10 SetFormat(3,6) mantem XY mas ainda grava ferramentas com 3 decimais.
A unica alteracao CAM e restaurar o diametro lido do proprio arquivo nativo.
"""
from pathlib import Path
import pcbnew as k,json,re,hashlib
R=Path(__file__).resolve().parents[3];O=R/'projetos/P2S13/kicad/divisor_duplo_1x3_C07'
name='divisor_duplo_1x3_C07';cam=O/'gerbers';cam.mkdir(exist_ok=True)
b=k.LoadBoard(str(O/(name+'.kicad_pcb')))
holes=[p for f in b.GetFootprints() for p in f.Pads() if p.GetDrillSize().x]
assert len(holes)==8 and all(p.GetAttribute()==k.PAD_ATTRIB_NPTH for p in holes)
diameters={k.ToMM(p.GetDrillSize().x) for p in holes};assert len(diameters)==1
diameter=diameters.pop()
w=k.EXCELLON_WRITER(b);w.SetFormat(True,k.GENDRILL_WRITER_BASE.KEEP_ZEROS,3,6)
w.SetOptions(False,False,k.VECTOR2I(0,0),False)
assert w.CreateDrillandMapFilesSet(str(cam),True,False)
p=cam/(name+'-NPTH.drl');raw=p.read_text();tools=re.findall(r'^T(\d+)C([.\d]+)$',raw,re.M)
assert len(tools)==1 and abs(float(tools[0][1])-diameter)<.001
(O/'evidencias').mkdir(exist_ok=True)
(O/'evidencias/furacao_original_KiCad_NPTH.txt').write_text(raw,encoding='utf8')
new=re.sub(r'^T(\d+)C([.\d]+)$',lambda m:'T'+m[1]+'C'+format(diameter,'.6f'),raw,flags=re.M)
assert new.replace('C'+format(diameter,'.6f'),'C'+tools[0][1])==raw
p.write_text(new,encoding='ascii')
record=dict(furos=8,metalizados=False,diametro_nativo_mm=diameter,diametro_KiCad_3casas_mm=float(tools[0][1]),
    diametro_CAM_restaurado_mm=diameter,formato_XY='3:6 mm, zeros mantidos; origem absoluta',
    alteracao='Somente diametro T1 restaurado do nativo; coordenadas e quantidade nao alteradas',
    original_sha256=hashlib.sha256(raw.encode()).hexdigest(),final_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
(O/'precisao_furacao.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
report=['C07 - RELATORIO DE FURACAO NOMINAL CONFERIDA','NPTH: 8; PTH: 0; vias: 0',
    'Diametro nativo e CAM: %.6f mm'%diameter,'Coordenadas Excellon: mm absolutos 3:6, zeros mantidos',
    'Sem metalizacao. Cobre ate o furo: requer DFM especial JLC.',
    'Nao confundir com os antipads inferiores de 3.030000 mm.','', 'X_KiCad_mm;Y_KiCad_mm;Diametro_mm']
for p in sorted(holes,key=lambda p:(p.GetPosition().x,p.GetPosition().y)):
    report.append('%.6f;%.6f;%.6f'%(k.ToMM(p.GetPosition().x),k.ToMM(p.GetPosition().y),diameter))
(O/'furacao.txt').write_text('\n'.join(report)+'\n',encoding='utf8')
print(json.dumps(record,indent=2))
