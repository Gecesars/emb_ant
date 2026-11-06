"""Segunda montagem do ensaio usando as conexões nativas de scikit-rf."""
import argparse
import json
from pathlib import Path
import numpy as np
import skrf
from skrf.circuit import Circuit
from skrf.media import DefinedGammaZ0

def verify(root,path):
    first=skrf.Network(str(root/"rede/1x2/divisor.s6p"),name="1x2")
    lower=skrf.Network(str(root/"revisao/1x5/divisor.s12p"),name="INF")
    upper=lower.copy();upper.name="SUP"
    lengths=json.loads((root/"compacta/verificacao_cad.json").read_text())["comprimentos_mm"]
    loaded=skrf.Network(str(path/"R02_coax_divisores.s22p"))
    frequency=first.frequency
    loss=np.interp(first.f/1e9,[5.,10.],[27.6,41.6])/30.48
    media=DefinedGammaZ0(frequency=frequency,z0=50,gamma=loss*np.log(10)/20+1j*(2*np.pi*first.f*50*95.2e-12))
    externa=[];internal=[]
    def link(name,mm,left,right):
        segment=media.line(mm,unit="mm",name=name)
        return [[left,(segment,0)],[(segment,1),right]]
    for p in "AB":
        key=p+"_IN"
        externa.extend(link("N_"+p,lengths["IN_"+p]-1.5,(Circuit.Port(frequency,key),0),(first,first.port_names.index(key))))
    for p in "AB":
        for i,(group,nt) in enumerate([("INF",lower),("SUP",upper)],1):
            key="TR_"+group+"_"+p
            internal.extend(link(key,lengths[key]-3,(first,first.port_names.index(p+str(i))),(nt,nt.port_names.index(p+"_IN"))))
            for number in range(1,6):
                small=p+str(number);big=p+str(number+5*(i-1));n=group+"_"+small
                externa.extend(link(n,lengths[n]-1.5,(Circuit.Port(frequency,big),0),(nt,nt.port_names.index(small))))
    computed=Circuit(externa+internal).network
    error=float(np.max(abs(loaded.s-computed.s)))
    assert error<1e-10,error
    return dict(pontos=len(first.f),portas=loaded.nports,erro_maximo_montagens_independentes=error)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("estudo",type=Path);p.add_argument("dados",type=Path)
    a=p.parse_args();print(json.dumps(verify(a.estudo,a.dados),indent=2))
