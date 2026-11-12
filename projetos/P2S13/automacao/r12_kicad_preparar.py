"""Prepara PCB M00 e reutiliza C08, sem alterar a geometria da R12."""
from pathlib import Path
import json,hashlib,shutil,ast
REPO=Path(__file__).resolve().parents[3];HERE=Path(__file__).parent
OUT=REPO/'projetos/P2S13/kicad/conjunto_R12'
SRC=REPO/'projetos/P2S13/casamento_placa2/m00/placa2'
R12=REPO/'projetos/P2S13/curvilinear_simplificado'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
cfg=read(R12/'configuracao.json');assert len(cfg['celulas'])==3
for c in cfg['celulas']:
 for n in ['geometria.json','2_elementos_simetrica.FCStd','cad/manifesto.json','cad/folhas_solidas.json']:
  assert sha(SRC/n)==c['fontes_sha256'][n],n
OUT.mkdir(parents=True,exist_ok=True)
baseline=REPO/'projetos/P2S13/fabricavel_radome/d00/kicad'
dest=OUT/'divisor_C08'
if not dest.exists():shutil.copytree(baseline,dest)
copied=[]
for p in baseline.rglob('*'):
 if p.is_file():
  q=dest/p.relative_to(baseline);assert sha(p)==sha(q),q
  copied.append(dict(arquivo=q.relative_to(OUT).as_posix(),fonte=p.relative_to(REPO).as_posix(),sha256=sha(p)))
(OUT/'origem_C08.json').write_text(json.dumps(copied,indent=2)+'\n',encoding='utf8')
s=(REPO/'projetos/P2M21/automacao/dois_elementos_kicad.py').read_text(encoding='utf-8-sig')
replaces={
 "SOURCE = REPO / 'projetos/P2M21/dois_verticais_divisor/variantes/v05_B_longo_inferior_15'":"SOURCE = REPO / 'projetos/P2S13/casamento_placa2/m00/placa2'",
 "OUT = REPO / 'projetos/P2M21/kicad/2_elementos'":"OUT = REPO / 'projetos/P2S13/kicad/conjunto_R12/placa2_M00'",
 "assert not g['verificacao']['shorts'] and g['verificacao']['cobre_dentro_contorno']":"assert not g['shorts'] and g['radiadores']==2 and g['placa_largura_altura_mm']==[50.,88.]",
 "2_elementos | v05 | RO4350B 0.76 mm":"2_elementos M00 | R12 | RO4350B 0.76 mm",
 "'R01 / arte HFSS v05'":"'R12 / arte HFSS M00'",
 "'2026-11-09'":"'2026-11-12'",
 "board_mm=[49,82.8]":"board_mm=[50,88]",
 "a partir da arte v05":"a partir da arte M00 simetrica usada na R12"
}
for a,b in replaces.items():assert a in s,a;s=s.replace(a,b)
ast.parse(s);(HERE/'r12_kicad_placa2.py').write_text(s,encoding='utf8')
s=(REPO/'projetos/P2M21/automacao/quatro_elementos_conferir.py').read_text(encoding='utf-8-sig')
s=s.replace("projetos/P2M21/kicad/4_elementos","projetos/P2S13/kicad/conjunto_R12/placa2_M00").replace("projetos/P2M21/quatro_elementos_casamento_banda/c12_raiz_intermediaria","projetos/P2S13/casamento_placa2/m00/placa2")
s=s.replace('4_elementos','2_elementos').replace('R13 C12','M00 / R12').replace('70 × 184','50 × 88')
ast.parse(s);(HERE/'r12_kicad_conferir.py').write_text(s,encoding='utf8')
s=(REPO/'projetos/P2M21/automacao/quatro_elementos_gerbers.py').read_text(encoding='utf-8-sig')
s=s.replace("projetos/P2M21/kicad/4_elementos","projetos/P2S13/kicad/conjunto_R12/placa2_M00").replace("projetos/P2M21/quatro_elementos_casamento_banda/c12_raiz_intermediaria","projetos/P2S13/casamento_placa2/m00/placa2")
s=s.replace('4_elementos','2_elementos').replace('{.4:8,1.1:2}','{.4:4,1.1:2}').replace('contorno_mm=[70,184]','contorno_mm=[50,88]').replace('ax.set_xlim(40,120);ax.set_ylim(-207,-13)','ax.set_xlim(52,108);ax.set_ylim(-158,-62)').replace('70 × 184 mm | 8 vias','50 × 88 mm | 4 vias').replace('figsize=(12,11)','figsize=(12,7)')
s=s.replace("assert 'METRIC' in drill", "assert 'FORMAT={3:6/' in drill and 'METRIC' in drill")
s=s.replace("holes[current].append((float(m[1]),float(m[2])))", "holes[current].append((float(m[1])/1e6,float(m[2])/1e6))")
s=s.replace('<=.000501','<=.000001').replace('resolucao_Excellon_mm=.001','resolucao_Excellon_mm=.000001')
s=s.replace('Excellon decimal nativo KiCad arredonda a 0,001 mm; cobre Gerber a 0,000001 mm.', 'Excellon 3:6 e cobre Gerber a 0,000001 mm.')
s=s.replace('rect=(0,.025,1,.94)','rect=(0,.085,1,.94)').replace("fig.text(.5,.012,","fig.text(.5,.018,")
ast.parse(s);(HERE/'r12_kicad_gerbers.py').write_text(s,encoding='utf8')
print('Preparados scripts M00 exata e copia do C08; arquivos C08 identicos:',len(copied))
