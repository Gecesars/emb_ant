"""Audita apenas montagem mecanica R09; nao simula RF."""
import FreeCAD as A, Part, json, hashlib
from pathlib import Path
ROOT=Path('D:/dev/EMBRAER/emb_ant/projetos/P2M19/mecanica_R09_PRELIMINAR')
d=A.openDocument(str(ROOT/'P2M19_R09_PRELIMINAR.FCStd'))
spec=json.loads((ROOT/'objetos.json').read_text())
final=[d.getObject(n) for n in spec['finais']]
crit=set(spec['criticos']);rows=[];tested=0
bad=[o.Name for o in final if not o.Shape.isValid() or o.Shape.Volume<=0]
for i,a in enumerate(final):
    aa=a.Shape.BoundBox
    for b in final[i+1:]:
        if a.Name not in crit and b.Name not in crit:continue
        bb=b.Shape.BoundBox
        if any(min(getattr(aa,k+'Max'),getattr(bb,k+'Max'))-max(getattr(aa,k+'Min'),getattr(bb,k+'Min'))<1e-6 for k in 'XYZ'):continue
        tested+=1
        volume=a.Shape.common(b.Shape).Volume
        if volume>1e-5:rows.append(dict(a=a.Name,b=b.Name,volume_mm3=volume))
hashfail=[]; geometry_fail=[]; geometry_checks=[]
source=A.openDocument('D:/dev/EMBRAER/emb_ant/projetos/P2M19/continuacao_72mm_ref146_14passes/P2M19_R04_72mm_ref146.FCStd')
cached=ROOT/'verificacao_rf_reabertura.json'
refcheck=json.loads(cached.read_text()) if cached.exists() else None
if refcheck:
    assert not refcheck['RF_geometria_divergente']
    initial=json.loads((ROOT/'verificacao_inicial.json').read_text())
    assert hashlib.sha256(Path(source.FileName).read_bytes()).hexdigest()==initial['fonte_cad_sha256']
for name,value in spec['rf_hashes'].items():
    actual=hashlib.sha256(d.getObject(name).Shape.exportBrepToString().encode()).hexdigest()
    if refcheck and actual==spec.get('rf_hashes_pos_reabertura',{}).get(name):
        prior=[r for r in refcheck['RF_conferencia_geometrica'] if r['nome']==name]
        if prior:
            assert prior[0]['aprovado'];geometry_checks+=prior;hashfail.append(name)
        continue
    if actual!=value:
        hashfail.append(name)
        a=source.getObject(name).Shape;b=d.getObject(name).Shape
        diff1=a.cut(b).Volume;diff2=b.cut(a).Volume
        bounds=max(abs(getattr(a.BoundBox,k)-getattr(b.BoundBox,k)) for k in ['XMin','XMax','YMin','YMax','ZMin','ZMax'])
        ca=sum((s.CenterOfMass*s.Volume for s in a.Solids),A.Vector())/a.Volume
        cb=sum((s.CenterOfMass*s.Volume for s in b.Solids),A.Vector())/b.Volume
        centroid=(ca-cb).Length
        passed=diff1<1e-5 and diff2<1e-5 and bounds<1e-7 and centroid<1e-7 and len(a.Solids)==len(b.Solids)
        geometry_checks.append(dict(nome=name,diferenca_origem_menos_salvo_mm3=diff1,diferenca_salvo_menos_origem_mm3=diff2,delta_bbox_mm=bounds,delta_centroide_mm=centroid,aprovado=passed))
        if not passed:geometry_fail.append(name)
report=dict(estado='PRELIMINAR',corpos=len(final),invalidos=bad,RF_BREP_serializacao_divergente=hashfail,RF_geometria_divergente=geometry_fail,RF_conferencia_geometrica=geometry_checks,
    pares_testados=tested,intersecoes=rows,reaberto=True,
    referencia_conferencia_RF_sha256=hashlib.sha256(cached.read_bytes()).hexdigest() if refcheck else None,
    observacao='Intersecoes medem volume positivo >1e-5 mm3; contatos de faces sao permitidos. BREP posicionado, sem analise estrutural. Conferencia RF anterior reaproveitada apenas com fonte SHA e formas BREP pos-reabertura identicas.')
(ROOT/'verificacao_cad.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2),flush=True)
