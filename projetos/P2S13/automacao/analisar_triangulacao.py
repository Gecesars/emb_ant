"""Qualidade das facetas de entrada do mesher, nao qualidade final dos tetraedros."""
from pathlib import Path
import argparse,re,json,numpy as np
p=argparse.ArgumentParser();p.add_argument('origem',type=Path);p.add_argument('destino',type=Path);args=p.parse_args()
facebody={};body=None;facetfaces={};facet=None;points={};tris=[]
for line in args.origem.read_text().splitlines():
    if '# id name' in line:body=line.split('#')[0].split()[3]
    elif re.search(r'# face \d+$',line):facebody[int(line.split()[0])]=body
    elif '#facet id,' in line:facet=int(line.split()[0]);facetfaces[facet]=[]
    elif '#face id, sense' in line:facetfaces[facet].append(int(line.split()[0]))
    elif '#pid px py pz pid' in line:
        q=line.split();points[int(q[0])]=[float(x) for x in q[1:4]]
    elif '#triid, tv1, tv2, tv3, facetid' in line:tris.append([int(x) for x in line.split('#')[0].split()])
pts=np.array([[points[i] for i in t[1:4]] for t in tris]);u=pts[:,1]-pts[:,0];v=pts[:,2]-pts[:,0]
area=np.linalg.norm(np.cross(u,v),axis=1)/2
edges=np.stack([np.linalg.norm(u,axis=1),np.linalg.norm(v,axis=1),np.linalg.norm(pts[:,2]-pts[:,1],axis=1)],axis=1)
quality=4*np.sqrt(3)*area/np.sum(edges**2,axis=1)
radius_ratio=np.prod(edges,axis=1)*np.sum(edges,axis=1)/(16*area**2)
rows=[]
for i,t in enumerate(tris):
    rows.append(dict(tri=t[0],facet=t[4],corpos=sorted({facebody.get(f,'?') for f in facetfaces.get(t[4],[])}),area_mm2=float(area[i]),qualidade=float(quality[i]),razao_R_2r=float(radius_ratio[i]),altura_min_mm=float(2*area[i]/edges[i].max()),arestas_mm=edges[i].tolist(),vertices_mm=pts[i].tolist()))
reflector=[r for r in rows if 'Refletor_Al2mm' in r['corpos']]
result=dict(fonte=str(args.origem),pontos=len(points),triangulos=len(tris),triangulos_refletor=len(reflector),area_min_mm2=float(area.min()),qualidade_min=float(quality.min()),triangulos_degenerados_area1em10=int((area<1e-10).sum()),piores=sorted(rows,key=lambda x:x['qualidade'])[:25],piores_refletor=sorted(reflector,key=lambda x:x['qualidade'])[:10],nota='Facetas antes da recuperacao volumetrica; isto nao e auditoria da malha final.')
args.destino.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['piores','piores_refletor']},indent=2))
