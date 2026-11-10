"""Desenho dimensional dos trechos de casamento a partir da geometria real."""
import argparse,json,math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import shape,LineString

def draw(folder):
    folder=Path(folder);g=json.loads((folder/'geometria.json').read_text())
    p=g['parametros'];nom=g['lines'][str(math.sqrt(2)*50)]
    fig,axes=plt.subplots(1,2,figsize=(12,6.8))
    rows=[]
    for ax,kind,prefix,title in zip(axes,['raiz','local'],['root','local'],['Primeiro estágio — próximo à entrada','Segundo estágio — próximo ao radiador']):
        trace=next(t for t in g['traces'] if t['tipo']==kind and t['polarizacao']=='A' and (t.get('grupo',0)>0 if kind=='raiz' else t['cx']>48))
        line=LineString(trace['linha70']);x0,y0=line.coords[0];x1,y1=line.coords[-1]
        width=nom['w_mm']*p.get(prefix+'_w_A',1.)
        post=g['lines']['50']['w_mm']*p.get(prefix+'_post_w_A',1.)
        for land in g['lands']:
            if land['layer']!='F':continue
            geom=shape(land['geometry']);polys=[geom] if geom.geom_type=='Polygon' else geom.geoms
            for poly in polys:
                x,y=poly.exterior.xy;ax.fill(x,y,color='#d5dde4',zorder=1)
                for hole in poly.interiors:
                    x,y=hole.xy;ax.fill(x,y,color='white',zorder=2)
        caps='flat' if kind=='raiz' and p.get('root_flat_sections',False) else 'square'
        q=line.buffer(width/2,cap_style=caps,join_style='mitre');x,y=q.exterior.xy
        ax.fill(x,y,color='#156c9c',zorder=3,label='Trecho transformador')
        ax.annotate('',xy=(x1,y0-2.3),xytext=(x0,y0-2.3),arrowprops=dict(arrowstyle='<->',color='#23313d'))
        ax.text((x0+x1)/2,y0-3.2,f'L = {line.length:.3f} mm',ha='center',va='top',fontsize=11)
        ax.annotate(f'W = {width:.3f} mm',xy=((x0+x1)/2,y0),xytext=((x0+x1)/2,y0+4),ha='center',arrowprops=dict(arrowstyle='->'),fontsize=11)
        extra=trace.get('secoes_adicionais',[]);xmax=max(x0,x1)
        for sec,color in zip(extra,['#c67b24','#378657','#8655a1']):
            path=LineString(sec['linha']);poly=path.buffer(sec['largura_mm']/2,cap_style=caps)
            xx,yy=poly.exterior.xy;ax.fill(xx,yy,color=color,zorder=3)
            a,b=path.coords[0][0],path.coords[-1][0];xmax=max(xmax,a,b)
            ax.text((a+b)/2,y0-3.5,f"S{sec['indice']}\nL {path.length:.3f}\nW {sec['largura_mm']:.3f}",ha='center',va='top',fontsize=9)
        ax.text(.03,.03,f'Após as seções: W = {post:.3f} mm',transform=ax.transAxes,fontsize=10,bbox=dict(facecolor='white',edgecolor='#aaaaaa'))
        ax.set(xlim=(min(x0,x1)-4,xmax+4),ylim=(y0-10 if extra else y0-7,y0+7),xlabel='X vertical da antena (mm)',ylabel='Y horizontal (mm)',title=title)
        ax.set_aspect('equal');ax.grid(alpha=.18)
        rows.append(dict(estagio=kind,largura_mm=width,comprimento_mm=line.length,secoes_adicionais=extra,largura_segmento_seguinte_mm=post))
    fig.suptitle('Dimensões dos transformadores de impedância\n'+folder.name+' | cobre da face F.Cu',fontsize=14)
    fig.text(.5,.05,'Mesmas dimensões nas polarizações A/B e nos ramos equivalentes.\nCotas obtidas do modelo; a imagem não substitui os arquivos de fabricação.',ha='center',fontsize=11)
    fig.tight_layout(rect=[0,.13,1,.91]);fig.savefig(folder/'transformadores_detalhe.png',dpi=180);plt.close(fig)
    (folder/'dimensoes_transformadores.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(rows,ensure_ascii=False))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('pasta');args=a.parse_args();draw(args.pasta)
