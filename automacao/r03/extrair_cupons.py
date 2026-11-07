"""Extrair atenuação e fase do par diferencial de linhas com terminais idênticos."""
import argparse
import csv
import re
from pathlib import Path
import numpy as np
import skrf
from projeto import LAMINADOS, Z50, dimensionar


def passes(path):
    data=path.read_text()
    def val(label):return int(re.search(r"^"+label+r"\s*:\s*(\d+)",data,re.M)[1])
    return val("Current Consecutive Passes"),val("Target Consecutive Passes")


def extract(base,mat):
    p=base/mat
    pair=[skrf.Network(str(p/f"cupom_{length}/linha.s2p")) for length in [20,120]]
    count=[passes(p/f"cupom_{length}/convergencia.txt") for length in [20,120]]
    a,b=pair
    np.testing.assert_allclose(a.f,np.arange(5090,5251,10)*1e6,rtol=0,atol=2)
    np.testing.assert_allclose(a.f,b.f,rtol=0,atol=2)
    model=dimensionar(mat,1.52)[Z50][2]
    # A cadeia T120 inv(T20) é semelhante à propagação de 100 mm pela linha.
    # A fase prevista escolhe o sinal e a volta de 2pi sem impor atenuação positiva.
    out=[]
    for i,f in enumerate(a.f):
        t=b.a[i]@np.linalg.inv(a.a[i]);v=np.linalg.eigvals(t)
        target=model.beta[i]*.1
        delta=np.angle(v*np.exp(-1j*target))
        j=np.argmin(abs(delta));gamma=(np.log(abs(v[j]))+1j*(target+delta[j]))/.1
        assert abs(delta[j])<.8,(mat,f,delta)
        assert abs(np.prod(v)-1)<1e-5
        for nt in pair:
            assert abs(nt.s[i,0,1]-nt.s[i,1,0])<1e-5
            assert max(np.linalg.svd(nt.s[i],compute_uv=False))<1.002
        out.append([mat,round(f/1e6),8.685889638*gamma.real,gamma.imag,
                    -20*np.log10(abs(b.s[i,1,0]/a.s[i,1,0]))/.1,
                    count[0][0],count[1][0],all(c>=t for c,t in count)])
    return out


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("estudo",type=Path)
    args=parser.parse_args()
    data=[]
    for mat in LAMINADOS:
        if not (args.estudo/mat/"cupom_120/linha.s2p").exists():continue
        series=extract(args.estudo,mat);data+=series;print(series[8])
    dest=args.estudo/"perdas/cupons_hfss.csv"
    with dest.open("w",newline="",encoding="utf8") as f:
        writer=csv.writer(f);writer.writerow(["material","MHz","atenuacao_dB_m","beta_rad_m","delta_S21_dB_m",
              "passes_consecutivos_20","passes_consecutivos_120","criterio_completo"]);writer.writerows(data)
