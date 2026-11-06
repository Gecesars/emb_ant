"""Medir o lóbulo de pico de um corte HFSS de ganho realizado total em dB."""
import argparse
import csv
import math
from pathlib import Path


def medir(arquivo):
    angulo = "Theta [deg]"
    ganho = "dB(RealizedGainTotal) []"
    with arquivo.open(encoding="utf-8-sig", newline="") as entrada:
        dados = csv.DictReader(entrada)
        campos = dados.fieldnames or []
        if angulo not in campos or ganho not in campos:
            raise ValueError("Exportar Theta em graus e dB(RealizedGainTotal) em um único corte.")
        fixos = [campo for campo in campos if campo not in (angulo, ganho)]
        familias = set()
        pontos = []
        for linha in dados:
            if None in linha or any(not linha[campo] for campo in campos):
                raise ValueError(f"Linha {dados.line_num} incompleta ou com colunas extras.")
            familias.add(tuple(linha[campo] for campo in fixos))
            try:
                pontos.append((float(linha[angulo]), float(linha[ganho])))
            except ValueError as erro:
                raise ValueError(f"Ângulo ou ganho inválido na linha {dados.line_num}.") from erro
    if len(familias) != 1 or len(pontos) < 3:
        raise ValueError("Selecionar uma única frequência, plano e variação com pelo menos três ângulos.")
    pontos.sort()
    if not all(math.isfinite(x) and math.isfinite(y) for x, y in pontos):
        raise ValueError("O corte contém amostras inválidas.")
    if any(a[0] == b[0] for a, b in zip(pontos, pontos[1:])):
        raise ValueError("Ângulo duplicado. Separar as famílias antes da análise.")
    pico = max(range(len(pontos)), key=lambda i: pontos[i][1])
    nivel = pontos[pico][1] - 3

    def cruzamento(direcao):
        i = pico
        while 0 <= i + direcao < len(pontos):
            x1, y1 = pontos[i]
            i += direcao
            x2, y2 = pontos[i]
            if y2 <= nivel:
                return x1 + (nivel - y1) * (x2 - x1) / (y2 - y1)
        raise ValueError("Cruzamento fora do intervalo. Recentrar ou ampliar o corte antes de medir.")

    esquerda, direita = cruzamento(-1), cruzamento(1)
    passos = [b[0] - a[0] for a, b in zip(pontos, pontos[1:])]
    return (*pontos[pico], esquerda, direita, direita - esquerda, min(passos), max(passos))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arquivos", type=Path, nargs="+", help="CSVs de cortes assinados de Theta, um por arquivo")
    args = parser.parse_args()
    for arquivo in args.arquivos:
        try:
            ang, pico, esq, direita, largura, pmin, pmax = medir(arquivo)
            passo = f"{pmin:g}°" if math.isclose(pmin, pmax) else f"{pmin:g}°–{pmax:g}°"
            print(f"{arquivo.name} | pico {pico:.3f} dBi a {ang:g}° | -3 dB de {esq:.2f}° a {direita:.2f}° | HPBW {largura:.2f}° | passo {passo}")
        except (OSError, ValueError) as erro:
            parser.exit(1, f"{arquivo}: {erro}\n")
