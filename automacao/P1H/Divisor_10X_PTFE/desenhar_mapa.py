"""Vista das duas redes e numeração dos cabos em coordenadas da PCB."""
from pathlib import Path
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Circle,FancyBboxPatch
root=Path(__file__).resolve().parent
g=json.loads((root/"geometria.json").read_text())
fig,ax=plt.subplots(figsize=(9.1,4.9))
fig.subplots_adjust(left=.035,right=.965,bottom=.11,top=.82)
fig.text(.055,.925,"Divisor radial para as duas polarizações",fontsize=19,weight="bold",color="#162b38")
fig.text(.056,.858,"Vista pelo lado das trilhas   |   ZYF300CA-C   |   39 × 78 mm",fontsize=11,color="#425864")
# Rotate the artwork in plane, keeping the source and numbering unchanged.
def pos(x,y):return y,-x
ax.add_patch(FancyBboxPatch((-39,-19.5),78,39,boxstyle="round,pad=0,rounding_size=.4",facecolor="#264c4b",edgecolor="#173536"))
for pol,coords in g["copper"].items():
    ax.add_patch(Polygon([pos(*pt) for pt in coords],closed=True,facecolor="#efbd68",edgecolor="#e6ad52",linewidth=.5))
for n,x,y in g["ports"]:
    X,Y=pos(x,y);is_input=n.endswith("IN")
    ax.add_patch(Circle((X,Y),.51,facecolor="#172c32",edgecolor="#cda761",lw=.45))
    if is_input:
        ny=Y+2.6;nx=X
    else:
        cx=-19.25 if n.startswith("A") else 19.25
        nx=cx+1.18*(X-cx);ny=1.18*Y
    ax.text(nx,ny,n.replace("_IN"," IN"),color="white",fontsize=7.7,weight="bold",ha="center",va="center")
ax.set_aspect("equal");ax.set_xlim(-40.5,40.5);ax.set_ylim(-20.5,20.5);ax.axis("off")
fig.text(.056,.056,"A1–A10 e B1–B10 seguem a coluna da antena de −X para +X. Os cabos entram pelo lado do plano de terra.",fontsize=9,color="#344854")
fig.savefig(root/"mapa_divisor.png",dpi=160,facecolor="white")
