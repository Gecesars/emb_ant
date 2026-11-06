"""Dimensionar duas redes simétricas em PTFE para alimentar metades da coluna."""
import argparse
import json
import math
from pathlib import Path

from scipy.optimize import brentq
from shapely.geometry import LineString, Point
from shapely.ops import unary_union
from skrf import Frequency
from skrf.media.mline import MLine


def microstrip(ohms):
    frequency = Frequency(5.17, 5.17, 1, "GHz")
    def line(w):
        return MLine(frequency=frequency, w=w/1000, h=.00152, t=.000035, ep_r=2.94, tand=.0016,
                     rho=1/5.8e7, rough=.5e-6)
    w = brentq(lambda w: line(w).z0[0].real-ohms,.03,10)
    return round(w,3), round(math.pi/(2*line(w).beta[0])*1000,3)


def layout(n,folder):
    width50,_ = microstrip(50)
    width,quarter = microstrip(50*math.sqrt(n))
    rpad, radius = .86, 15.2
    geometry = dict(arquivo=f"R02_Duplo_1x{n}", legenda=f"P1H 2 x 1:{n}", h=1.52,
                    width=width,l_arm=quarter,r_pad=rpad,r_out=radius,w50=width50,
                    half_x=19.5,half_y=39.0,ports=[],copper={})
    if n==5:
        # Janela usinada para os dois coaxiais que atravessam a PCB rumo ao elemento central.
        axis=LineString([(0,-2.50916841304063),(0,2.50916841304063)])
        geometry["janela"]=list(axis.buffer(2.5,quad_segs=16).exterior.coords)[:-1]
        geometry["janela_sem_cobre"]=list(axis.buffer(3.0,quad_segs=16).exterior.coords)[:-1]
    for pol,sign in [("A",-1),("B",1)]:
        cy=sign*19.25
        geometry["ports"].append([pol+"_IN",0.,cy])
        lands=[Point(0,cy).buffer(rpad,quad_segs=12)]
        pads=[]
        for i in range(n):
            angle=math.radians(i*360/n+(18 if n==5 else 0))
            def at(r):
                return (r*math.cos(angle),cy+sign*r*math.sin(angle))
            transition=rpad+quarter
            lands.extend([LineString([at(.6),at(transition)]).buffer(width/2,cap_style="flat"),
                          LineString([at(transition-.001),at(radius)]).buffer(width50/2,cap_style="flat"),
                          Point(*at(radius)).buffer(width50/2,quad_segs=12)])
            pads.append(at(radius))
        for i,(x,y) in enumerate(sorted(pads,key=lambda p:round(p[0],5)),1):
            geometry["ports"].append([pol+str(i),x,y])
        copper=unary_union(lands)
        assert copper.geom_type=="Polygon" and not copper.interiors
        geometry["copper"][pol]=list(copper.exterior.coords)[:-1]
    folder.mkdir(parents=True,exist_ok=True)
    (folder/"geometria.json").write_text(json.dumps(geometry,indent=1),encoding="utf8")
    return geometry


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("destino",type=Path)
    args=ap.parse_args()
    for n in [2,5]:
        g=layout(n,args.destino/f"1x{n}")
        print(g["arquivo"],"W =",g["width"],"L =",g["l_arm"],"mm")
