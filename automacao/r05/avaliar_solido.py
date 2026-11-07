"""Comparar a representação volumétrica e shell do divisor isolado."""
import argparse
import json
import re
from pathlib import Path

import skrf
from analisar_enig import validate

def main(work):
    folder=work/'enig_solido/1x2'
    convergence=(folder/'convergencia.txt').read_text()
    assert 'Converged : Yes' in convergence
    assert int(re.search(r'Current Consecutive Passes\s*:\s*(\d+)',convergence)[1])>=2
    history=re.findall(r'^\s*(\d+)\|\s*(\d+)\|\s*([\d.eE+-]+)\|',convergence,re.M)
    assert len(history)>=2 and all(float(row[2])<=.008 for row in history[-2:])
    new,loss=validate(folder/'divisor.s6p')
    old,loss_old=validate(work/'enig/1x2/divisor.s6p')
    a=skrf.Network(str(folder/'divisor.s6p'))
    b=skrf.Network(str(work/'enig/1x2/divisor.s6p'))
    assert a.port_names==b.port_names
    result=dict(solido=new,shell=old,diferenca_IL_min_dB=float((loss-loss_old).min()),
        diferenca_IL_max_dB=float((loss-loss_old).max()),diferenca_S_max_abs=float(abs(a.s-b.s).max()),
        passes=int(history[-1][0]),tetraedros=int(history[-1][1]),
        deltaS_final=float(history[-1][2]),pontos=len(a.f),
        observacao='O cobre volumétrico acrescenta os 35um físicos e suas bordas; o shell tinha espessura geométrica nula. Não é resultado do painel.')
    (folder/'comparacao.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('diretorio',type=Path)
    main(p.parse_args().diretorio)
