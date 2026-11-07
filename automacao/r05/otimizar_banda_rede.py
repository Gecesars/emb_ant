"""Selecionar comprimentos pela pior frequência, com antena congelada no centro."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.optimize import differential_evolution

from rede_carregada import LoadedPanel, NOMINAL
from ensaiar_rede import cable


def main(work, branch_max=160, seed=5, input_min=None):
    model = LoadedPanel(work / "face40", work, enig=True)
    frequencies = np.arange(5090, 5251, 10) * 1e6
    matrices = []
    for frequency in frequencies:
        model.set_frequency(frequency, freeze_antenna=True)
        matrices.append(model.s)
    matrices = np.stack(matrices)
    field = model.patterns["H"][np.flatnonzero(model.angles == 0)[0]]
    indexes = np.array([[model.lookup[a], model.lookup[b]] for a, b, _, _ in model.connections])
    kinds = np.array([-1 if index is None else index for _, _, index, _ in model.connections])
    corrections = np.array([correction for _, _, _, correction in model.connections])
    excitation = matrices @ model.excitation
    identity = np.eye(len(model.s))[None]

    def gains(lengths):
        lengths = np.r_[lengths, 0]
        distance = lengths[kinds] + corrections
        transfer = cable(frequencies[:, None], distance[None, :])
        links = np.zeros_like(matrices)
        links[:, indexes[:, 0], indexes[:, 1]] = transfer
        links[:, indexes[:, 1], indexes[:, 0]] = transfer
        outgoing = np.linalg.solve(identity - matrices @ links, excitation[..., None])[..., 0]
        incident = model.excitation + (links @ outgoing[..., None])[..., 0]
        feeding = incident[:, model.antenna_indexes]
        return 10 * np.log10(np.sum(abs(feeding @ field.T) ** 2, axis=1))

    def objective(lengths):
        values = gains(lengths)
        return -values.min()

    bounds = list(zip(NOMINAL, NOMINAL + 30))
    if input_min is not None:
        bounds[0] = (input_min, NOMINAL[0] + 30)
    bounds[2] = (NOMINAL[2], branch_max)
    result = differential_evolution(objective, bounds,
                                    seed=seed, popsize=20, maxiter=200, tol=2e-7, polish=True)
    cases = {"construido": np.array([288, 134, 142]), "minimax": result.x,
             "minimax_arredondado": np.round(result.x)}
    record = dict(hipotese="Antena S20 e campos congelados em 5,17 GHz; "
                  "não substitui FEM integral ou varredura dos radiadores.",
                  solver_sucesso=bool(result.success), iteracoes=int(result.nit), casos={})
    for tag, lengths in cases.items():
        values = gains(lengths)
        metrics = []
        for frequency, expected in zip(frequencies, values):
            model.set_frequency(frequency, freeze_antenna=True)
            actual, _, _ = model.calculate(lengths)
            assert abs(expected - actual["ganho_frontal_dBi"]) < 1e-8
            metrics.append(dict(MHz=frequency / 1e6, **actual))
        record["casos"][tag] = dict(comprimentos_mm=list(map(float, lengths)),
            ganho_antena_congelada_min_dBi=float(values.min()),
            ganho_antena_congelada_max_dBi=float(values.max()), resultados=metrics)
    output = work / ("enig/analise/minimax_max%03d_in%03d_seed%d.json" % (branch_max, input_min or NOMINAL[0], seed))
    output.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps({key: {k: v for k, v in value.items() if k != "resultados"}
                      for key, value in record["casos"].items()}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("diretorio", type=Path)
    parser.add_argument("--ramal-max", type=float, default=160)
    parser.add_argument("--seed", type=int, default=5)
    parser.add_argument("--entrada-min", type=float)
    args = parser.parse_args()
    main(args.diretorio, args.ramal_max, args.seed, args.entrada_min)
