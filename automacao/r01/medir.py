"""Medir os dois cortes do HFSS e verificar os dados de duas portas no plano dos N."""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

import numpy as np
import skrf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "P1H"))
from medir_corte import medir


def resumo_rede(caminho, frequencias):
    rede = skrf.Network(str(caminho))
    assert rede.nports == 2 and np.allclose(rede.z0, 50)
    np.testing.assert_allclose(rede.f / 1e6, frequencias, rtol=0, atol=.001)
    assert np.isfinite(rede.s).all()
    sigma = np.linalg.svd(rede.s, compute_uv=False)[:, 0]
    assert max(sigma) <= 1.005, "Erro de passividade"
    reciprocidade = abs(rede.s[:, 0, 1] - rede.s[:, 1, 0])
    assert max(reciprocidade) < .02, "Erro de reciprocidade"
    onda = np.ones(2, dtype=complex) / np.sqrt(2)
    refletida = rede.s @ onda
    retorno = -20 * np.log10(np.maximum(abs(refletida / onda), 1e-15))
    return retorno, np.sum(abs(refletida)**2, axis=1), float(max(sigma)), float(max(reciprocidade))


def ler_corte(arquivo, mhz, phi):
    with arquivo.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    np.testing.assert_allclose([float(row["Freq [GHz]"]) * 1000 for row in rows], mhz, rtol=0, atol=.001)
    np.testing.assert_allclose([float(row["Phi [deg]"]) for row in rows], phi, rtol=0, atol=1e-6)
    a = np.array([float(row["Theta [deg]"]) for row in rows])
    np.testing.assert_allclose(np.sort(a), np.arange(-180, 180.01, .25), rtol=0, atol=1e-6)
    front = float(next(row["dB(RealizedGainTotal) []"] for row in rows if float(row["Theta [deg]"]) == 0))
    pico, ganho, esq, direita, largura, _, _ = medir(arquivo)
    return front, pico, ganho, esq, direita, largura


def analisar(work, dest, apenas_centro):
    conv = (work / "convergencia.txt").read_text(encoding="utf-8-sig")
    assert re.search(r"Converged\s*:\s*Yes", conv), "Malha sem convergência documentada"
    atual=int(re.search(r"Current Consecutive Passes\s*:\s*(\d+)",conv)[1])
    minimo=int(re.search(r"Target Consecutive Passes\s*:\s*(\d+)",conv)[1])
    assert atual>=minimo, "Número insuficiente de passes consecutivos"
    frequencias = [5170] if apenas_centro else list(range(5090, 5251, 10))
    tag = "Centro" if apenas_centro else "Discreta"
    retorno, refletida, sigmax, rec = resumo_rede(work / ("centro.s2p" if apenas_centro else "painel.s2p"), frequencias)
    registros = []
    for i, f in enumerate(frequencias):
        h = ler_corte(work / f"{tag}_H_{f}.csv", f, 90)
        v = ler_corte(work / f"{tag}_V_{f}.csv", f, 0)
        assert abs(h[0] - v[0]) < .005, "Ganho frontal inconsistente"
        h_ok = h[3] <= 0 <= h[4] and 81 <= h[5] <= 99
        registros.append(dict(MHz=f, ganho_frontal_dBi=h[0], H_graus=h[5], V_graus=v[5],
            pico_H_graus=h[1], pico_V_graus=v[1], H_esquerda=h[3], H_direita=h[4],
            V_esquerda=v[3], V_direita=v[4], RL_ativo_A_dB=retorno[i, 0], RL_ativo_B_dB=retorno[i, 1],
            potencia_refletida_W=refletida[i], atende_H=bool(h_ok), atende_ganho=bool(h[0] >= 16)))
    dest.mkdir(parents=True, exist_ok=True)
    with (dest / f"metricas_{tag}.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=registros[0]); writer.writeheader(); writer.writerows(registros)
    audit = dict(pontos=len(registros), frequencias_MHz=frequencias,
        sigma_maxima_S=sigmax, reciprocidade_erro_max_abs=rec,
        todos_os_pontos_atendem=all(row["atende_H"] and row["atende_ganho"] for row in registros))
    (dest / f"verificacao_{tag}.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    return registros


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("estudo", type=Path)
    parser.add_argument("destino", type=Path)
    parser.add_argument("--centro", action="store_true")
    args = parser.parse_args()
    analisar(args.estudo, args.destino, args.centro)
