"""Mede o deslocamento real das facetas sinalizadas pelo TAU contra o CAD fonte.

Executar no FreeCAD headless. Nao exporta triangulos para o repositorio.
"""
from pathlib import Path
import os,json,math,time
import FreeCAD as A,Part
root=Path(os.environ['P2S13_ROOT'])
file=next((root/'P2S13.aedtresults').rglob('nominalmesh.g3derr'))
rows={};points=[]
for line in file.open():
    if '#xyz tv' not in line:continue
    q=line.split('#')[0].split();points.append(tuple(float(x) for x in q[:3]))
    if '#xyz tv2' in line:
        bid=int(q[4]);rows.setdefault(bid,[]).append(points[-3:]);points=[]
names={246:'R2_PCB_RO4350B',1884:'R2_F_SIG_A_Cu0'}
assert set(rows).issubset(set(names)),list(rows)
d=A.openDocument(str(root/'P2S13.FCStd'));results=[]
for bid,triangles in rows.items():
    sh=d.getObject(names[bid]).Shape;unique=sorted(set(p for t in triangles for p in t));distances=[];start=time.time()
    for p in unique:
        v=Part.Vertex(A.Vector(*p));distances.append(sh.distToShape(v)[0])
    worst=max(range(len(unique)),key=lambda i:distances[i])
    result=dict(body_id=bid,objeto=names[bid],triangulos_sinalizados=len(triangles),vertices_unicos=len(unique),distancia_maxima_ao_CAD_mm=distances[worst],vertice_maximo_mm=unique[worst],distancia_media_mm=sum(distances)/len(distances),vertices_acima_1um=sum(x>.001 for x in distances),tempo_s=time.time()-start)
    results.append(result);print(json.dumps(result),flush=True)
(root/'desvios_reparos.json').write_text(json.dumps(dict(metodo='Distancia minima de cada vertice sinalizado ao solido CAD fonte. Mede posicao dos vertices, nao conectividade nem completude das faces.',objetos=results),indent=2)+'\n')
A.closeDocument(d.Name)
