# -*- coding: utf-8 -*-
"""Executar os cupons R05 com as mesmas portas e referências do ensaio R01."""
import json
import os
import sys
import traceback


folder = os.path.dirname(os.path.abspath(__file__))
os.environ["P1H_BOBINA"] = os.path.join(os.environ["P1H_R05"], "cupons")
sys.path.insert(0, os.path.join(folder, "..", "r01"))
from bobina_hfss import log, root, solve


with open(os.path.join(root, "casos.json")) as stream:
    cases = json.load(stream)
for case in cases:
    name = case["nome"]
    if os.path.isfile(os.path.join(root, name, "cupom.s2p")):
        continue
    try:
        solve(name, oDesktop)
    except:
        log(traceback.format_exc())
