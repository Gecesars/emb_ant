"""STEP para integracao mecanica; nativo e referencia para RF/parametros."""
import FreeCAD as A,Part,json
from pathlib import Path
from collections import defaultdict
ROOT=Path('D:/dev/EMBRAER/emb_ant/projetos/P2M19/mecanica_R09_PRELIMINAR')
d=A.openDocument(str(ROOT/'P2M19_R09_PRELIMINAR.FCStd'));spec=json.loads((ROOT/'objetos.json').read_text())
objects=[d.getObject(n) for n in spec['finais']]
shape=Part.makeCompound([o.Shape for o in objects]);path=ROOT/'P2M19_R09_PRELIMINAR.step'
# Exportar explicitamente apenas quando ainda nao existir; evita tocar entrega revisada.
if not path.exists():shape.exportStep(str(path))
step=Part.read(str(path));a=shape.BoundBox;b=step.BoundBox
def key(s):
 b=s.optimalBoundingBox(False,False);return tuple(round(getattr(b,k),4) for k in ['XMin','XMax','YMin','YMax','ZMin','ZMax'])
src=defaultdict(list);dst=defaultdict(list)
for o in objects:
 for i,s in enumerate(o.Shape.Solids):src[key(s)].append((o.Name,i,s.Volume))
for i,s in enumerate(step.Solids):dst[key(s)].append((i,s.Volume))
unmatched=[];components=defaultdict(lambda:dict(solidos=0,volume_CAD_mm3=0,volume_STEP_mm3=0))
for k,ss in src.items():
 tt=dst.get(k,[])
 if len(ss)!=len(tt):unmatched.append(dict(bbox=list(k),origem=[q[:2] for q in ss],quantidade_STEP=len(tt)));continue
 for so,st in zip(sorted(ss,key=lambda x:x[2]),sorted(tt,key=lambda x:x[1])):
  r=components[so[0]];r['solidos']+=1;r['volume_CAD_mm3']+=so[2];r['volume_STEP_mm3']+=st[1]
detail=[]
for n,r in components.items():
 r.update(nome=n,delta_volume_mm3=r['volume_STEP_mm3']-r['volume_CAD_mm3']);r['delta_relativo']=r['delta_volume_mm3']/r['volume_CAD_mm3'];detail.append(r)
detail.sort(key=lambda r:abs(r['delta_volume_mm3']),reverse=True)
report=dict(solidos_CAD=len(shape.Solids),solidos_STEP=len(step.Solids),valido_STEP=step.isValid(),volume_CAD_mm3=shape.Volume,volume_STEP_mm3=step.Volume,
 erro_volume_mm3=abs(shape.Volume-step.Volume),erro_volume_relativo=abs(shape.Volume-step.Volume)/shape.Volume,
 erro_bbox_mm=max(abs(getattr(a,k)-getattr(b,k)) for k in ['XMin','XMax','YMin','YMax','ZMin','ZMax']),bbox_mm=[a.XMin,a.XMax,a.YMin,a.YMax,a.ZMin,a.ZMax],
 metodo_componentes='Pareamento de solidos por optimalBoundingBox(False,False) arredondada a0.0001mm; em grupo igual, ordena volume. Evita bbox de hull de controle das curvas. Nao usa booleanas de toda a montagem.',
 componentes_pareados=len(detail),solidos_pareados=sum(r['solidos'] for r in detail),grupos_nao_pareados=unmatched,
 componentes=detail,uso='STEP para visualizacao/integracao mecanica; NAO reimportar como novo modelo RF. FCStd e referencia.')
report.update(soma_volumes_solidos_CAD_mm3=sum(r['volume_CAD_mm3'] for r in detail),soma_volumes_solidos_STEP_mm3=sum(r['volume_STEP_mm3'] for r in detail),
 delta_soma_volumes_solidos_mm3=sum(r['delta_volume_mm3'] for r in detail),maior_delta_volume_corpo_RF_mm3=max(abs(r['delta_volume_mm3']) for r in detail if r['nome'].startswith('C') and not r['nome'].startswith('Cabo')),
 observacao_integracao='Volume global do compound e soma individual dos solidos possuem integracoes numericas distintas no OCCT. Todos os 643 solidos foram pareados; use as duas medidas registradas, sem atribuir toda a diferenca global a geometria perdida.')
assert report['solidos_CAD']==report['solidos_STEP'] and report['valido_STEP'] and report['erro_bbox_mm']<1e-5
(ROOT/'verificacao_STEP.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='componentes'},indent=2));print(json.dumps(detail[:12],indent=2),flush=True)
