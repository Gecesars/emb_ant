"""Comparar a potência entregue nos terminais das antenas a partir do HFSS e dos coaxiais."""
import argparse
import csv
import json
import sys
from pathlib import Path
import numpy as np
import skrf
from extrair_cupons import passes
from projeto import LAMINADOS

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"r02"))
from ensaiar_rede import cable


def measure(estudo,mat,nome):
    rede=estudo/mat/"rede_hfss"
    c,t=passes(rede/"convergencia.txt")
    assert c>=t and t>=2
    nt=skrf.Network(str(rede/nome));f=nt.f
    if nome=="placa.s11p":np.testing.assert_allclose(f/1e6,range(5090,5251,10),atol=.001,rtol=0)
    else:np.testing.assert_allclose(f/1e6,[5170],atol=.001,rtol=0)
    names=[n.strip().split(":")[0] for n in nt.port_names]
    expected=["IN"]+["E%02d"%i for i in range(1,11)]
    assert set(names)==set(expected) and np.allclose(nt.z0,50)
    assert np.max(abs(nt.s-nt.s.transpose(0,2,1)))<.001
    assert np.max(np.linalg.svd(nt.s,compute_uv=False))<1.005
    lengths=json.loads((estudo/"mecanica/verificacao_chicote.json").read_text())["comprimentos_mm"]
    output=[]
    for k,hz in enumerate(f):
        inc=cable(hz,lengths["IN_B"]-1.5)
        # O modo par equivale às duas polarizações com a mesma onda incidente.
        rad=np.array([nt.s[k,names.index(tag),names.index("IN")]*inc*cable(hz,lengths[tag+"_B"]-1.5) for tag in expected[1:]])
        reflected=nt.s[k,names.index("IN"),names.index("IN")]*inc**2
        power=np.sum(abs(rad)**2)
        assert 0<power<=1-abs(reflected)**2+.001
        phi=np.sort(np.mod(np.angle(rad,deg=True),360))
        spread=360-max(np.diff(np.r_[phi,phi[0]+360]))
        output.append([mat,round(hz/1e6),power,-10*np.log10(power),-20*np.log10(abs(reflected)),
                       np.ptp(20*np.log10(abs(rad))),spread])
    return output


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("estudo",type=Path)
    args=parser.parse_args()
    for nome in ["centro.s11p","placa.s11p"]:
        rows=[]
        for mat in LAMINADOS:
            if (args.estudo/mat/"rede_hfss"/nome).exists():rows.extend(measure(args.estudo,mat,nome))
        if rows:
            with (args.estudo/"perdas"/("rede_hfss_"+nome.split(".")[0]+".csv")).open("w",newline="") as f:
                w=csv.writer(f);w.writerow(["material","MHz","potencia_entregue_por_W","perda_excedente_dB",
                    "retorno_ativo_dB","dispersao_amplitude_dB","dispersao_fase_graus"]);w.writerows(rows)
