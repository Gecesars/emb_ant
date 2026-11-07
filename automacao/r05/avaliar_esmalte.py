"""Conferir o cupom com película e aplicar a diferença ao estudo de rede."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
import skrf
from rede_carregada import LoadedPanel


def main(work):
    folder=work/'cupons/Bobina_esmalte20'
    convergence=(folder/'convergencia.txt').read_text()
    assert 'Current Consecutive Passes : 2' in convergence and 'Converged : Yes' in convergence
    coated=skrf.Network(str(folder/'cupom.s2p'))
    bare=skrf.Network(str(work/'cupons/Bobina_r090/cupom.s2p'))
    np.testing.assert_allclose(coated.f,np.arange(5090,5251,10)*1e6,atol=1,rtol=0)
    assert np.allclose(coated.z0,50)
    assert np.linalg.svd(coated.s,compute_uv=False).max()<1.005
    assert abs(coated.s-coated.s.transpose(0,2,1)).max()<.001
    il=-20*np.log10(abs(coated.s[:,1,0]))
    delta=il+20*np.log10(abs(bare.s[:,1,0]))
    rl=-20*np.log10(abs(coated.s[:,0,0]))
    model=LoadedPanel(work/'face40',work,True)
    front=model.patterns['H'][np.flatnonzero(model.angles==0)[0]]
    def gain():
        incident,_=model.waves([290,132,135])
        return float(10*np.log10(np.sum(abs(front@incident[model.antenna_indexes])**2)))
    rows=[]
    for i,f in enumerate(coated.f):
        model.set_frequency(f,freeze_antenna=True)
        before=gain()
        for pol in 'AB':
            indexes=[model.lookup['C'+pol+'/'+name] for name in ['Entrada','Saida']]
            model.s[np.ix_(indexes,indexes)]=coated.s[i]
        after=gain()
        rows.append(dict(MHz=f/1e6,IL_cupom_dB=float(il[i]),RL_cupom_dB=float(rl[i]),
            acrescimo_IL_dB=float(delta[i]),ganho_antena_congelada_sem_esmalte_dBi=before,
            ganho_antena_congelada_com_esmalte_dBi=after,diferenca_ganho_dB=after-before))
    with (folder/'comparacao.csv').open('w',newline='',encoding='utf8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    record=dict(hipotese=json.loads((folder/'hipotese.json').read_text()),
        IL_centro_dB=float(il[8]),RL_min_dB=float(rl.min()),acrescimo_IL_max_dB=float(delta.max()),
        efeito_ganho_min_dB=min(r['diferenca_ganho_dB'] for r in rows),
        efeito_ganho_max_dB=max(r['diferenca_ganho_dB'] for r in rows),
        ressalva='Película hipotética, somente na hélice. Campos e S20 da antena congelados em 5,17 GHz; não substitui o painel integral nem qualifica o fio real.')
    (folder/'resultado.json').write_text(json.dumps(record,indent=2),encoding='utf8')
    print(json.dumps(record,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('diretorio',type=Path)
    main(parser.parse_args().diretorio)
