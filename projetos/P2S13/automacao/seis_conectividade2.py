"""Conectividade DC dos condutores alimentados, com filtro espacial antes do OCCT."""
import FreeCAD as A,json,os
from pathlib import Path
r=Path(os.environ.get('P2S13_CELULA2','D:/dev/EMBRAER/P2S13/R01_Seis_Elementos/celula2_simetrica'))
d=A.openDocument(str(r/'2_elementos_simetrica.FCStd'));man=json.loads((r/'cad/manifesto.json').read_text());groups={}
for pol in 'AB':
    groups['SIG_'+pol]=[n for n in man if ('_SIG_'+pol+'_') in n]+[k+'_'+pol for k in ['Vivo','PTH','Solda']]+(['Via_'+str(k) for k in range(4)] if pol=='B' else [])
    groups['RET_'+pol]=[n for n in man if '_RET_'+pol+'_' in n]+['Blindagem_'+pol]
sh={n:d.getObject(n).Shape for ns in groups.values() for n in ns};bounds={n:s.BoundBox for n,s in sh.items()}
def touch(a,b):
    aa,bb=bounds[a],bounds[b]
    if any(max(getattr(aa,k+'Min'),getattr(bb,k+'Min'))-min(getattr(aa,k+'Max'),getattr(bb,k+'Max'))>1e-6 for k in 'XYZ'):return False
    return sh[a].distToShape(sh[b])[0]<1e-6
result={};shorts=[]
for net,names in groups.items():
    edges=[(a,b) for i,a in enumerate(names) for b in names[i+1:] if touch(a,b)]
    seen={names[0]}
    while True:
        old=set(seen)
        for a,b in edges:
            if a in seen or b in seen:seen.update([a,b])
        if seen==old:break
    result[net]={'objetos':names,'contatos':edges,'conectado':len(seen)==len(names),'isolados':list(set(names)-seen)}
    assert result[net]['conectado'],(net,result[net])
for i,(na,aa) in enumerate(groups.items()):
    for nb,bb in list(groups.items())[i+1:]:
        for a in aa:
            for b in bb:
                if touch(a,b):shorts.append((na,nb,a,b))
assert not shorts,shorts
(r/'conectividade.json').write_text(json.dumps({'redes':result,'curtos':shorts,'aprovado':True},indent=2)+'\n')
A.closeDocument(d.Name);print(json.dumps({'redes_conectadas':list(result),'curtos':shorts}))
