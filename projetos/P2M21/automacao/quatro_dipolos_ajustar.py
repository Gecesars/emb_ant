"""Varia apenas as partes externas dos radiadores, preservando feeds e vias."""
import copy
from shapely.geometry import Polygon,box

def morph(art,factor,protected=4.):
    assert .98<=factor<=1.02
    out=copy.deepcopy(art)
    def coord(x):return x if abs(x)<=protected else (1 if x>0 else -1)*(protected+(abs(x)-protected)*factor)
    def ring(points):
        pts=[tuple(p) for p in points]
        if pts[0]!=pts[-1]:pts.append(pts[0])
        result=[]
        for a,b in zip(pts[:-1],pts[1:]):
            ts={0.,1.}
            for axis in [0,1]:
                if b[axis]!=a[axis]:
                    for cut in [-protected,protected]:
                        t=(cut-a[axis])/(b[axis]-a[axis])
                        if 0<t<1:ts.add(t)
            for t in sorted(ts)[:-1]:result.append([coord(a[0]+t*(b[0]-a[0])),coord(a[1]+t*(b[1]-a[1]))])
        result.append(result[0]);return result
    audit=[]
    for src,dst in zip(art['lands'],out['lands']):
        if src['layer']!='B' or src['net'] not in ['RET_A','RET_B','Q2','Q3']:continue
        before=Polygon(src['outer'],src['holes'])
        dst['outer']=ring(src['outer']);dst['holes']=[ring(h) for h in src['holes']]
        after=Polygon(dst['outer'],dst['holes']);assert after.is_valid
        protected_error=before.intersection(box(-protected,-protected,protected,protected)).symmetric_difference(after.intersection(box(-protected,-protected,protected,protected))).area
        assert protected_error<1e-9
        audit.append(dict(net=src['net'],area_antes_mm2=before.area,area_depois_mm2=after.area,area_alterada_mm2=before.symmetric_difference(after).area,nucleo_inalterado_erro_mm2=protected_error))
    assert art['ports']==out['ports'] and art['vias']==out['vias']
    return out,dict(fator=factor,nucleo_protegido_meia_largura_mm=protected,contornos=audit,nota='Fator aplicado somente a distancia alem de +/-4mm; nao e uma escala global do dipolo nem previsao de deslocamento da ressonancia.')

def plot_change(before_file,after_file,output_file):
    from pathlib import Path
    import json
    from shapely.geometry import shape
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    before=json.loads(Path(before_file).read_text(encoding='utf-8'))
    after=json.loads(Path(after_file).read_text(encoding='utf-8'))
    fig,axs=plt.subplots(1,2,figsize=(10,5.5));cx=-24.
    loop=shape(next(l['geometry'] for l in before['lands'] if l['net']=='E2_Q2'))
    tip=max(loop.exterior.coords,key=lambda q:q[1])
    for data,color,style,label in [(before,'#6a6a6a','--','R12'),(after,'#087fbc','-','Dipolos modificados')]:
        first=True
        for land in data['lands']:
            if land['layer']!='B':continue
            geom=shape(land['geometry']);polys=list(geom.geoms) if geom.geom_type=='MultiPolygon' else [geom]
            for poly in polys:
                for ring in [poly.exterior]+list(poly.interiors):
                    coords=list(ring.coords);xx=[p[1] for p in coords];yy=[p[0]-cx for p in coords]
                    axs[0].plot(xx,yy,c=color,ls=style,lw=.7,label=label if first else None);first=False
                    if land['net']=='E2_Q2':axs[1].plot(xx,yy,c=color,ls=style,lw=1.4)
    axs[0].add_patch(Rectangle((-4,-4),8,8,fill=False,ec='green',ls=':',lw=1.2))
    axs[0].set(xlim=(-15,15),ylim=(-15,15),title='Um radiador — cobre traseiro');axs[0].legend(fontsize=8,loc='lower left')
    axs[1].set(xlim=(tip[1]-.4,tip[1]+.4),ylim=(tip[0]-cx-.4,tip[0]-cx+.4),title='Detalhe de uma extremidade')
    for ax in axs:ax.set_aspect('equal');ax.grid(alpha=.2);ax.set_xlabel('Y (mm)');ax.set_ylabel('X relativo ao radiador (mm)')
    factor=after['parametros'].get('dipolo_escala_externa',1.)
    fig.suptitle(f'Variação geométrica dos dipolos — fator externo {factor:.3f}\nRegião central de 8 × 8 mm, conexões dos radiadores e vias preservadas')
    fig.tight_layout(rect=(0,0,1,.86));fig.savefig(output_file,dpi=180);plt.close(fig)
