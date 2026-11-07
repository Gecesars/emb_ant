"""Comparar os dois divisores em cargas de 50 Ω com os mesmos modelos de linha."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
import skrf

from projeto import LAMINADOS,FREQUENCIAS,Z50,Z2,Z5,dimensionar,routes


def abcd(gamma,z0,length):
    arg=gamma*length/1000
    ch,sh=np.cosh(arg),np.sinh(arg)
    return np.array([[ch,z0*sh],[sh/z0,ch]])


def solve(links,external):
    """Admitâncias nodais, com eliminação dos nós internos e referência externa de 50 Ω."""
    nodes=external+sorted({node for a,b,m in links for node in (a,b)}-set(external))
    Y=np.zeros((len(nodes),len(nodes)),complex)
    for u,v,t in links:
        i,j=nodes.index(u),nodes.index(v)
        a,b=t[0];c,d=t[1]
        Y[i,i]+=d/b;Y[j,j]+=a/b;Y[i,j]+=(b*c-a*d)/b;Y[j,i]+=-1/b
    n=len(external)
    eq=Y[:n,:n]-Y[:n,n:]@np.linalg.solve(Y[n:,n:],Y[n:,:n])
    eye=np.eye(n)
    return np.linalg.solve(eye+50*eq,eye-50*eq)


def test(material,geometry,ff,coax,kind):
    model=dimensionar(material,1.52)
    data=[];mats=[]
    for k,f in enumerate(ff):
        links=[]
        def micro(a,b,segments):
            t=np.eye(2)
            for length,z in segments:
                line=model[z][2]
                t=t@abcd(line.gamma[k],line.z0[k],length)
            links.append((a,b,t))
        def cable(a,b,length):
            loss=np.interp(f/1e9,[5.,10.],[27.6,41.6])/30.48
            jbeta=2j*np.pi*f*50*95.2e-12
            links.append((a,b,abcd(loss/8.685889638+jbeta,50,length)))
        cable("N","IN",coax["N"])
        if kind=="alongada":
            for edge in geometry:micro(edge["de"],edge["para"],edge["trechos"])
        else:
            # Duas etapas radiais por polarização. Cada saída compacta fica a 15,2 mm do centro.
            def radial(a,b,z):
                q=model[z][1]
                micro(a,b,[(.86,50),(q,z),(15.2-.86-q,50)])
            for half in ("INF","SUP"):
                radial("IN","T"+half,Z2);cable("T"+half,half,coax["T"])
                for i in range(1,6):radial(half,half+str(i),Z5)
        outputs=[]
        for group in ("INF","SUP"):
            for i in range(1,6):
                name=group+str(i)
                cable(name,"ANT_"+name,coax["ramal"]);outputs.append("ANT_"+name)
        s=solve(links,["N"]+outputs)
        assert max(np.linalg.svd(s,compute_uv=False))<1.0001 and np.max(abs(s-s.T))<1e-9
        out=s[1:,0];power=sum(abs(out)**2);ref=abs(s[0,0])**2
        assert 1-ref-power>0
        phase=np.angle(out/np.mean(out),deg=True)
        data.append([int(round(f/1e6)),material,kind,-10*np.log10(power),-10*np.log10(power/(1-ref)),
                     -10*np.log10(ref),power,np.ptp(20*np.log10(abs(out))),np.ptp(phase)])
        mats.append(s)
    return data,np.stack(mats)


def run(root):
    p=root/"mecanica/verificacao_chicote.json"
    ends=json.loads(p.read_text())["comprimentos_mm"]
    out=root/"perdas";out.mkdir(exist_ok=True)
    allrows=[]
    for mat in LAMINADOS:
        g=json.loads((root/mat/"linhas.json").read_text())
        for kind,coax in [("compacta",{"N":271.792113,"T":132,"ramal":130}),
                          ("alongada",{"N":ends["IN_A"],"ramal":ends["E01_A"]})]:
            rows,matrix=test(mat,g["rede"],FREQUENCIAS.f,coax,kind)
            allrows.extend(rows)
            n=skrf.Network(frequency=FREQUENCIAS,s=matrix,z0=50,name=kind+"_"+mat)
            n.port_names=["N"]+["E%02d"%i for i in range(1,11)]
            n.write_touchstone(dir=out,form="ri")
            print(mat,kind,"L0/550 [dB]",round(rows[8][3],4),"pp",round(rows[8][-1],3))
    with (out/"comparacao_linhas.csv").open("w",newline="",encoding="utf8") as f:
        w=csv.writer(f)
        w.writerow(["MHz","material","geometria","perda_excedente_dB","perda_aceita_dB","retorno_dB",
                    "potencia_entregue_por_W","dispersao_amplitude_dB","dispersao_fase_graus"])
        w.writerows(allrows)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("dir",type=Path);run(p.parse_args().dir)
