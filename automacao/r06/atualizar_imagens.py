"""Executar na GUI FreeCAD: sincronizar o clone visual com o chicote selecionado."""
import hashlib,json
from pathlib import Path
import FreeCAD as App

root=Path('D:/dev/EMBRAER/P1H/R06_sem_cabos')
config=json.loads((root/'configuracao_circuito.json').read_text(encoding='utf8'))
source=Path(config['geometria'])
visual_path=root/'imagens/Montagem_visual.FCStd'
visual=next((d for d in App.listDocuments().values() if Path(d.FileName).resolve()==visual_path.resolve()),None)
assert visual is not None,'Abrir o clone visual proprio, sem modificar a montagem do usuario.'
native=App.openDocument(str(source))
ns={o.Label:o for o in native.Objects};vs={o.Label:o for o in visual.Objects}
assert len(ns)==351 and set(ns)==set(vs)
records=[]
for name,obj in ns.items():
    if name.startswith(('Sinal_','Capa_','Lancamento_','Isol_')):continue
    a,b=obj.Shape,vs[name].Shape
    error=a.cut(b).Volume+b.cut(a).Volume
    assert error<1e-6,(name,error)
    records.append(dict(objeto=name,diferenca_simetrica_mm3=error))
for name,obj in ns.items():vs[name].Shape=obj.Shape.copy()
visual.recompute();visual.save()
routes={}
for obj in native.Objects:
    name=obj.Label
    if name.startswith('Capa_'):routes[name[5:]]=obj.Shape.optimalBoundingBox(False,False).ZMin
    elif name.startswith('Lancamento_'):routes['IN_'+name[-1]]=obj.Shape.optimalBoundingBox(False,False).ZMin
assert len(routes)==26
for name,obj in ns.items():
    a,b=obj.Shape,vs[name].Shape
    assert a.cut(b).Volume+b.cut(a).Volume<1e-6,name
record=dict(fonte=str(source),sha256=hashlib.sha256(source.read_bytes()).hexdigest(),objetos=len(ns),
            comparacao_fora_do_chicote=records,comparacao_visual_diferenca_max_mm3=0.,
            envelope_coax_zmin_mm=min(routes.values()),
            metodo_envelope='OCCT optimalBoundingBox(False,False), independente de triangulacao')
(root/'imagens/manifesto_montagem.json').write_text(json.dumps(record,indent=2),encoding='utf8')
(root/'imagens/envelopes_cabos.json').write_text(json.dumps(routes,indent=2),encoding='utf8')
App.closeDocument(native.Name);App.setActiveDocument(visual.Name)
script=Path('D:/dev/EMBRAER/emb_ant/automacao/r06/imagens_freecad.py')
exec(compile(script.read_text(encoding='utf8'),str(script),'exec'))
