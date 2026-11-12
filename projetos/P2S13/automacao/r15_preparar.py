"""C09 c01: somente as duas secoes comuns; portas, placa e cabos preservados."""
from pathlib import Path
import json,shutil,hashlib,os
import numpy as np
from shapely.geometry import Point,Polygon,box
from shapely.ops import unary_union
from skrf.media import MLine
import skrf as rf
BASE=Path('D:/dev/EMBRAER/P2S13/R14_Compacto_Simetrico_SemRadome/c00')
ROOT=Path('D:/dev/EMBRAER/P2S13/R15_Casamento_C09');CASE=Path(os.environ.get('P2S13_R15_CASE',str(ROOT/'c01')));DIV=CASE/'divisor'
assert not (DIV/'Divisor_Duplo3.aedt').exists() and not (DIV/'Divisor_Duplo3.FCStd').exists()
DIV.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
dc=read(BASE/'divisor/configuracao.json');old=json.loads(json.dumps(dc));q=read(Path(os.environ.get('P2S13_MODEL_DEST',str(ROOT)))/'guia_passiva.json')['candidato']
w1,w2,l1=[round(q[k],6) for k in ['W1_mm','W2_mm','L1_mm']];R=dc['parametros']['comprimento_por_ramal_mm'];l2=R-l1
widths=[w1,w2];lengths=[l1,l2]
media=[MLine(frequency=rf.Frequency(5.17,5.17,1,'ghz'),w=w/1000,h=.00152,t=.000035,ep_r=2.94,tand=.0016,rho=1/5.8e7,diel='frequencyinvariant',z0_port=50) for w in widths]
zs=[float(m.z0[0].real) for m in media];phases=[float(m.beta[0]*l/1000*180/np.pi) for m,l in zip(media,lengths)]
signals={};traces=[];shapes=[];ports={p['name']:p for p in dc['portas']}
for pol in 'AB':
    center=np.array([ports['IN_'+pol][k] for k in ['x','y']]);parts=[Point(*center).buffer(.65,quad_segs=24)]
    for cell in ['R1','R2','R3']:
        end=np.array([ports[cell+'_'+pol][k] for k in ['x','y']]);u=(end-center)/R;n=np.array([-u[1],u[0]]);assert abs(np.linalg.norm(u)-1)<1e-12
        contour=[(0,-w1/2),(l1,-w1/2),(l1,-w2/2),(R,-w2/2),(R,w2/2),(l1,w2/2),(l1,w1/2),(0,w1/2)]
        parts.extend([Polygon([center+x*u+y*n for x,y in contour]),Point(*end).buffer(.65,quad_segs=24)])
        split=center+l1*u
        for j,(a,b) in enumerate([(center,split),(split,end)]):
            traces.append(dict(name=pol+'_'+cell+'_T%d'%(j+1),points=[a.tolist(),b.tolist()],Z_ohm=zs[j],width_mm=widths[j],length_mm=lengths[j],phase_nominal_graus=phases[j]))
    raw=unary_union(parts);assert raw.is_valid and raw.geom_type=='Polygon'
    sh=Polygon([(round(x,8),round(y,8)) for x,y in raw.exterior.coords],[[ (round(x,8),round(y,8)) for x,y in h.coords] for h in raw.interiors]).simplify(1e-7,preserve_topology=True)
    assert sh.is_valid and raw.hausdorff_distance(sh)<2e-7
    ox,oy=dc['board_origin'];bx,by=dc['board'];assert box(ox,oy,ox+bx,oy+by).contains(sh)
    signals[pol]=dict(exterior=list(sh.exterior.coords),holes=[list(h.coords) for h in sh.interiors]);shapes.append(sh)
assert shapes[0].distance(shapes[1])>.2
dc.update(revisao='C09_Casamento_'+CASE.name,signals=signals,traces=traces,topology='Duas trifurcacoes sem resistores; tres ramais identicos de duas secoes ajustadas, conexoes fixas.',
    parametros=dict(W1_mm=w1,W2_mm=w2,L1_mm=l1,L2_mm=l2,Z1_ohm=zs[0],Z2_ohm=zs[1],comprimento_por_ramal_mm=R,distancia_centros_AB_mm=38.2))
assert dc['portas']==old['portas'] and dc['board']==old['board'] and dc['board_origin']==old['board_origin']
save(DIV/'configuracao.json',dc)
save(DIV/'igualdade_ramais.json',dict(comprimentos_mm=[R]*6,larguras_mm=widths,secoes_mm=lengths,fase_nominal_graus=[sum(phases)]*6,portas_preservadas=True,simetria_nominal=True,notas='Fase eletrica real sera medida no HFSS; valores nominais de linhas nao sao criterio EM.'))
c=read(BASE/'configuracao.json');c.update(revisao='R15_C09_'+CASE.name,fonte_divisor=str(DIV),antena_reutilizada=str(BASE/'antena'),fontes_antena_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [BASE/'antena/PCB_SemCabos.aedt',BASE/'antena/centro.s6p']},
    alteracoes_autorizadas='12nov: ajustar duas secoes iguais do C09; max6/DeltaS0.05/14cores; semradome/cabos3D.',modelos_RF_ativos=dict(antena=str(BASE/'antena/PCB_SemCabos.aedt'),divisor='divisor/Divisor_Duplo3.aedt',circuito='circuito/C09_Ajuste_Nexxim.aedt'))
save(CASE/'configuracao.json',c)
for p in [CASE,DIV]:shutil.copy2(BASE/'HFSS_14nucleos.acf',p/'HFSS_14nucleos.acf')
save(CASE/'alteracoes.json',dict(antes=old['parametros'],depois=dc['parametros'],portas_placa_cabos_preservados=True,antena_nao_alterada=True))
print(json.dumps(dc['parametros'],indent=2))
