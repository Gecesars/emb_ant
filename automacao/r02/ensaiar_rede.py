"""Ensaio em cargas de 50 ohms das duas arquiteturas. Portas iguais nos dois ensaios."""
import argparse
import csv
import json
from pathlib import Path

import numpy as np
import skrf
from scipy.linalg import block_diag


def read(path,prefix):
    network=skrf.Network(str(path))
    assert network.port_names is not None
    assert np.allclose(network.z0,50)
    np.testing.assert_allclose(network.f/1e6,np.arange(5090,5251,10),rtol=0,atol=.001)
    assert np.isfinite(network.s).all()
    assert np.max(np.linalg.svd(network.s,compute_uv=False))<1.005
    return [prefix+n.strip().split(":")[0] for n in network.port_names],network.s


def cable(f,mm):
    # Atenuação em dB/100 ft e capacitância em pF/m, ficha UT-141C.
    loss=np.interp(f/1e9,[5,10],[27.6,41.6])/30.48
    velocity=1/(50*95.2e-12)
    return 10**(-loss*mm/20000)*np.exp(-2j*np.pi*f*(mm/1000)/velocity)


def calculate(parts,input_names,output_names,feed,branch,trunks):
    ports=[name for names,values in parts for name in names]
    ext=input_names+output_names
    indexes=[ports.index(name) for name in ext]
    results=[]
    for k,f in enumerate(np.arange(5090,5251,10)*1e6):
        s=block_diag(*[values[k] for _,values in parts])
        links=np.zeros_like(s)
        for x,y,length in trunks:
            i,j=ports.index(x),ports.index(y)
            links[i,j]=links[j,i]=cable(f,length-3)
        # b = S(a_ext + L b). No contorno, os geradores e as cargas são casados.
        running=np.linalg.solve(np.eye(len(s))-s@links,s)
        ext_s=running[np.ix_(indexes,indexes)]
        t=np.array([cable(f,feed-1.5)]*2+[cable(f,branch-1.5)]*20)
        answer=t[:,None]*ext_s*t[None,:]
        assert np.max(abs(answer-answer.T))<.02
        assert max(np.linalg.svd(answer,compute_uv=False))<1.005
        results.append(answer)
    return np.stack(results)


def evaluate(work,previous,dest):
    lengths=json.loads((work/"compacta/verificacao_cad.json").read_text())["comprimentos_mm"]
    repo=Path(__file__).resolve().parents[2]
    old_lengths=json.loads((repo/"freecad/mecanica_R01/verificacao.json").read_text())["cabos"]
    first=read(work/"rede/1x2/divisor.s6p","R_")
    lower=read(work/"revisao/1x5/divisor.s12p","L_")
    upper=(["U_"+n[2:] for n in lower[0]],lower[1])
    outputs=[g+p+str(i) for p in "AB" for g in ("L_","U_") for i in range(1,6)]
    inputs=["R_A_IN","R_B_IN"]
    joins=[("R_"+p+str(i),g+p+"_IN",lengths["TR_"+h+"_"+p])
           for i,g,h in [(1,"L_","INF"),(2,"U_","SUP")] for p in "AB"]
    split=calculate([first,lower,upper],inputs,outputs,lengths["IN_A"],lengths["INF_A1"],joins)
    old=calculate([read(previous,"")],["A_IN","B_IN"],[p+str(i) for p in "AB" for i in range(1,11)],
                  old_lengths["IN_A"]["eixo_mm"],old_lengths["A1"]["eixo_mm"],[])
    dest.mkdir(exist_ok=True,parents=True)
    incident=np.array([1,1])/np.sqrt(2)
    with (dest/"rede_cargas_50ohm.csv").open("w",newline="",encoding="utf8") as file:
        writer=csv.writer(file)
        writer.writerow(["MHz","rede","perda_excedente_dB","potencia_saidas_W","refletida_W","dissipada_ou_radiada_W",
                         "amplitude_pico_a_pico_dB","fase_pico_a_pico_graus","desvio_medio_superior_inferior_graus"])
        for k,f in enumerate(range(5090,5251,10)):
            for tag,ss in [("R01",old),("R02",split)]:
                b=ss[k,:,:2]@incident
                w=sum(abs(b[2:])**2)
                reflected=sum(abs(b[:2])**2)
                loss=1-w-reflected
                phase=np.angle(b[2:]/np.mean(b[2:]),deg=True)
                assert loss>=0 and np.ptp(phase)<180
                half=phase.reshape(2,2,5).mean(axis=(0,2))
                writer.writerow([f,tag,*[round(v,6) for v in [-10*np.log10(w),w,reflected,loss,
                                  np.ptp(20*np.log10(abs(b[2:]))),np.ptp(phase),half[1]-half[0]]]])
    for tag,ss in [("R01",old),("R02",split)]:
        network=skrf.Network(f=np.arange(5090,5251,10)*1e6,s=ss,z0=50,f_unit="Hz",name=tag+"_coax_divisores")
        network.port_names=["A_IN","B_IN"]+[p+str(i) for p in "AB" for i in range(1,11)]
        network.write_touchstone(dir=dest,form="ri")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ["estudo","divisor_r01","saida"]:parser.add_argument(name,type=Path)
    args=parser.parse_args()
    evaluate(args.estudo,args.divisor_r01,args.saida)
