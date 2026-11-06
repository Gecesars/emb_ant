"""Exportação e conferência de contornos fechados, em mm e sem compensação de ferramenta."""
import math
import ezdxf
from ezdxf.math import Vec2
from ezdxf import path
from shapely.geometry import Polygon
from dimensoes import *

def main():
    doc=ezdxf.new("R2010");doc.units=ezdxf.units.MM
    doc.layers.new("CORTE",dxfattribs={"color":7})
    m=doc.modelspace()
    def loop(points):
        m.add_lwpolyline([(p[0],p[1],p[2] if len(p)>2 else 0) for p in points],
                         format="xyb",close=True,dxfattribs={"layer":"CORTE"})
    loop(contorno_plano())
    for x in CENTROS:loop(slot(x,0,R_PASSA,PIN))
    for x,y in ref_bolts():m.add_circle((x,y),1.4,dxfattribs={"layer":"CORTE"})
    for y in (-N_Y,N_Y):loop(duplo_d(N_FLAT,y))
    filename=SAIDA/"04_Refletor_CORTE_1a1.dxf"
    doc.saveas(filename)
    back=ezdxf.readfile(filename);model=back.modelspace()
    assert not back.audit().has_errors and back.units==4 and len(model)==31
    loops=list(model.query("LWPOLYLINE"));assert len(loops)==13 and all(e.closed for e in loops)
    areas=[Polygon([(v.x,v.y) for v in path.make_path(e).flattening(.0001)]).area for e in loops]
    dxf_volume=(areas[0]-sum(areas[1:])-18*math.pi*1.4**2)*T
    import zipfile,xml.etree.ElementTree as ET
    # Checagem independente com a seção do arquivo nativo calculada no FreeCAD.
    import json
    data=json.loads((SAIDA/"verificacao.json").read_text())
    folded=data["volume_dobrado_mm3"]
    bendwidth=82+2*sum(b-a for a,b in TRECHOS)
    flat_volume=folded-T*math.pi/2*(.5-K)*T*bendwidth
    assert abs(flat_volume-dxf_volume)<.25,(flat_volume,dxf_volume)
    data.update({"volume_planificado_mm3":round(flat_volume,6),"dxf_contornos_fechados":31,"dxf_unidade":"mm",
                 "BA_90_mm":round(BA,6),"planificado_limites_X":[FIM_FLAT,TOPO],"modelo_dobrado_limites_X":[BASE-RO,TOPO]})
    (SAIDA/"verificacao.json").write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf8")
    doc.layers.new("EIXOS_DOBRA",dxfattribs={"color":1})
    def fold(a,b):m.add_line(a,b,dxfattribs={"layer":"EIXOS_DOBRA"})
    fold((BASE-BA/2,-41),(BASE-BA/2,41))
    for a,b in TRECHOS:
        for s in (-1,1):fold((a,s*(18+BA/2)),(b,s*(18+BA/2)))
    doc.saveas(SAIDA/"05_Refletor_marcacao_dobras.dxf")
    print("DXF_OK",len(model),round(dxf_volume,4),round(flat_volume,4))
if __name__=="__main__":main()
