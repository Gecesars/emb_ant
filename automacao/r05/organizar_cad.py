"""Preparar a entrega mecânica R05 sem copiar malhas ou temporários."""
import argparse
import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np

repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo / "automacao/r02"))
from ramais import sample, lengths


def main(work):
    source = work / "candidato290"
    dest = repo / "freecad/mecanica_R05"
    dest.mkdir(exist_ok=True)
    verification = json.loads((source / "cad/verificacao.json").read_text())
    assert not verification["interferencias_mm3"]
    assert verification["folga_minima_entre_capas_mm"] > .4
    for name in ["01_Refletor_dobrado.FCStd", "01_Refletor_dobrado.step",
                 "02_Refletor_planificado.FCStd", "04_Refletor_CORTE_1a1.dxf",
                 "05_Refletor_marcacao_dobras.dxf"]:
        shutil.copy2(work / "candidato288/refletor" / name, dest / name)
    shutil.copy2(work / "candidato288/refletor/verificacao.json", dest / "verificacao_chapa.json")
    assembly = work / 'candidato290_solido/cad/Painel_R05.FCStd'
    if not assembly.is_file():
        assembly = source / 'cad/Painel_R05.FCStd'
    shutil.copy2(assembly, dest / "P1H_R05_compacta.FCStd")
    shutil.copy2(source / "cad/verificacao.json", dest / "verificacao_cad.json")
    for name in ["frente.png", "traseira.png"]:
        shutil.copy2(source / "cad" / name, dest / name)
    for name in ["caminhos.json", "enlaces.json", "chicote_ajustado.json"]:
        shutil.copy2(source / "compacta" / name, dest / name)
    routes = json.loads((dest / "caminhos.json").read_text())
    routes.update(json.loads((dest / "enlaces.json").read_text()))
    with (repo / "freecad/mecanica_R02/chicote_26_cabos.csv").open(encoding="utf-8-sig", newline="") as stream:
        records = list(csv.DictReader(stream))
    for record in records:
        edges = routes[record["cabo"]]
        record["eixo_entre_interfaces_mm"] = round(sum(lengths(edges)), 6)
        record["menor_Z_externo_mm"] = round(float(sample(edges, .1)[:, 2].min()) - 1.7905, 6)
        assert abs(record["eixo_entre_interfaces_mm"] - verification["comprimentos_mm"][record["cabo"]]) < 1e-5
    assert len(records) == 26
    with (dest / "chicote_26_cabos.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    hashes = {str(path.relative_to(repo)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in [repo / "fabricacao/gerbers" / name for name in
                           ["Gerber_P1H_Coluna_10.zip", "Gerber_R02_Inferior.zip", "Gerber_R02_Superior.zip"]]}
    record = dict(coaxial_total_mm=sum(row["eixo_entre_interfaces_mm"] for row in records),
                  percurso_por_radiador_mm=290+132+135,
                  menor_Z_externo_mm=min(row["menor_Z_externo_mm"] for row in records),
                  gerbers_inalterados_sha256=hashes,
                  estado="Geometria validada; aprovação de RF depende do FEM integral da R05")
    (dest / "rastreabilidade.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("diretorio", type=Path)
    main(parser.parse_args().diretorio)
