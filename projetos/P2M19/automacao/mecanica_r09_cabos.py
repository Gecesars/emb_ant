"""Integra envelopes coaxiais do planejamento em arcos circulares exatos de R10.
Sem RF, sem acabamento de solda e sem lista de corte final.
"""
import FreeCAD as A, Part, json, math, hashlib
from pathlib import Path
ROOT=Path('D:/dev/EMBRAER/emb_ant/projetos/P2M19/mecanica_R09_PRELIMINAR')
NETWORK=ROOT.parent/'rede_R09_PLANEJAMENTO/plano_rede.json'
plan=json.loads(NETWORK.read_text());spec=json.loads((ROOT/'objetos.json').read_text());colors=json.loads((ROOT/'cores.json').read_text())
d=A.openDocument(str(ROOT/'P2M19_R09_PRELIMINAR.FCStd'));V=A.Vector
before={n:hashlib.sha256(d.getObject(n).Shape.exportBrepToString().encode()).hexdigest() for n in spec['rf_hashes']}
assert not d.getObject('Chicote_planejado'), 'Cabos ja integrados'
for tag in ['A','B']:d.getObject('N_'+tag+'_rebaixo').Radius=16
d.recompute()
grp=d.addObject('App::DocumentObjectGroup','Chicote_planejado')
def rounded_wire(points,r):
    points=[V(*p) for p in points];joints=[]
    for i in range(1,len(points)-1):
        a,b,c=points[i-1:i+2];u=b-a;u.normalize();v=c-b;v.normalize()
        ang=math.acos(max(-1,min(1,u.dot(v))))
        if ang<1e-7:continue
        t=r*math.tan(ang/2);ti=b-u*t;to=b+v*t
        normal=u.cross(v);normal.normalize();inward=normal.cross(u)
        center=ti+inward*r;radial=ti-center
        midpoint=center+radial*math.cos(ang/2)+normal.cross(radial)*math.sin(ang/2)
        joints.append((ti,midpoint,to))
    edges=[];prev=points[0]
    for ti,mid,to in joints:
        if (prev-ti).Length>1e-8:edges.append(Part.makeLine(prev,ti))
        edges.append(Part.Arc(ti,mid,to).toShape());prev=to
    if (points[-1]-prev).Length>1e-8:edges.append(Part.makeLine(prev,points[-1]))
    return Part.Wire(edges)
rows=[];wires={}
for cab in plan['cabos']:
    name='Cabo_'+cab['id'];wire=rounded_wire(cab['pontos_controle_mm'],cab['raio_eixo_mm'])
    delta=abs(wire.Length-cab['comprimento_eixo_mm']);assert delta<1e-6,(name,delta)
    p0=V(*cab['pontos_controle_mm'][0]);direction=V(*cab['pontos_controle_mm'][1])-p0;direction.normalize()
    circle=Part.Wire([Part.makeCircle(plan['cabo_od_mm']/2,p0,direction)])
    shape=wire.makePipeShell([circle],True,False)
    assert shape.isValid() and len(shape.Solids)==1,name
    o=d.addObject('Part::Feature',name);o.Shape=shape;grp.addObject(o)
    for key,value in dict(Material_nominal='UT-141C; envelope externo OD3.581mm',Estado='PRELIMINAR; percurso igualado, sem soldas nem sobremetal de corte',Origem=cab['origem'],Destino=cab['destino'],Classe=cab['classe'],Polarizacao=cab['polarizacao']).items():
        o.addProperty('App::PropertyString',key,'Planejamento');setattr(o,key,value)
    o.addProperty('App::PropertyLength','Comprimento_eixo','Planejamento');o.Comprimento_eixo=wire.Length
    o.addProperty('App::PropertyLength','Raio_minimo_eixo','Planejamento');o.Raio_minimo_eixo=cab['raio_eixo_mm']
    colors[name]=[.78,.39,.15] if cab['polarizacao']=='A' else [.30,.57,.76]
    spec['finais'].append(name);spec['criticos'].append(name);wires[name]=wire
    rows.append(dict(id=cab['id'],comprimento_plano_mm=cab['comprimento_eixo_mm'],comprimento_CAD_mm=wire.Length,erro_mm=delta,solido_valido=True))
gaps=[]
for i,a in enumerate(wires):
    for b in list(wires)[i+1:]:
        distance=wires[a].distToShape(wires[b])[0]
        gaps.append(dict(a=a,b=b,distancia_eixos_mm=distance,folga_superficies_mm=distance-plan['cabo_od_mm']))
gaps.sort(key=lambda x:x['folga_superficies_mm'])
assert gaps[0]['folga_superficies_mm']>0,gaps[0]
# Envelope de acesso de soquete OD30mm, abertura interna25.2mm: vazio na base/reforcos.
tools=[]
for tag,y in [('A',-24),('B',24)]:
    sh=Part.makeCylinder(15,17,V(-394,y,-45),V(1,0,0)).cut(Part.makeCylinder(12.6,17,V(-394,y,-45),V(1,0,0)))
    inter=[]
    for name in ['Base_furada_D','Reforco_L_E','Reforco_L_D']:
        vol=sh.common(d.getObject(name).Shape).Volume
        if vol>1e-5:inter.append(dict(objeto=name,volume_mm3=vol))
    tools.append(dict(conector=tag,ferramenta_envelope_OD_mm=30,folga_radial_rebaixo_mm=1,intersecoes=inter))
assert not any(t['intersecoes'] for t in tools)
assert all(hashlib.sha256(d.getObject(n).Shape.exportBrepToString().encode()).hexdigest()==h for n,h in before.items())
spec['rf_hashes_pos_reabertura']=before
d.recompute();d.save()
d.getObject('Base_furada_D').Shape.exportStep(str(ROOT/'Base_aluminio_PRELIMINAR.step'))
(ROOT/'objetos.json').write_text(json.dumps(spec,indent=2),encoding='utf-8');(ROOT/'cores.json').write_text(json.dumps(colors,indent=2),encoding='utf-8')
dim=json.loads((ROOT/'dimensoes.json').read_text());dim['base']['rebaixo_N']=[32,2];dim['chicote']=dict(quantidade=22,eixo_total_mm=sum(r['comprimento_CAD_mm'] for r in rows),raio_eixo_mm=10,OD_mm=plan['cabo_od_mm'],aviso='Nao e lista de corte; soldas/decapagens/tolerancias pendentes')
(ROOT/'dimensoes.json').write_text(json.dumps(dim,ensure_ascii=False,indent=2),encoding='utf-8')
text=(ROOT/'furacao_PRELIMINAR.csv').read_text(encoding='utf-8-sig').replace('D26x2','D32x2');(ROOT/'furacao_PRELIMINAR.csv').write_text(text,encoding='utf-8-sig')
report=dict(estado='PRELIMINAR',plano_rede_sha256=hashlib.sha256(NETWORK.read_bytes()).hexdigest(),cabos=rows,menores_folgas_cabo_cabo=gaps[:10],teste_acesso_ferramenta=tools,sem_alteracao_RF=True,
    metodo='Arcos circulares R10 exatos, sweep de secao circular OD3.581; distancia exata entre fios-eixo no OCCT. Solid exterior sem internosRF.')
(ROOT/'verificacao_cabos.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(cabos=len(rows),total_mm=sum(r['comprimento_CAD_mm'] for r in rows),folga_min_mm=gaps[0]['folga_superficies_mm'],ferramentas=tools),indent=2),flush=True)
