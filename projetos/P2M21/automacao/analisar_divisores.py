"""Auditoria dos S reais dos divisores, sem extrapolar frequencias."""
import json,sys,hashlib
from pathlib import Path
import numpy as np,skrf
repo=Path(__file__).resolve().parents[3];sys.path.insert(0,str(repo/'automacao/r06'))
from auditar_malha import audit
root=Path('D:/dev/EMBRAER/P2M21/R00_Concepcao')
for n in (4,8):
    folder=root/f'divisor_1x{n}';path=folder/f'divisor.s{2*(n+1)}p'
    if not path.exists():continue
    nw=skrf.Network(str(path));names=[p.strip().split(':')[0] for p in nw.port_names]
    np.testing.assert_allclose(nw.f,np.arange(5090,5251,10)*1e6,atol=1,rtol=0)
    assert np.allclose(nw.z0,50)
    singular=float(np.linalg.svd(nw.s,compute_uv=False).max());rec=float(abs(nw.s-nw.s.transpose(0,2,1)).max())
    assert singular<=1.0001 and rec<1e-6
    rows=[]
    for f,s in zip(nw.f,nw.s):
        row=dict(frequencia_GHz=float(f/1e9))
        for pol in 'AB':
            i=names.index(pol+'_IN');o=[names.index(pol+str(j)) for j in range(1,n+1)]
            gamma=abs(s[i,i]);v=(1+gamma)/(1-gamma);t=s[o,i]
            row[pol]=dict(VSWR=float(v),perda_excedente_dB=float(-10*np.log10(sum(abs(t)**2))),
              amplitude_pp_dB=float(np.ptp(20*np.log10(abs(t)))),fase_pp_graus=float(np.ptp(np.angle(t/np.mean(t),deg=True))))
        rows.append(row)
    mesh=audit(folder);assert mesh['reparos_major']==0,mesh
    result=dict(n_saidas_por_polarizacao=n,passivo=True,reciproco=True,max_valor_singular=singular,
      erro_reciprocidade=rec,pontos=rows,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
      nota='Outras portas casadas50ohms. Perda excedente inclui reflexao e potencia que nao chega as saidas da mesma polarizacao. Nao e resultado do painel carregado.')
    (folder/'analise.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    (folder/'malha.json').write_text(json.dumps(mesh,indent=2),encoding='utf8')
    print(n,'PASSIVO_RECIPROCO',singular,'MAJOR',mesh['reparos_major'],'MINOR',mesh['reparos_minor'],rows[8])
