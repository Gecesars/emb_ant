"""Quatro elementos com dois coaxiais fisicos e refletor local; sem apoios plasticos."""
from pathlib import Path
import json
import FreeCAD as A,Part,Import
V=A.Vector
root=Path('D:/dev/EMBRAER/P2M21/R11_Divisor_Ajustes/v20_altura_mais10')

def box(x,y,z,a,b,c):return Part.makeBox(a,b,c,V(x,y,z))
def cyl(x,y,z,r,h):return Part.makeCylinder(r,h,V(x,y,z))
def face(coords,z):
    def wire(points):
        pts=[V(float(x),float(y),z) for x,y in points]
        if (pts[0]-pts[-1]).Length>1e-9:pts.append(pts[0])
        return Part.makePolygon(pts)
    s=Part.Face(wire(coords[0]))
    for hole in coords[1:]:s=s.cut(Part.Face(wire(hole)))
    return s

for folder in [root]:
    g=json.loads((folder/'geometria.json').read_text());cad=folder/'cad';cad.mkdir(exist_ok=True)
    d=A.newDocument('Quatro_Elementos');man={};rec={};ports=[]
    def add(n,s,m):
        assert s.isValid() and s.Volume>0,n
        o=d.addObject('Part::Feature',n);o.Shape=s;o.addProperty('App::PropertyString','Material_nominal');o.Material_nominal=m;man[n]=m
        return o
    x0,y0=g['outline'][0];x1,y1=g['outline'][2];z0=g.get('distancia_pcb_refletor_mm',16.61)
    core=box(x0,y0,z0,x1-x0,y1-y0,.76)
    holes=[(x,y,.2,.235) for x,y in g['vias']]+[(p['x'],p['y'],.55,.585) for p in g['inputs']]
    for x,y,ri,ro in holes:core=core.cut(cyl(x,y,z0,ro,.76))
    add('PCB_RO4350B',core,'RO4350B_R01')
    for l in g['lands']:
        geometry=l['geometry'];polys=[geometry['coordinates']] if geometry['type']=='Polygon' else geometry['coordinates']
        z=z0+(.76 if l['layer']=='F' else -.035)
        parts=[face(c,z).extrude(V(0,0,.035)) for c in polys]
        if l['net']=='SIG_B':parts += [cyl(x,y,z,.363,.035) for x,y in g['vias']]
        for p in g['inputs']:
            if l['net']==p['sig']:parts.append(cyl(p['x'],p['y'],z,.8,.035))
        s=parts[0].multiFuse(parts[1:]).removeSplitter() if len(parts)>1 else parts[0]
        for x,y,ri,ro in holes:s=s.cut(cyl(x,y,z,ri,.035))
        for i,solid in enumerate(s.Solids):
            n=l['layer']+'_'+l['net']+'_Cu'+str(i);add(n,solid,'folha_cu')
            rec[n]=dict(base_z_mm=z0+.76 if l['layer']=='F' else z0,exposto=1 if l['layer']=='F' else -1,espessura_mm=.035)
    for i,(x,y) in enumerate(g['vias']):add('Via_'+str(i),cyl(x,y,z0,.235,.76).cut(cyl(x,y,z0,.2,.76)),'copper')
    for p in g['inputs']:
        x,y=p['x'],p['y'];name=p['name'];zend=z0-50
        pin=cyl(x,y,zend,.45975,49.82).fuse(cyl(x,y,z0-.18,.525,1.01)).removeSplitter()
        solder=cyl(x,y,z0,.55,.795).fuse(cyl(x,y,z0+.795,.65,.035)).cut(pin).removeSplitter()
        shield=cyl(x,y,zend,1.7905,49.82).cut(cyl(x,y,zend,1.515,49.82))
        shield=shield.fuse(cyl(x,y,z0-.18,2.13,.145).cut(cyl(x,y,z0-.18,1.515,.145))).removeSplitter()
        ptfe=cyl(x,y,zend,1.515,50).cut(pin).cut(cyl(x,y,z0-.035,.8,.035)).removeSplitter()
        add('Vivo_'+name,pin,'copper');add('Blindagem_'+name,shield,'copper');add('PTFE_'+name,ptfe,'PTFE_terminal')
        add('Solda_'+name,solder,'SAC305');add('PTH_'+name,cyl(x,y,z0,.585,.76).cut(cyl(x,y,z0,.55,.76)),'copper')
        ports.append(dict(name=name,x=x,y=y,z=zend,ri=.45975,ro=1.515))
    ref=box(x0-8,-45,-2,x1-x0+16,90,2)
    for p in g['inputs']:ref=ref.cut(cyl(p['x'],p['y'],-2,2.1,2))
    add('Refletor_Al2mm',ref,'AL5052')
    d.recompute();d.saveAs(str(folder/'4_elementos.FCStd'))
    for m in sorted(set(man.values())):Import.export([d.getObject(n) for n,mat in man.items() if mat==m],str(cad/(m+'.step')))
    for name,data in [('manifesto',man),('folhas_solidas',rec),('portas',ports)]:
        (cad/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    objs=[d.getObject(n) for n in man];bad=[];tested=0
    for i,a in enumerate(objs):
        ba=a.Shape.BoundBox
        for b in objs[i+1:]:
            bb=b.Shape.BoundBox
            if min(ba.XMax,bb.XMax)-max(ba.XMin,bb.XMin)<=1e-6 or min(ba.YMax,bb.YMax)-max(ba.YMin,bb.YMin)<=1e-6 or min(ba.ZMax,bb.ZMax)-max(ba.ZMin,bb.ZMin)<=1e-6:continue
            tested+=1;volume=a.Shape.common(b.Shape).Volume
            if volume>1e-7:bad.append(dict(a=a.Name,b=b.Name,volume=volume))
    result=dict(aprovado=not bad,objetos=len(objs),pares=tested,intersecoes=bad,portas=ports)
    (cad/'intersecoes.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(folder.name,result,flush=True);assert not bad
    A.closeDocument(d.Name)
