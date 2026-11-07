"""Limite de projeto para N: retorno 25 dB e perda 0,15 dB, fase de reflexão livre.

A perda de 0,15 dB é uma hipótese de projeto, não especificação do 082-6784.
Os campos e a matriz da antena continuam congelados no centro da banda.
"""
import csv
import json
from pathlib import Path
import argparse
import numpy as np

from rede_carregada import LoadedPanel


def main(work):
    model = LoadedPanel(work / "face40", work, enig=True)
    lengths = [290, 132, 135]
    front = model.patterns["H"][np.flatnonzero(model.angles == 0)[0]]
    r = 10 ** (-25 / 20)
    t = 10 ** (-.15 / 20)
    ranges = []
    for f in np.arange(5090, 5251, 10) * 1e6:
        model.set_frequency(f, freeze_antenna=True)
        phase = np.angle(model.s[0, 1])
        values = []
        for phi in np.linspace(-np.pi, np.pi, 73):
            reflection = r * np.exp(1j * phi)
            other = r * np.exp(1j * (2 * phase + np.pi - phi))
            transmission = t * np.exp(1j * phase)
            block = np.array([[other, transmission], [transmission, reflection]])
            assert np.linalg.svd(block, compute_uv=False).max() < 1
            model.s[:2, :2] = model.s[2:4, 2:4] = block
            incident, _ = model.waves(lengths)
            field = front @ incident[model.antenna_indexes]
            gain = 10 * np.log10(np.sum(abs(field) ** 2))
            values.append(float(gain))
        ranges.append(dict(MHz=f / 1e6, ganho_min_dBi=min(values), ganho_max_dBi=max(values)))
    output = work / "enig/analise"
    with (output / "conector_25dB_hipotese.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(ranges[0]))
        writer.writeheader()
        writer.writerows(ranges)
    record = dict(hipotese=__doc__, comprimentos_mm=lengths,
        fase_transmissao="Modelo nominal; dois conectores iguais",
        perda_insercao_dB=.15, retorno_dB=25, pontos_fase=73,
        minimo_dBi=min(r["ganho_min_dBi"] for r in ranges),
        maximo_dBi=max(r["ganho_max_dBi"] for r in ranges))
    (output / "conector_25dB_hipotese.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("diretorio", type=Path)
    main(parser.parse_args().diretorio)
