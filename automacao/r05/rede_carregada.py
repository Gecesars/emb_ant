"""Combinar campos embutidos da placa montada com as matrizes físicas da alimentação."""
import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
import skrf
from scipy.linalg import block_diag
from scipy.optimize import differential_evolution


repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo / "automacao/r02"))
from ensaiar_rede import cable


FREQUENCY = 5.17e9
NOMINAL = np.array([271.792113, 132.0, 130.0])


def read_pattern(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    columns = list(rows[0])
    component_names = [name for name in columns if name.startswith(("re(", "im("))]
    assert len(component_names) == 4
    angles = np.array([float(row["Theta [deg]"]) for row in rows])
    values = np.array([[float(row[name]) for name in component_names] for row in rows])
    fields = np.stack([values[:, 0] + 1j * values[:, 1],
                       values[:, 2] + 1j * values[:, 3]], axis=-1)
    powers = np.sum(abs(fields) ** 2, axis=1)
    gains = 10 ** (np.array([float(row["dB(RealizedGainTotal) []"]) for row in rows]) / 10)
    valid = powers > powers.max() * .01
    calibration = np.median(gains[valid] / powers[valid])
    np.testing.assert_allclose(powers[valid] * calibration, gains[valid], rtol=1e-8)
    return angles, fields * np.sqrt(calibration)


def beam(angles, gain):
    front = (angles >= -90) & (angles <= 90)
    indexes = np.flatnonzero(front)
    peak = indexes[np.argmax(gain[front])]
    level = gain[peak] - 3
    left = peak
    right = peak
    while left > 0 and gain[left] >= level:
        left -= 1
    while right < len(gain) - 1 and gain[right] >= level:
        right += 1
    assert left < peak < right
    low = np.interp(level, gain[left:left + 2], angles[left:left + 2])
    high = np.interp(level, gain[right - 1:right + 1][::-1], angles[right - 1:right + 1][::-1])
    return high - low, low, high


class LoadedPanel:
    def __init__(self, work, components=None, enig=False):
        components = components or work
        self.frequency = FREQUENCY
        reference = repo / "resultados/r02/rede"
        antenna = skrf.Network(str(work / "antena_direta/antena.s20p"))
        self.antenna_ports = [name.strip() for name in antenna.port_names]
        paths = [
            ("NA", components / "cupons/Conector_N/cupom.s2p"),
            ("NB", components / "cupons/Conector_N/cupom.s2p"),
            ("CA", components / "cupons/Bobina_r090/cupom.s2p"),
            ("CB", components / "cupons/Bobina_r090/cupom.s2p"),
            ("R", components / "enig/1x2/divisor.s6p" if enig else reference / "R02_1x2.s6p"),
            ("L", components / "enig/1x5/divisor.s12p" if enig else reference / "R02_1x5.s12p"),
            ("U", components / "enig/1x5/divisor.s12p" if enig else reference / "R02_1x5.s12p"),
            ("ANT", work / "antena_direta/antena.s20p"),
        ]
        port_names = []
        matrices = []
        self.networks = []
        for prefix, path in paths:
            network = skrf.Network(str(path))
            self.networks.append((prefix, network))
            index = np.argmin(abs(network.f - FREQUENCY))
            assert abs(network.f[index] - FREQUENCY) < 1
            assert np.allclose(network.z0, 50)
            matrices.append(network.s[index])
            port_names.extend(prefix + "/" + name.strip() for name in network.port_names)
        self.s = block_diag(*matrices)
        self.antenna_s = antenna.s[0]
        self.lookup = {name: i for i, name in enumerate(port_names)}
        assert len(self.lookup) == len(port_names)
        self.antenna_indexes = [self.lookup["ANT/" + name] for name in self.antenna_ports]
        self.inputs = [self.lookup["N" + pol + "/Entrada"] for pol in "AB"]
        self.excitation = np.zeros(len(self.s), dtype=complex)
        self.excitation[self.inputs] = 1 / np.sqrt(2)
        self.patterns = {}
        for axis in "HV":
            patterns = []
            for port in self.antenna_ports:
                angles, field = read_pattern(work / "antena_direta/padroes" / (port + "_" + axis + ".csv"))
                patterns.append(field)
            self.angles = angles
            self.patterns[axis] = np.stack(patterns, axis=-1)
        self.connections = []
        for pol in "AB":
            self.connections.extend([
                ("N" + pol + "/Saida", "C" + pol + "/Entrada", 0, -8),
                ("C" + pol + "/Saida", "R/" + pol + "_IN", None, -5.5),
                ("R/" + pol + "1", "L/" + pol + "_IN", 1, -3),
                ("R/" + pol + "2", "U/" + pol + "_IN", 1, -3),
            ])
            for offset, group in [(0, "L"), (5, "U")]:
                for number in range(1, 6):
                    self.connections.append((group + "/" + pol + str(number),
                        "ANT/E%02d_%s" % (number + offset, pol), 2, -1.5 - 20.61))

    def set_frequency(self, frequency, freeze_antenna=False):
        """Variar blocos da rede; congelar a antena só para análise de sensibilidade."""
        if frequency != FREQUENCY and not freeze_antenna:
            raise ValueError("Os campos embutidos disponíveis são apenas de 5,17 GHz.")
        matrices = []
        for prefix, network in self.networks:
            target = FREQUENCY if prefix == "ANT" and freeze_antenna else frequency
            index = np.argmin(abs(network.f - target))
            if abs(network.f[index] - target) >= 1:
                raise ValueError("Frequência indisponível em " + prefix)
            matrices.append(network.s[index])
        self.s = block_diag(*matrices)
        self.antenna_s = matrices[-1]
        self.frequency = frequency

    def waves(self, lengths):
        links = np.zeros_like(self.s)
        for first, second, index, correction in self.connections:
            length = correction + (0 if index is None else lengths[index])
            i, j = self.lookup[first], self.lookup[second]
            links[i, j] = links[j, i] = cable(self.frequency, length)
        outgoing = np.linalg.solve(np.eye(len(self.s)) - self.s @ links, self.s @ self.excitation)
        incident = self.excitation + links @ outgoing
        return incident, outgoing

    def calculate(self, lengths):
        incident, outgoing = self.waves(lengths)
        feeding = incident[self.antenna_indexes]
        cuts = {axis: 10 * np.log10(np.maximum(np.sum(abs(field @ feeding) ** 2, axis=-1), 1e-30))
                for axis, field in self.patterns.items()}
        widths = {axis: beam(self.angles, gain) for axis, gain in cuts.items()}
        center = np.flatnonzero(self.angles == 0)[0]
        np.testing.assert_allclose(cuts["H"][center], cuts["V"][center], atol=.005)
        reflected = np.sum(abs(outgoing[self.inputs]) ** 2)
        assert reflected <= 1.001
        antenna_reflected = self.antenna_s @ feeding
        antenna_accepted = np.sum(abs(feeding) ** 2 - abs(antenna_reflected) ** 2)
        phases = np.angle(feeding / np.mean(feeding), deg=True)
        return dict(ganho_frontal_dBi=float(cuts["H"][center]),
                    H_graus=float(widths["H"][0]), V_graus=float(widths["V"][0]),
                    H_esquerda=float(widths["H"][1]), H_direita=float(widths["H"][2]),
                    refletida_W=float(reflected), aceita_antena_W=float(antenna_accepted),
                    perda_rede_W=float(1 - reflected - antenna_accepted),
                    dispersao_fase_graus=float(np.ptp(phases)),
                    dispersao_amplitude_dB=float(np.ptp(20 * np.log10(abs(feeding)))),
                    comprimentos_mm=list(map(float, lengths))), cuts, feeding

    def objective(self, lengths):
        metrics, _, _ = self.calculate(lengths)
        outside = max(81 - metrics["H_graus"], 0, metrics["H_graus"] - 99)
        return -metrics["ganho_frontal_dBi"] + outside ** 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("diretorio", type=Path)
    parser.add_argument("--componentes", type=Path)
    parser.add_argument("--enig", action="store_true")
    args = parser.parse_args()
    model = LoadedPanel(args.diretorio, args.componentes, args.enig)
    baseline, _, _ = model.calculate(NOMINAL)
    result = differential_evolution(model.objective, list(zip(NOMINAL, NOMINAL + 21)),
                                    seed=5, popsize=12, maxiter=70, tol=1e-6, polish=True)
    best, cuts, feeding = model.calculate(result.x)
    record = dict(metodo="Campos embutidos e rede de matrizes HFSS, centro de banda",
                  nominal=baseline, candidato=best, solver_sucesso=bool(result.success))
    output = args.diretorio / "rede_carregada"
    output.mkdir(exist_ok=True)
    (output / "candidato.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    np.savez_compressed(output / "campos_candidato.npz", theta=model.angles,
                        H=cuts["H"], V=cuts["V"], excitacoes=feeding)
    print(json.dumps(record, indent=2))
