# -*- coding: utf-8 -*-
"""Aferir em duas portas a representação nominal da transição N existente."""
import os
import sys
import traceback


os.environ["P1H_BOBINA"] = os.path.join(os.environ["P1H_R05"], "cupons")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "r01"))
from bobina_hfss import log, solve


ports = [
    dict(name="Entrada", x=-288, y=-19.25, z=-31, axis="X", inner=3.5 / 2.3, outer=3.5),
    dict(name="Saida", x=-260, y=-19.25, z=-31, axis="X", inner=.45975, outer=1.515)
]
try:
    solve("Conector_N", oDesktop, ports=ports, conductivity=1.6e7)
except:
    log(traceback.format_exc())
