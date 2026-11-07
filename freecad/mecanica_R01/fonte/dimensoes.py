"""Dimensões em mm. X cresce da base para o topo. +Z aponta para a frente."""
from math import pi, sqrt, tan, acos
from pathlib import Path
import csv

FONTE = Path(__file__).resolve().parent
SAIDA = FONTE.parent
REPO = SAIDA.parents[1]
T, RI, K = 2.0, 2.0, 0.40
RO = RI + T
BA = pi / 2 * (RI + K*T)
BASE, TOPO, MEIA_BASE, MEIA_FACE = -271.0, 258.0, 41.0, 18.0
PROF_BASE, PROF_NERV = 56.0, 8.0
TRECHOS = [(-248.,-28.),(32.,TOPO)]
LADO_FLAT = MEIA_FACE + BA + PROF_NERV - RO
FIM_FLAT = BASE - BA - PROF_BASE + RO
N_Y, N_Z = 19.25, -31.0
N_FLAT = BASE - BA - (abs(N_Z)-RO)
MEIO_D, R_D = 7.0, 8.25
PASSO, PLACA_Z, CORE = 52.6, 16.61, .76
PIN = 2.50916841304063
DIV_X = PIN
DIV_F, DIV_B = -6., -7.52
R_CABO, R_PASSA = 1.7905,3.5
SUP_X = [-210.4,-105.2,0.,105.2,210.4]
BAT_X = [-253.9,253.9]
DIV_RAIL = [DIV_X-21.5,DIV_X+21.5]
CENTROS = [(i-4.5)*PASSO+PIN for i in range(10)]
ROSCA_Y = 11.0
def face_ext():
    return [(BASE,-MEIA_BASE),(-259,-MEIA_BASE),(-252,-MEIA_FACE),(TOPO,-MEIA_FACE),(TOPO,MEIA_FACE),(-252,MEIA_FACE),(-259,MEIA_BASE),(BASE,MEIA_BASE)]
def contorno_plano():
    neg=[(FIM_FLAT,-MEIA_BASE),(-259,-MEIA_BASE),(-252,-MEIA_FACE)]
    for a,b in TRECHOS:
        neg.extend([(a,-MEIA_FACE),(a,-LADO_FLAT),(b,-LADO_FLAT)])
        if b!=TOPO:neg.append((b,-MEIA_FACE))
    return neg+[(x,-y) for x,y in neg[::-1]]
def ref_bolts():
    return [(x,y) for x in SUP_X+BAT_X+DIV_RAIL for y in (-ROSCA_Y,ROSCA_Y)]
def slot(x,y,rad,half):
    # Lista (x, y, bulge); arco/linha do vértice até o seguinte.
    return [(x+rad,y-half,0),(x+rad,y+half,1),(x-rad,y+half,0),(x-rad,y-half,1)]
def duplo_d(x,y):
    # Faces planas paralelas a X. Largura entre planos no eixo Y.
    q=sqrt(R_D**2-MEIO_D**2)
    b=tan((pi-2*acos(MEIO_D/R_D))/4)
    return [(x-q,y-MEIO_D,0),(x+q,y-MEIO_D,b),(x+q,y+MEIO_D,0),(x-q,y+MEIO_D,b)]
def cabos():
    path=REPO/'fabricacao/montagem/ligacao_dos_cabos.csv'
    with path.open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))
