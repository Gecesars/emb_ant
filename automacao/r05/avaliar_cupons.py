"""Conferir convergência, passividade e perdas dos cupons físicos R05."""
import argparse
import csv
import json
import re
from pathlib import Path

import numpy as np
import skrf


def evaluate(root):
    records = []
    cases = json.loads((root / "casos.json").read_text(encoding="utf-8"))
    for case in cases:
        directory = root / case["nome"]
        path = directory / "cupom.s2p"
        if not path.is_file():
            continue
        convergence = (directory / "convergencia.txt").read_text()
        consecutive = int(re.search(r"Current Consecutive Passes\s*:\s*(\d+)", convergence)[1])
        assert consecutive >= 2, directory
        network = skrf.Network(str(path))
        np.testing.assert_allclose(network.f, np.arange(5090, 5251, 10) * 1e6, atol=1, rtol=0)
        assert network.nports == 2 and np.allclose(network.z0, 50)
        assert np.max(np.linalg.svd(network.s, compute_uv=False)) <= 1.005
        assert np.max(abs(network.s[:, 0, 1] - network.s[:, 1, 0])) < .001
        for frequency, matrix in zip(network.f, network.s):
            transmitted = abs(matrix[1, 0]) ** 2
            reflected = abs(matrix[0, 0]) ** 2
            records.append(dict(caso=directory.name, MHz=frequency / 1e6,
                                IL_dB=-10 * np.log10(transmitted),
                                RL_dB=-10 * np.log10(reflected),
                                potencia_dissipada_ou_radiada=1 - transmitted - reflected,
                                fase_transmissao_graus=np.angle(matrix[1, 0], deg=True)))
    assert len(records) == 4 * 17, "Campanha de cupons incompleta"
    with (root / "comparacao.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=records[0])
        writer.writeheader()
        writer.writerows(records)
    return records


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("diretorio", type=Path)
    args = parser.parse_args()
    for row in evaluate(args.diretorio):
        if row["MHz"] == 5170:
            print(row)
