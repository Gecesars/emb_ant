"""Confere config usada no KiCad contra solidos que deram origem ao HFSS C07.
Executar em FreeCADCmd isolado, sem salvar ou alterar o original.
"""
from pathlib import Path
import FreeCAD as A,Part,json,hashlib
R=Path(__file__).resolve().parents[3]
S=R/'projetos/P2S13/divisor_duplo_1x3_correcao/c07_centro'
O=R/'projetos/P2S13/kicad/divisor_duplo_1x3_C07';O.mkdir(parents=True,exist_ok=True)
cfg=json.loads((S/'configuracao.json').read_text());p=S/'Divisor_Duplo3.FCStd'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(p);d=A.openDocument(str(p));V=A.Vector
h=cfg['h'];cu=cfg['cu']
shapes={'Terra':Part.makeBox(220,64,cu,V(-110,-32,-cu)), 'Substrato':Part.makeBox(220,64,h,V(-110,-32,0))}
for pol,data in cfg['signals'].items():
    def face(pts):return Part.Face(Part.makePolygon([V(x,y,h) for x,y in pts]))
    f=face(data['exterior'])
    for hole in data['holes']:f=f.cut(face(hole))
    shapes['Sinal_'+pol]=f.extrude(V(0,0,cu))
for ip in cfg['portas']:
    for name in shapes:
        radius=ip['ro'] if name=='Terra' else ip['ri']
        shapes[name]=shapes[name].cut(Part.makeCylinder(radius,h+cu*2+.4,V(ip['x'],ip['y'],-.2)))
rows=[]
for name,s in shapes.items():
    original=d.getObject(name).Shape;diff=s.cut(original).Volume+original.cut(s).Volume
    assert s.isValid() and diff<1e-7,(name,diff)
    rows.append(dict(objeto=name,volume_mm3=original.Volume,diferenca_booleana_mm3=diff))
A.closeDocument(d.Name);assert sha(p)==before
out=dict(aprovado=True,fonte_fcstd_sha256=before,fonte_config_sha256=sha(S/'configuracao.json'),
    fonte_hfss_sha256=sha(S/'Divisor_Duplo3.aedt'),comparacoes=rows,
    nota='Config reproduz exatamente os solidos de PCB do CAD importado no HFSS; pinos, solda e PTFE sao itens de montagem, nao cobre de Gerber.')
(O/'conferencia_cad_hfss.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(out,indent=2))
