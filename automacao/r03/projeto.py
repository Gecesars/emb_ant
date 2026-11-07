"""Rede impressa de alimentação central para dois grupos de cinco elementos. Geometria em mm."""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import brentq
from shapely import affinity
from shapely.geometry import LineString, Point, box
from shapely.ops import substring, unary_union
from skrf import Frequency
from skrf.media.mline import MLine

LAMINADOS={"ZYF300CA-C":(2.94,.0016),"ZYF300CA-P":(3.0,.0018),
           "ZYF265D":(2.65,.0019),"ZYF255DA":(2.55,.0018)}
FREQUENCIAS=Frequency(5.09,5.25,17,"GHz")
PIN=2.50916841304063
PASSO=52.6
Z50=50.;Z2=50*math.sqrt(2);Z25=50*math.sqrt(2.5);Z5=50*math.sqrt(5)
SEAM=15.4
GAP=.5
GND_Z=-10.
RAIO=3.


def dimensionar(material,h):
    dk,df=LAMINADOS[material]
    def linha(w):
        return MLine(frequency=FREQUENCIAS,w=w/1000,h=h/1000,t=.000035,ep_r=dk,tand=df,
                     rho=1/5.8e7,rough=.5e-6,f_epr_tand=1e10)
    model={}
    for z in [Z50,Z2,Z25,Z5]:
        w=brentq(lambda w:linha(w).z0[8].real-z,.03,12)
        w=round(w,3);m=linha(w)
        model[z]=(w,float(np.pi/(2*m.beta[8])*1000),m)
    return model


def curvas(points,r=RAIO):
    """Polilinha arredondada. Arcos amostrados em passos de no máximo três graus."""
    points=np.array(points,dtype=float)
    verts=[points[0]]
    for a,b,c in zip(points,points[1:],points[2:]):
        u=(b-a)/np.linalg.norm(b-a);v=(c-b)/np.linalg.norm(c-b)
        turn=math.atan2(u[0]*v[1]-u[1]*v[0],u@v)
        if abs(turn)<1e-8:continue
        if abs(turn)>=math.pi-.01:raise ValueError("Retorno sem raio")
        tangent=r*math.tan(abs(turn)/2)
        p=b-u*tangent;q=b+v*tangent
        assert np.dot(p-verts[-1],u)>-.001,(p,verts[-1])
        center=p+math.copysign(r,turn)*np.array([-u[1],u[0]])
        angle=math.atan2(*(p-center)[::-1])
        for t in np.linspace(angle,angle+turn,max(3,int(abs(turn)*180/math.pi/3)+1)):
            verts.append(center+r*np.array([np.cos(t),np.sin(t)]))
        assert np.linalg.norm(verts[-1]-q)<1e-7
    verts.append(points[-1])
    return LineString(verts)


def routes(model):
    """P, P2 e P5 são pontos de divisão física, ambos os lados são desenhados por simetria."""
    row,hub,sub=31.5,25.5,16.
    runs=[]
    def add(start,end,pts,z=None):
        line=curvas(pts)
        runs.append((start,end,line,z))
        return line
    add("IN","P", [(-230,31),(-230,38.2),(0,38.2),(0,row)])
    for g,sgn in [("INF",-1),("SUP",1)]:
        cx=sgn*131.5
        add("P",g,[(0,row),(cx,row),(cx,hub)],Z2)
        trunk=curvas([(0,hub),(78.9,hub),(78.9,sub)])
        leaf=LineString([(78.9,sub),(105.2,PIN)])
        beta=lambda z:model[z][2].beta[8]/1000
        q=lambda z:model[z][1]
        phase_side=beta(Z50)*(trunk.length+leaf.length-q(Z25)-q(Z2))+beta(Z25)*q(Z25)+beta(Z2)*q(Z2)
        goal=(phase_side-beta(Z5)*q(Z5))/beta(Z50)+q(Z5)
        def meander(a):
            return curvas([(0,hub),(0,13.4),(a,13.4),(a,6.8),(0,6.8),(0,PIN)])
        leg=brentq(lambda a:meander(a).length-goal,20,60)
        center=affinity.translate(meander(leg),xoff=cx)
        runs.append((g,g+"3",center,Z5))
        for j,sign in [("L",-1),("R",1)]:
            tap=cx+sign*78.9
            add(g,g+j,[(cx,hub),(tap,hub),(tap,sub)],Z25)
            for dx,index in [(-26.3,1 if sign<0 else 4),(26.3,2 if sign<0 else 5)]:
                add(g+j,g+str(index),[(tap,sub),(tap+dx,PIN)],Z2)
    return runs


def outlines():
    left=box(-245,-41,SEAM-GAP/2,41)
    for s in [-1,1]:
        y=sorted((s*17,s*28))
        left=left.difference(box(-246,y[0],-224.5,y[1]))
    return {"Inferior":left,"Superior":box(SEAM+GAP/2,-41,245,41)}


def fixings():
    return {"Inferior":[(x,y) for x in (-228.5,-165.5,-34.5,7.5) for y in (-13.4,13.4)],
            "Superior":[(x,y) for x in (34.5,97.5,228.5) for y in (-13.4,13.4)]}


def layout(material,h):
    model=dimensionar(material,h);runs=routes(model);lands=[];edges=[]
    for start,end,l,z in runs:
        segments=[]
        if z:
            q=model[z][1]
            segments.append((substring(l,0,q),z))
            segments.append((substring(l,q,l.length),Z50))
        else:segments.append((l,Z50))
        for section,imp in segments:
            lands.append(section.buffer(model[imp][0]/2,cap_style="flat",join_style="round",quad_segs=8))
        edges.append(dict(de=start,para=end,trechos=[[round(sec.length,6),imp] for sec,imp in segments]))
    ports=[("IN",-230.,31.)]+[(half+str(i+1),cx+(i-2)*PASSO,PIN)
                              for half,cx in [("INF",-131.5),("SUP",131.5)] for i in range(5)]
    for _,x,y in ports:lands.append(Point(x,y).buffer(model[Z50][0]/2,quad_segs=16))
    copper=unary_union(lands).buffer(.00005).simplify(.001,preserve_topology=True)
    assert copper.geom_type=="Polygon" and len(copper.interiors)==0,(copper.geom_type,len(copper.interiors))
    top={"A":affinity.scale(copper,1,-1,origin=(0,0)),"B":copper}
    assert top["A"].distance(top["B"])>.4
    boards={}
    for side,outline in outlines().items():
        # A borda de cobre acaba 0,52 mm antes da emenda; cada fita transpõe o intervalo.
        sq=outline.buffer(-.52,join_style="mitre")
        g=dict(arquivo="R03_"+material.replace("-","_")+"_"+side,h=h,material=material,dk=LAMINADOS[material][0],
               df=LAMINADOS[material][1],origem_x=260,sinal_no_verso=True,outline=list(outline.exterior.coords)[:-1],
               outline_gnd=list(sq.exterior.coords)[:-1],half_x=245,half_y=41,
               ports=[],copper={},rotulos={},fixacao=fixings()[side],legenda="P1H R03 "+side.upper(),
               legenda_xy=[-130 if side=="Inferior" else 132,0],emenda_x=SEAM-GAP/2 if side=="Inferior" else SEAM+GAP/2)
        xedge=g["emenda_x"]
        x1,x2=sorted([xedge,xedge+(-3.5 if side=="Inferior" else 3.5)])
        g["mascara_emenda_gnd"]=[list(box(x1,s*31.5-7,x2,s*31.5+7).exterior.coords)[:-1] for s in (-1,1)]
        for pol,sign in [("A",-1),("B",1)]:
            cut=top[pol].intersection(sq)
            assert cut.geom_type=="Polygon" and not cut.interiors
            for x,y in g["fixacao"]:
                assert cut.distance(Point(x,y))>=3.05,(material,side,pol,x,y,cut.distance(Point(x,y)))
            g["copper"][pol]=list(cut.exterior.coords)[:-1]
            for name,x,y in ports:
                if not outline.contains(Point(x,y*sign)):continue
                key=pol+"_IN" if name=="IN" else pol+str(int(name[-1])+(5 if name.startswith("SUP") else 0))
                g["ports"].append([key,x,y*sign])
                g["rotulos"][key]=[key,x+4.0,sign*(abs(y)+2.5)]
        boards[side]=g
    widths={str(round(z,6)):dict(largura_mm=v[0],quarto_mm=v[1],atenuacao_dB_m=float(v[2].alpha[8]*8.685889638)) for z,v in model.items()}
    return boards,edges,widths


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trabalho",type=Path)
    parser.add_argument("--espessura",type=float,default=1.52)
    parser.add_argument("--revisao",default="R03")
    args=parser.parse_args()
    for mat in LAMINADOS:
        boards,edges,w=layout(mat,args.espessura)
        for side,g in boards.items():
            g["arquivo"]=g["arquivo"].replace("R03_",args.revisao+"_")
            g["legenda"]=g["legenda"].replace("R03",args.revisao)
            out=args.trabalho/mat/side;out.mkdir(parents=True,exist_ok=True)
            (out/"geometria.json").write_text(json.dumps(g,indent=1),encoding="utf8")
        (args.trabalho/mat/"linhas.json").write_text(json.dumps(dict(larguras=w,rede=edges),indent=1),encoding="utf8")
        print(mat,len(edges),"ramos",w["50.0"])
