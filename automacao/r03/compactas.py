"""Ensaiar a rede compacta com os mesmos quatro laminados candidatos da alongada."""
import argparse
import csv
import json
import sys
from pathlib import Path
import numpy as np
from projeto import LAMINADOS
from extrair_cupons import passes

repo=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(repo/"automacao/r02"))
from radiais import layout
from ensaiar_rede import calculate, read


def evaluate(estudo):
    lengths=json.loads((repo/"freecad/mecanica_R02/verificacao_cad.json").read_text())["comprimentos_mm"]
    records=[]
    for material in LAMINADOS:
        stages=estudo/material/"compacta"
        if material=="ZYF300CA-C":
            archive=repo/"resultados/r02/rede"
            paths=[archive/"R02_1x2.s6p",archive/"R02_1x5.s12p"]
            checks=[archive/"convergencia_1x2.txt",archive/"convergencia_1x5.txt"]
        else:
            paths=[stages/"1x2/divisor.s6p",stages/"1x5/divisor.s12p"]
            checks=[p.parent/"convergencia.txt" for p in paths]
        if not all(p.is_file() for p in paths):continue
        for path in checks:
            n,target=passes(path)
            assert n>=target>=2
        first=read(paths[0],"R_");lower=read(paths[1],"L_")
        upper=(["U_"+n[2:] for n in lower[0]],lower[1])
        joins=[("R_"+p+str(i),g+p+"_IN",lengths["TR_"+h+"_"+p])
               for i,g,h in [(1,"L_","INF"),(2,"U_","SUP")] for p in "AB"]
        outputs=[g+p+str(i) for p in "AB" for g in ("L_","U_") for i in range(1,6)]
        s=calculate([first,lower,upper],["R_A_IN","R_B_IN"],outputs,lengths["IN_A"],lengths["INF_A1"],joins)
        for f,matrix in zip(range(5090,5251,10),s):
            wave=matrix[:,:2]@([1/np.sqrt(2)]*2)
            power=np.sum(abs(wave[2:])**2)
            phase=np.angle(wave[2:]/np.mean(wave[2:]),deg=True)
            assert 0<power<=1-np.sum(abs(wave[:2])**2)+.001 and np.ptp(phase)<180
            records.append([material,f,power,-10*np.log10(power),np.ptp(20*np.log10(abs(wave[2:]))),np.ptp(phase)])
    with (estudo/"perdas/compactas_hfss.csv").open("w",newline="") as f:
        w=csv.writer(f);w.writerow(["material","MHz","potencia_entregue_por_W","perda_excedente_dB",
                                   "dispersao_amplitude_dB","dispersao_fase_graus"]);w.writerows(records)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("estudo",type=Path)
    parser.add_argument("--preparar",action="store_true")
    args=parser.parse_args()
    if args.preparar:
        for mat,(dk,df) in LAMINADOS.items():
            if mat=="ZYF300CA-C":continue
            for n in [2,5]:layout(n,args.estudo/mat/"compacta"/f"1x{n}",mat,dk,df)
    evaluate(args.estudo)
