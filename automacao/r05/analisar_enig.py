"""Conferir cupons ENIG e sua influência na rede com antena congelada em 5,17 GHz."""
import argparse
import csv
import json
from pathlib import Path

import numpy as np
import skrf

from rede_carregada import LoadedPanel, repo


def validate(path):
    network = skrf.Network(str(path))
    np.testing.assert_allclose(network.f, np.arange(5090, 5251, 10) * 1e6, atol=1)
    assert np.allclose(network.z0, 50)
    assert np.isfinite(network.s).all()
    singular = float(np.linalg.svd(network.s, compute_uv=False).max())
    reciprocal = float(abs(network.s - network.s.transpose(0, 2, 1)).max())
    assert singular <= 1.005
    assert reciprocal <= .02
    names = [name.strip() for name in network.port_names]
    inputs = [names.index(pol + "_IN") for pol in "AB"]
    outputs = [i for i in range(len(names)) if i not in inputs]
    wave = np.ones(2) / np.sqrt(2)
    outgoing = network.s[:, :, inputs] @ wave
    power_out = np.sum(abs(outgoing[:, outputs]) ** 2, axis=1)
    power_ref = np.sum(abs(outgoing[:, inputs]) ** 2, axis=1)
    excess = -10 * np.log10(power_out)
    assert (1 - power_out - power_ref >= -1e-5).all()
    record = dict(singular_max=singular, erro_reciprocidade=reciprocal,
                  perda_excedente_min_dB=float(excess.min()),
                  perda_excedente_max_dB=float(excess.max()),
                  perda_excedente_centro_dB=float(excess[8]),
                  reflexao_centro_W=float(power_ref[8]))
    return record, excess


def main(work):
    output = work / "enig/analise"
    output.mkdir(exist_ok=True)
    record = {"hipotese": "Os campos e S20 da antena ficam congelados em 5,17 GHz. "
              "As matrizes dos demais blocos variam nos 17 pontos. "
              "Não é um resultado de ganho do painel na banda.", "cupons": {}}
    for stage, suffix in [("1x2", "s6p"), ("1x5", "s12p")]:
        new, new_loss = validate(work / ("enig/%s/divisor.%s" % (stage, suffix)))
        old, old_loss = validate(repo / ("resultados/r02/rede/R02_%s.%s" % (stage, suffix)))
        convergence = (work / "enig" / stage / "convergencia.txt").read_text()
        assert "Converged : Yes" in convergence
        assert "Current Consecutive Passes : 2" in convergence
        record["cupons"][stage] = dict(cobre=old, enig=new,
            acrescimo_min_dB=float((new_loss - old_loss).min()),
            acrescimo_max_dB=float((new_loss - old_loss).max()))
    model = LoadedPanel(work / "face40", work, enig=True)
    cases = {"construido": [288, 134, 142],
             "alternativa_nao_construida": [271.792113, 145.04592889, 135.16068993]}
    rows = []
    for tag, lengths in cases.items():
        gains = []
        for f in np.arange(5090, 5251, 10) * 1e6:
            model.set_frequency(f, freeze_antenna=True)
            metrics, _, _ = model.calculate(lengths)
            gains.append(metrics["ganho_frontal_dBi"])
            assert metrics["perda_rede_W"] >= 0
            rows.append(dict(caso=tag, MHz=f / 1e6, **metrics))
            if f == 5170e6:
                record[tag + "_centro"] = metrics
        record[tag + "_sensibilidade"] = dict(
            ganho_com_antena_congelada_min_dBi=min(gains),
            ganho_com_antena_congelada_max_dBi=max(gains))
    (output / "resumo.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    with (output / "sensibilidade_antena_congelada.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("diretorio", type=Path)
    main(parser.parse_args().diretorio)
