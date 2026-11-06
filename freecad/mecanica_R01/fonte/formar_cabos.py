"""Gabaritos geométricos de linhas de centro, sem solver físico. Unidades mm."""
import json, math
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from dimensoes import *

R=4.4
def fillet(points,r=R):
    pts=np.array(points,dtype=float)
    edges=[];last=pts[0]
    for a,b,c in zip(pts,pts[1:],pts[2:]):
        u=(a-b)/np.linalg.norm(a-b);v=(c-b)/np.linalg.norm(c-b)
        theta=math.acos(np.clip(-u@v,-1,1))
        if theta<.00001:continue
        t=r*math.tan(theta/2);p=b+u*t;q=b+v*t
        if (p-last)@(-u)<-.0001 or t>=np.linalg.norm(c-b):raise ValueError("tangentes cruzadas")
        center=b+(u+v)/np.linalg.norm(u+v)*r/math.cos(theta/2)
        mid=center+(b-center)/np.linalg.norm(b-center)*r
        if np.linalg.norm(last-p)>.0001:edges.append(["L",last,p])
        edges.append(["A",p,mid,q]);last=q
    edges.append(["L",last,pts[-1]])
    return [[e[0]]+[v.tolist() for v in e[1:]] for e in edges]
def lengths(edges):
    ans=[]
    for tag,*rest in edges:
        a,b,*c=np.array(rest)
        d=np.linalg.norm(a-(c[0] if c else b))
        ans.append(d if tag=="L" else 2*R*math.asin(min(1,d/(2*R))))
    return ans
def sample(edges,step=1.0):
    out=[]
    for e,d in zip(edges,lengths(edges)):
        a,b,*c=np.array(e[1:]);u=np.linspace(0,1,max(2,math.ceil(d/step)+1))[:,None]
        if e[0]=="L":out.extend(a+(b-a)*u)
        else:
            end=c[0];v=b-(a+end)/2;v/=np.linalg.norm(v)
            C=b-R*v;theta=d/R
            out.extend(C+np.sin(theta*(1-u))/math.sin(theta)*(a-C)+np.sin(theta*u)/math.sin(theta)*(end-C))
    return np.array(out)
def path_candidate(s,e,offset,frac):
    direct=e[:2]-s[:2];dist=np.linalg.norm(direct)
    m=s[:2]+frac*direct+offset*np.array([-direct[1],direct[0]])/dist
    plan=[s[:2],e[:2]] if offset==0 else [s[:2],m,e[:2]]
    def at(z):return fillet([s]+[[*p,z] for p in plan]+[e])
    ref=-155
    z=ref+(sum(lengths(at(ref)))-254)/2
    edges=at(z)
    if abs(sum(lengths(edges))-254)>1e-5:raise ValueError("comprimento")
    return edges
def main():
    rows=[r for r in cabos() if r["centro_elemento_X_mm"]]
    # Cabos externos mais longos têm a menor liberdade de dobra.
    def endpoints(row):
        pol=row["polarizacao"]
        return np.array([float(row["x_placa_mm"])+DIV_X,float(row["y_placa_mm"]),DIV_B]),np.array([float(row["centro_elemento_X_mm"])+PIN,-PIN if pol=="A" else PIN,PLACA_Z])
    rows.sort(key=lambda r:-np.linalg.norm(endpoints(r)[0]-endpoints(r)[1]))
    routes={};occupied=[]
    for pol,sgn in [("A",-1),("B",1)]:
        h=sgn*N_Y
        pts=[[BASE+11,h,N_Z],[-245,h,N_Z],[-223,sgn*43,N_Z],[-46,sgn*43,-38],[DIV_X,h,-38],[DIV_X,h,DIV_B]]
        edges=fillet(pts); routes["IN_"+pol]=edges;occupied.append(sample(edges,.5))
    tree=cKDTree(np.vstack(occupied))
    for row in rows:
        s,e=endpoints(row);best=None
        reserves=[]
        for other in rows:
            if row is other:continue
            os,oe=endpoints(other)
            reserves.extend((oe[0],oe[1],z) for z in np.arange(-120,17,.75))
            reserves.extend((os[0],os[1],z) for z in np.arange(-17,DIV_B,.75))
        for sy in (-N_Y,N_Y):
            reserves.extend((DIV_X,sy,z) for z in np.arange(-72,DIV_B,.75))
        keep=cKDTree(reserves)
        for offset in [0,5,-5,10,-10,15,-15,21,-21,28,-28,36,-36,45,-45,55,-55,68,-68]:
            for frac in ([.5] if not offset else [.5,.25,.75]):
                try:edges=path_candidate(s,e,offset,frac)
                except ValueError:continue
                points=sample(edges,.75)
                if min(keep.query(points)[0])<3.85:continue
                near=np.where((points[:,2]>-9.8)&(points[:,2]<-.2)&(np.abs(points[:,1])>16.1)&(np.abs(points[:,1])<23.9)&(((points[:,0]>-250)&(points[:,0]<-26))|((points[:,0]>30)&(points[:,0]<260))))[0]
                if len(near):continue
                clearance=min(tree.query(points)[0]) if tree else 999
                if clearance<4.02:continue
                score=abs(offset)*.1+max(0,-70-min(points[:,2]))*.15
                if best is None or score<best[0]:best=(score,edges,points)
        if best is None:raise RuntimeError("sem rota para "+row["porta_divisor"])
        _,edges,p=best; routes[row["porta_divisor"]]=edges;occupied.append(p);tree=cKDTree(np.vstack(occupied))
    (SAIDA/"linhas_de_centro.json").write_text(json.dumps(routes,separators=(",",":")),encoding="utf8")
    with (SAIDA/"08_Gabarito_dos_cabos.csv").open("w",encoding="utf-8-sig",newline="") as out:
        writer=csv.writer(out,delimiter=";")
        writer.writerow(["Cabo","Ordem","Trecho","Comprimento_mm","Raio_eixo_mm","Angulo_graus",
                         "X_inicio","Y_inicio","Z_inicio","X_meio_arco","Y_meio_arco","Z_meio_arco","X_fim","Y_fim","Z_fim"])
        def fmt(v):return format(v,".4f").replace(".",",")
        for name,edges in sorted(routes.items()):
            for idx,(edge,d) in enumerate(zip(edges,lengths(edges)),1):
                arc=edge[0]=="A"
                writer.writerow([name,idx,"Arco" if arc else "Reto",fmt(d),fmt(R) if arc else "",fmt(math.degrees(d/R)) if arc else "",
                                 *map(fmt,edge[1]),*(map(fmt,edge[2]) if arc else [""]*3),*map(fmt,edge[-1])])
    for name,edges in routes.items():print(name,round(sum(lengths(edges)),2),round(min(sample(edges)[:,2]),1))
if __name__=="__main__":main()
