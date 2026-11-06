from pathlib import Path
import json, math
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
p=Path(__file__).resolve().parent
g={"h":1.52,"width":.220,"l_arm":10.076,"r_pad":.86,"r_out":15.2,"w50":3.866,
   "half_x":19.5,"half_y":39.0,"ports":[],"copper":{}}
for pol,cy in [("A",-19.25),("B",19.25)]:
    copper=[Point(0,cy).buffer(g["r_pad"],quad_segs=12)]
    g["ports"].append([pol+"_IN",0,cy])
    outs=[]
    for i in range(10):
        ang=math.radians(i*36+18)
        def pt(r):return (r*math.cos(ang),cy+r*math.sin(ang))
        transition=g["r_pad"]+g["l_arm"]
        copper.append(LineString([pt(.6),pt(transition)]).buffer(g["width"]/2,cap_style="flat"))
        copper.append(LineString([pt(transition-.001),pt(g["r_out"])]).buffer(g["w50"]/2,cap_style="flat"))
        x,y=pt(g["r_out"])
        copper.append(Point(x,y).buffer(g["w50"]/2,quad_segs=12))
        outs.append((x,y))
    for i,(x,y) in enumerate(sorted(outs,key=lambda xy:(round(xy[0],4),xy[1])),1):g["ports"].append([pol+str(i),x,y])
    poly=unary_union(copper)
    assert poly.geom_type=="Polygon" and len(poly.interiors)==0
    g["copper"][pol]=list(poly.exterior.coords)[:-1]
(p/"geometria.json").write_text(json.dumps(g))
