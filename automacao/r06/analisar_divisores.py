"""Caracterizar as duas PCBs com todos os terminais nao excitados casados em 50 ohms."""
import argparse,csv,json,re
from pathlib import Path
import numpy as np
import skrf
from auditar_malha import audit

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);args=parser.parse_args()
rows=[];summary={}
for side,count in [('inferior',18),('superior',12)]:
    folder=args.root/('divisor_'+side)
    net=skrf.Network(str(folder/('divisor.s%dp'%count)))
    names=[p.strip() for p in net.port_names]
    np.testing.assert_allclose(net.f/1e6,np.arange(5090,5251,10),atol=.001,rtol=0)
    assert np.allclose(net.z0,50)
    singular=float(np.max(np.linalg.svd(net.s,compute_uv=False)))
    reciprocal=float(np.max(abs(net.s-net.s.transpose(0,2,1))))
    assert singular<=1.005 and reciprocal<1e-6
    convergence=(folder/'convergencia.txt').read_text()
    assert 'Converged : Yes' in convergence
    assert int(re.search(r'Current Consecutive Passes\s*:\s*(\d+)',convergence)[1])>=2
    mesh=audit(folder)
    (folder/'malha.json').write_text(json.dumps(mesh,indent=2),encoding='utf8')
    assert mesh['reparos_major']==0, 'Rever reparos da malha do divisor '+side
    groups=[('1x5','',5)]+([('1x2','R',2)] if side=='inferior' else [])
    board=[]
    for stage,prefix,n in groups:
        inputs=[names.index(prefix+p+'_IN') for p in 'AB']
        outputs=[names.index(prefix+p+str(i)) for p in 'AB' for i in range(1,n+1)]
        excitation=np.zeros(count,complex);excitation[inputs]=1/np.sqrt(2)
        for k,f in enumerate(net.f):
            b=net.s[k]@excitation;power=float(sum(abs(b[outputs])**2))
            refl=float(sum(abs(b[inputs])**2))
            active=abs(b[inputs]/excitation[inputs]);vs=(1+active)/(1-active)
            row=dict(placa=side,estagio=stage,frequencia_MHz=float(f/1e6),
                perda_excedente_dB=float(-10*np.log10(power)),potencia_destinos_W=power,
                refletida_W=refl,nao_entregue_destinos_W=1-power-refl,
                VSWR_ativo_A=float(vs[0]),VSWR_ativo_B=float(vs[1]))
            rows.append(row);board.append(row)
    summary[side]=dict(max_valor_singular=singular,reciprocidade_erro_max=reciprocal,
                       portas=count,reparos_major=mesh['reparos_major'],centro=[r for r in board if r['frequencia_MHz']==5170])
output=args.root/'circuito';output.mkdir(exist_ok=True)
with (output/'divisores_cargas50.csv').open('w',newline='',encoding='utf8') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
(output/'divisores.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
print(json.dumps(summary,indent=2))
