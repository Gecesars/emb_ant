"""Variantes independentes de divisores/retornos; nao executa o HFSS."""
from pathlib import Path
import argparse,copy,json,math,shutil,hashlib
from shapely.geometry import Polygon,Point,LineString,mapping
from shapely.affinity import translate,scale
from shapely.ops import unary_union
from shapely import set_precision
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MP
from matplotlib.patches import PathPatch

REPO=Path(__file__).resolve().parents[3]
BASE=Path('D:/dev/EMBRAER/P2M21/R10_Quatro_Verticais')
ROOT=Path('D:/dev/EMBRAER/P2M21/R11_Divisor_Ajustes')

def build(name,params):
    folder=ROOT/name
    assert not folder.exists(), 'Preservar variante existente: '+str(folder)
    folder.mkdir(parents=True)
    if params.get('simetria',False):
        assert params.get('extra_A',0)==params.get('extra_B',0)
        assert params.get('upper',0)==params.get('lower',1.5)
        for attr in ['root_w','root_l','local_w','local_l']:
            assert params.get(attr+'_A',1)==params.get(attr+'_B',1),attr
    g=json.loads((BASE/'geometria.json').read_text())
    pitch=float(params.get('pitch',48.))
    assert 34.<=pitch<=54., 'Espacamento fora do estudo de quatro radiadores'
    centers=[v*pitch for v in [-1.5,-.5,.5,1.5]]
    g.update(passo_vertical_mm=pitch,centros_HFSS_X_mm=centers)
    g['distancia_pcb_refletor_mm']=float(params.get('pcb_z',16.61))
    if params.get('contorno_centrado',False):
        half_x=float(params.get('board_half_x',92.))
        g['outline']=[[-half_x,-35.],[half_x,-35.],[half_x,35.],[-half_x,35.]]
        g['placa_largura_altura_mm']=[70.,2*half_x]
        g['refletor_planejado_mm']=[90.,2*half_x+16,2.]
    art=json.loads((REPO/'automacao/P1H/KiCad_Antenas/elemento_hfss.json').read_text())
    p=art['ports']['B'][0];lines=g['lines']
    w50=lines['50']['w_mm'];w70=lines[str(math.sqrt(2)*50)]['w_mm'];l70=lines[str(math.sqrt(2)*50)]['l90_mm']
    lands=[];vias=[];traces=[];inputs=[]
    for i,cx in enumerate(centers,1):
        for land in art['lands']:
            net=land['net'] if land['net'] in ('SIG_A','SIG_B','RET_A','RET_B') else 'E%d_'%i+land['net']
            lands.append(dict(layer=land['layer'],net=net,shape=translate(Polygon(land['outer'],land['holes']),cx,0)))
        vias.extend([[x+cx,y] for x,y in art['vias']])
    ground_ribbons={};signals={}
    for pol in 'AB':
        sy=-1 if pol=='A' else 1
        yr=sy*params.get('root_y',32.);yl=sy*params.get('local_y',18.);xr=p
        signal=[Point(xr,yr).buffer(.95,quad_segs=48)]
        ground=[Point(xr,yr).buffer(2.65,quad_segs=48)]
        for dx in [-pitch,pitch]:
            s=1 if dx>0 else -1
            pts70=[(xr,yr),(xr+s*l70*params.get('root_l_'+pol,1),yr)]
            pts50=[pts70[-1],(xr+dx,yr),(xr+dx,yl)]
            root_extra=params.get('root_extra',0.)
            if root_extra>0:
                # Acrescimo igual nos dois troncos e nas polarizacoes: preservar
                # comprimento ao reduzir o passo, sem atrasos A/B distintos.
                xa=pts70[-1][0]+s*2;xb=xa+s*5;ym=yr-sy*root_extra/2
                pts50=[pts70[-1],(xa,yr),(xa,ym),(xb,ym),(xb,yr),(xr+dx,yr),(xr+dx,yl)]
            signal.extend([LineString(pts70).buffer(w70*params.get('root_w_'+pol,1)/2,cap_style='square',join_style='mitre'),
                LineString(pts50).buffer(w50/2,cap_style='square',join_style='mitre')])
            ground.append(LineString(pts70+pts50[1:]).buffer(params.get('root_ground',params['ground'])/2,join_style='mitre'))
            traces.append(dict(polarizacao=pol,tipo='raiz',grupo=dx,linha70=pts70,linha50=pts50))
            for sign in [-1,1]:
                cx=dx+sign*pitch/2;tx=dx+p
                # Meandro com acrescimo de comprimento 2*depth. Preserva a transicao do radiador.
                extra=params.get('extra_'+pol,0)+(params.get('upper',0) if sign>0 else params.get('lower',1.5))
                depth=extra/2
                lw=w70*params.get('local_w_'+pol,1);ll=l70*params.get('local_l_'+pol,1)
                taper=params.get('outer_amplitude',1.)
                if taper!=1.:
                    # Sintese nominal com cargas de 50 ohms; a divisao efetiva sera determinada pelo HFSS.
                    from skrf import Frequency
                    from skrf.media.mline import MLine
                    from scipy.optimize import brentq
                    z_branch=50*(1+taper*taper)/(taper*taper if abs(cx)>pitch else 1.)
                    zq=math.sqrt(50*z_branch)
                    def line(w):return MLine(frequency=Frequency(5.17,5.17,1,'GHz'),w=w/1000,h=.00076,t=.000035,ep_r=3.66,tand=.0037,diel='frequencyinvariant',rho=1/5.8e7,rough=.5e-6)
                    lw=brentq(lambda w:line(w).z0[0].real-zq,.05,4)*params.get('local_w_'+pol,1)
                    ll=math.pi/(2*line(lw).beta[0])*1000*params.get('local_l_'+pol,1)
                q70=[(tx,yl),(tx+sign*ll,yl)]
                if depth>1e-9:
                    ym=yl+sy*depth
                    q50=[q70[-1],(tx+sign*(ll+1),yl),(tx+sign*(ll+1),ym),
                        (tx+sign*(ll+5),ym),(tx+sign*(ll+5),yl),(cx+p,yl),(cx+p,sy*p)]
                else:q50=[q70[-1],(cx+p,yl),(cx+p,sy*p)]
                signal.extend([LineString(q70).buffer(lw/2,cap_style='square',join_style='mitre'),
                    LineString(q50).buffer(w50/2,cap_style='square',join_style='mitre')])
                full=q70+q50[1:]
                if 'terminal_ground' in params:
                    stop=(cx+p,sy*(p+params.get('terminal_length',6.)))
                    ground.append(LineString(full[:-1]+[stop]).buffer(params['ground']/2,cap_style='flat',join_style='mitre'))
                    ground.append(LineString([stop,full[-1]]).buffer(params['terminal_ground']/2,join_style='mitre'))
                else:ground.append(LineString(full).buffer(params['ground']/2,join_style='mitre'))
                traces.append(dict(polarizacao=pol,tipo='local',cx=cx,linha70=q70,linha50=q50,largura_transformador_mm=lw,comprimento_mm=LineString(q70+q50[1:]).length))
        obstacles=unary_union([l['shape'] for l in lands if l['layer']=='B' and l['net']!='RET_'+pol])
        if params.get('rails',False):
            from shapely.geometry import box
            rw=params.get('rail_width',6.)
            ground.append(box(-84.,yl-rw/2,84.,yl+rw/2))
            ground.append(LineString([(xr,yr),(xr,yl)]).buffer(params.get('rail_link_width',6.)/2,join_style='mitre'))
        if params.get('lateral_planes',False):
            from shapely.geometry import box
            yi=params.get('plane_inner_y',14.5)
            ground.append(box(-89.,-34.8,89.,-yi) if pol=='A' else box(-89.,yi,89.,34.8))
        # Os retornos novos respeitam uma separacao central de 0,2 mm;
        # nao unir as duas polarizacoes ao ampliar as faixas de terra.
        from shapely.geometry import box
        half=box(-100,-40,100,-.1) if pol=='A' else box(-100,.1,100,40)
        ground_ribbons[pol]=unary_union(ground).intersection(half).difference(obstacles.buffer(.2,join_style='mitre'))
        signals[pol]=unary_union(signal)
        inputs.append(dict(name=pol,x=xr,y=yr,sig='SIG_'+pol,ret='RET_'+pol))
    symmetry={}
    if params.get('simetria',False):
        symmetry['diferenca_area_sinais_novos_mm2']=signals['A'].symmetric_difference(scale(signals['B'],xfact=1,yfact=-1,origin=(0,0))).area
        assert symmetry['diferenca_area_sinais_novos_mm2']<1e-8,symmetry
        # Mesma faixa de retorno em ambas as polarizacoes, respeitando os
        # recortes necessarios nas transicoes originais dos radiadores.
        common=ground_ribbons['A'].intersection(scale(ground_ribbons['B'],xfact=1,yfact=-1,origin=(0,0)))
        ground_ribbons['A']=common;ground_ribbons['B']=scale(common,xfact=1,yfact=-1,origin=(0,0))
        symmetry['diferenca_area_retornos_novos_mm2']=ground_ribbons['A'].symmetric_difference(scale(ground_ribbons['B'],xfact=1,yfact=-1,origin=(0,0))).area
        symmetry['escopo']='Divisores e faixas de retorno acrescentados espelhados em Y=0; cobre e vias originais dos radiadores preservados.'
    for pol in 'AB':
        ip=next(x for x in inputs if x['name']==pol);pt=Point(ip['x'],ip['y'])
        gr=ground_ribbons[pol].intersection(Polygon(g['outline']).buffer(-.2)).difference(pt.buffer(1.516,quad_segs=96))
        lands.extend([dict(layer='F',net='SIG_'+pol,shape=signals[pol]),dict(layer='B',net='RET_'+pol,shape=gr),
            dict(layer='B',net='SIG_'+pol,shape=pt.buffer(.8,quad_segs=48).difference(pt.buffer(.55,quad_segs=48)))])
    merged=[]
    for layer,net in sorted({(x['layer'],x['net']) for x in lands}):
        poly=set_precision(unary_union([x['shape'] for x in lands if x['layer']==layer and x['net']==net]),1e-6).simplify(1e-6,preserve_topology=True)
        assert poly.is_valid and Polygon(g['outline']).contains(poly),(layer,net)
        merged.append(dict(layer=layer,net=net,shape=poly))
    shorts=[];clear=100.
    for i,a in enumerate(merged):
        for b in merged[i+1:]:
            if a['layer']!=b['layer'] or a['net']==b['net']:continue
            clear=min(clear,a['shape'].distance(b['shape']))
            if a['shape'].intersection(b['shape']).area>1e-8:shorts.append([a['net'],b['net']])
    assert not shorts and clear>=.15-1e-5,(shorts,clear)
    g.update(lands=[dict(layer=x['layer'],net=x['net'],geometry=mapping(x['shape'])) for x in merged],inputs=inputs,
        vias=vias,traces=traces,estado='VARIANTE_PREPARADA',parametros=params,shorts=shorts,folga_planar_minima_mm=clear,simetria=symmetry)
    g.pop('raizes',None);g.pop('ramos',None)
    (folder/'geometria.json').write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    cfg=json.loads((BASE/'configuracao.json').read_text());cfg.update(max_delta_s=.05,fonte=str(BASE/'geometria.json'),fonte_sha256=hashlib.sha256((BASE/'geometria.json').read_bytes()).hexdigest(),variante=name,parametros=params,refinamento_adaptativo_percent=params.get('adapt',20))
    cfg['malha']='Classic automatico 5; sem MeshLink, sem operacoes locais e sem LambdaRefine; adaptacao durante solve '+str(params.get('adapt',20))+'%.'
    cfg['espacamento_vertical_mm']=pitch
    cfg['distancia_face_inferior_laminado_ao_refletor_mm']=g['distancia_pcb_refletor_mm']
    if params.get('contorno_centrado',False):cfg.update(placa_largura_altura_mm=g['placa_largura_altura_mm'],refletores_mm=g['refletor_planejado_mm'])
    (folder/'configuracao.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    shutil.copy2(BASE/'HFSS_14nucleos.acf',folder/'HFSS_14nucleos.acf')
    for file in ['criar_cad.py','criar_hfss.py']:
        code=(BASE/file).read_text(encoding='utf-8')
        import re
        root_expr='Path('+repr(folder.as_posix())+')' if file=='criar_cad.py' else repr(folder.as_posix())
        code,n=re.subn(r'^root=.*$',lambda m:'root='+root_expr,code,flags=re.M);assert n==1
        if file=='criar_cad.py':
            assert code.count('z0=16.61')==1
            code=code.replace('z0=16.61',"z0=g.get('distancia_pcb_refletor_mm',16.61)")
        if file=='criar_hfss.py':
            code=code.replace("'MaxDeltaS:=',.04","'MaxDeltaS:=',.05").replace('max_delta_s=.04','max_delta_s=.05')
            code=code.replace("'PercentRefinement:=',20","'PercentRefinement:=',"+str(params.get('adapt',20)))
            code=code.replace("'BasisOrder:=',-1","'BasisOrder:=',"+str(params.get('basis_order',-1)))
            if params.get('diagnostico_campos',False):code=code.replace("'SaveRadFieldsOnly:=',True","'SaveRadFieldsOnly:=',False")
        (folder/file).write_text(code,encoding='utf-8')
    code=(REPO/'projetos/P2M21/automacao/quatro_elementos_resolver.py').read_text(encoding='utf-8')
    code,n=re.subn(r'^root=.*$',lambda m:'root='+repr(folder.as_posix()),code,flags=re.M);assert n==1
    code=code.replace('MaxDeltaS=0.04','MaxDeltaS=0.05').replace('delta_s=.04','delta_s=.05')
    if params.get('diagnostico_campos',False):
        code=code.replace('sources(sol);p.Save();oDesktop.CloseProject(p.GetName())',
            "sources(sol)\n    exec(compile(open(os.path.join(root,'sondas.py')).read(),'sondas.py','exec'))\n    p.Save();oDesktop.CloseProject(p.GetName())")
        shutil.copy2(Path(__file__).with_name('quatro_ajustar_sondas.py'),folder/'sondas.py')
    (folder/'resolver.py').write_text(code,encoding='utf-8')
    (folder/'qualificacao.json').write_text(json.dumps(dict(estado='AGUARDA_CAD',parametros=params),indent=2)+'\n',encoding='utf-8')
    def patch(poly,ax,color):
        if poly.geom_type=='MultiPolygon':
            for piece in poly.geoms:patch(piece,ax,color)
            return
        from shapely.geometry.polygon import orient
        poly=orient(poly,sign=1);v=[];codes=[]
        for ring in [poly.exterior]+list(poly.interiors):
            pts=list(ring.coords);v += [(y,x) for x,y in pts];codes += [MP.MOVETO]+[MP.LINETO]*(len(pts)-2)+[MP.CLOSEPOLY]
        ax.add_patch(PathPatch(MP(v,codes),fc=color,ec='none'))
    fig,axs=plt.subplots(1,2,figsize=(9,10))
    for ax,layer in zip(axs,'FB'):
        for l in merged:
            if l['layer']==layer:patch(l['shape'],ax,'#176a9b' if l['net']=='SIG_A' else '#d17b26' if l['net']=='SIG_B' else '#6c8589')
        ax.set(xlim=(-35,35),ylim=(g['outline'][0][0],g['outline'][2][0]),xlabel='Y horizontal (mm)',ylabel='X vertical (mm)',title=layer+'.Cu');ax.set_aspect('equal');ax.grid(alpha=.15)
    fig.suptitle(name+' | dois divisores 1:4 | quatro radiadores',fontsize=12);fig.tight_layout(rect=(0,0,1,.96));fig.savefig(folder/'layout.png',dpi=160);plt.close(fig)
    print(json.dumps(dict(pasta=str(folder),folga_mm=clear,parametros=params),indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('name');parser.add_argument('--params',required=True)
    args=parser.parse_args();build(args.name,json.loads(Path(args.params).read_text()))
