"""Comparar a terminação coaxial com a mesma janela e linguetas, com e sem bobina."""
import csv
import sys
from pathlib import Path

import numpy as np
import skrf


def ler(base, caso):
    assert "Converged : Yes" in (base / caso / "convergencia.txt").read_text()
    rede = skrf.Network(str(base / caso / "cupom.s2p"))
    np.testing.assert_allclose(rede.f / 1e6, np.arange(5090, 5251, 10), rtol=0, atol=.001)
    assert rede.port_names == ["Entrada", "Saida"] and np.isfinite(rede.s).all()
    assert np.allclose(rede.z0, 50) and max(np.linalg.svd(rede.s, compute_uv=False)[:, 0]) <= 1.001
    assert max(abs(rede.s[:, 1, 0] - rede.s[:, 0, 1])) < .001
    return rede


if __name__ == "__main__":
    base = Path(sys.argv[1])
    destino = Path(sys.argv[2])
    redes = [ler(base, k) for k in ("Controle", "Com_bobina")]
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="", encoding="utf8") as out:
        w = csv.writer(out)
        w.writerow(["MHz", "IL_controle_dB", "IL_bobina_dB", "IL_incremento_dB", "RL_controle_dB", "RL_bobina_dB",
                    "fase_controle_graus", "fase_bobina_graus"])
        for i, f in enumerate(redes[0].f):
            a, b = [-r.s_db[i, 1, 0] for r in redes]
            vals = [a, b, b-a] + [-r.s_db[i, 0, 0] for r in redes] + [r.s_deg[i, 1, 0] for r in redes]
            w.writerow([round(f / 1e6), *[round(float(v), 6) for v in vals]])
