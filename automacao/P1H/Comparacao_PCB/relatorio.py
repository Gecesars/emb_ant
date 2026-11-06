"""Compare the two KiCad panel models at the same input reference planes."""
import csv,json,re
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline

root=Path(__file__).resolve().parent
styles={"Separadas":("#596f80","--"),"Continua":("#007665","-")}
labels={"Separadas":"Dez PCBs individuais","Continua":"Uma PCB contínua"}
def read(p):
    with p.open(encoding="utf-8-sig") as f:return list(csv.DictReader(f))
def fmt(v,n=2):return f"{v:.{n}f}".replace(".",",")
def span(a):return fmt(min(a))+" a "+fmt(max(a))
def bounds(conv):
    t=conv.read_text()
    assert "Converged : Yes" in t
    return re.search(r"Completed\s*:\s*(\d+)",t)[1],float(re.search(r"Current\s*:\s*([.\d]+)",t)[1])
def profile(c):
    r=read(root/c/"Sistema/resultados.csv")
    return {key:np.array([float(item[key]) for item in r]) for key in r[0]}
series={c:profile(c) for c in styles}
fig,axes=plt.subplots(3,1,figsize=(8.1,7.3),sharex=True,layout="constrained")
for ax,key,label in zip(axes,["ganho_frontal_dBi","H_deg","V_deg"],["Ganho frontal (dBi)","Abertura H (°)","Abertura V (°)"]):
    for c,(col,ls) in styles.items():
        a=series[c];ax.plot(a["MHz"]/1000,a[key],ls,color=col,marker="o",markersize=3.2,lw=1.7,label=labels[c])
    if key=="ganho_frontal_dBi":ax.axhline(16,linewidth=1,color="#963e28",linestyle=":",label="Mínimo de 16 dBi")
    if key=="H_deg":ax.axhline(99,linewidth=1,color="#963e28",linestyle=":",label="Limite superior de 99°")
    ax.set_ylabel(label);ax.grid(alpha=.22);ax.spines[["right","top"]].set_visible(False)
axes[0].legend(ncol=3,fontsize=8);axes[-1].set_xlabel("Frequência (GHz)")
fig.suptitle("Painel P1H com divisor e vinte cabos de 254 mm")
fig.savefig(root/"comparacao_na_banda.png",dpi=160);plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(9,3.8),layout="constrained")
for c,(col,ls) in styles.items():
    for ax,tag,extent in zip(axes,["H","V"],[90,12]):
        path=root/c/"Sistema"/f"Entrada_{tag}.csv"
        th,g=np.loadtxt(path,delimiter=",",skiprows=1,usecols=(2,3)).T
        ax.plot(th,g,color=col,ls=ls,lw=1.8,label=labels[c]);ax.set_xlim(-extent,extent);ax.set_ylim(-2,19)
        ax.set_title("Horizontal · YZ" if tag=="H" else "Vertical · XZ");ax.set_xlabel("Ângulo em relação a +Z (°)")
        ax.grid(alpha=.2);ax.spines[["right","top"]].set_visible(False)
axes[0].set_ylabel("Ganho realizado total (dBi)");axes[0].legend(fontsize=8);fig.suptitle("Diagramas a 5,17 GHz")
fig.savefig(root/"cortes_5170.png",dpi=155);plt.close(fig)
keys=["H_deg","V_deg","ganho_frontal_dBi"]
with (root/"comparacao.csv").open("w",encoding="utf-8-sig",newline="") as out:
    w=csv.writer(out);w.writerow(["MHz"]+[c+"_"+k for c in styles for k in keys])
    for i,f in enumerate(series["Continua"]["MHz"]):w.writerow([int(f)]+[series[c][k][i] for c in styles for k in keys])
lines=["# Coluna em PCB contínua e em dez PCBs individuais","",
       "Verificação no Ansys HFSS 2024 R2. Metas de projeto: abertura horizontal de 81° a 99° e ganho frontal realizado de pelo menos 16 dBi em +Z. A vertical pode ser mais estreita que 7°.","",
       "| Montagem | H a 5,17 GHz | V a 5,17 GHz | Ganho a 5,17 GHz | Menor ganho | Frequência do mínimo | Margem mínima | Resultado nos 17 pontos |","|---|---:|---:|---:|---:|---:|---:|---|"]
for c,a in series.items():
    i=int(np.argmin(a["ganho_frontal_dBi"]));m=a["ganho_frontal_dBi"][i]
    ok=all((a['H_deg']>=81)&(a['H_deg']<=99)&(a['ganho_frontal_dBi']>=16))
    lines.append(f"| {labels[c]} | {fmt(a['H_deg'][8])}° | {fmt(a['V_deg'][8])}° | {fmt(a['ganho_frontal_dBi'][8])} dBi | {fmt(m)} dBi | {fmt(a['MHz'][i]/1000)} GHz | {fmt(m-16)} dB | "+("Atende" if ok else "Fora da meta")+" |")
lines.extend(["","| Frequência (GHz) | H separadas (°) | V separadas (°) | Ganho separadas (dBi) | H contínua (°) | V contínua (°) | Ganho contínua (dBi) |","|---:|---:|---:|---:|---:|---:|---:|"])
for i,f in enumerate(series["Continua"]["MHz"]):lines.append("| "+" | ".join([fmt(f/1000)]+[fmt(series[c][k][i]) for c in styles for k in keys])+" |")
lines+=["","## Verificação dentro da banda","",
        "As bordas e o centro fazem parte dos 17 pontos FEM discretos, separados por 10 MHz. Para verificar a resolução da varredura, uma spline cúbica construída com os nove pontos de 20 MHz foi comparada aos oito pontos intermediários efetivamente resolvidos. Abaixo constam o maior resíduo absoluto nesses pontos e o menor ganho estimado na interpolação dos 17 pontos em passos de 1 MHz.","",
        "| Montagem | Intervalo H calculado no FEM | Intervalo V | Resíduo H | Resíduo de ganho | Mínimo interpolado |","|---|---:|---:|---:|---:|---:|"]
for c,a in series.items():
    f=a["MHz"]
    def residual(k):return np.max(np.abs(CubicSpline(f[::2],a[k][::2])(f[1::2])-a[k][1::2]))
    dense=CubicSpline(f,a["ganho_frontal_dBi"])(np.arange(5090,5251))
    lines.append(f"| {labels[c]} | {span(a['H_deg'])}° | {span(a['V_deg'])}° | {fmt(residual('H_deg'),3)}° | {fmt(residual('ganho_frontal_dBi'),3)} dB | {fmt(min(dense),3)} dBi |")
lines+=["","## Espessura e montagem","",
    "Na sessão do usuário, o arquivo synth_dipole_array_2024_v9 contém o elemento R1 de 825 MHz com a variável array_pcb_thickness de 1,6 mm. A geometria P1H de 5,17 GHz usa o material P1H_RO4350B_DesignDk e vai de Z = 16,61 a 17,37 mm. O núcleo é de 0,76 mm, com Dk de projeto 3,66 e tan δ de 0,0037. O divisor usa 1,52 mm de PTFE ZYF300CA-C, com Dk 2,94 e tan δ de 0,0016. Esses são os núcleos selecionados nos Gerbers cotados. Cobre, máscara e acabamento contribuem para a espessura final da PCB. [Oferta da JLCPCB](https://jlcpcb.com/news/rogers-ptfe-high-frequency-pcb-available) · [Cotação do projeto](../KiCad_Antenas/Cotacao_JLCPCB.md)","",
    "O painel contínuo usa um único sólido RO4350B de 501,7125 × 28,3125 mm. A referência usa dez sólidos de 28,3125 × 28,3125 mm. Os nove vãos entre placas medem 24,2875 mm na referência. O cobre, o passo em X de 52,6 mm e os dez refletores individuais PEC de 48,3125 × 36 mm são os mesmos. Ambas as geometrias incluem as ampliações de cobre para os pads de 1,20 mm, as sondas de 0,726 mm e as vias com furo de 0,40 mm. Os furos de sonda de 0,85 mm têm casquilho e preenchimento condutor nominal. A condutividade superficial do cobre foi aplicada a 35 µm. Os refletores estão 16,61 mm abaixo da face inferior dos radiadores.","",
    "A comparação usa co-simulação. O HFSS resolveu cada painel inteiro com acoplamento entre suas vinte portas e resolveu o divisor de 22 portas e a transição soldada em modelos EM próprios. As matrizes complexas foram ligadas a vinte linhas de 50 Ω UT-141C, cada uma com 251 mm distribuídos e 3 mm de terminação FEM. Foram incluídas a atenuação do coaxial, a fase de propagação, as perdas de cobre e dielétrico e as reflexões múltiplas. As entradas A e B recebem 0,5 W a 0°. O HFSS recombinou os campos para as amplitudes e fases incidentes em cada painel. O ganho frontal considera 1 W incidente nas duas entradas externas. H e V são as aberturas a −3 dB dos cortes YZ e XZ, amostrados a 0,25°.","",
    "A simulação cobre a propagação interna dos cabos. O espalhamento externo depende da posição de montagem da placa divisora, das rotas das malhas coaxiais, do radome e dos suportes. A camada de acabamento ENIG, os filetes reais de solda, o relevo das tolerâncias e a máscara residual fora das janelas dos radiadores são aproximações de prototipagem. O modelo eletromagnético das antenas usa o laminado nominal exposto, inclusive nos vãos da placa longa.","","## Convergência","",
    "| Modelo | Passes | ΔS final |","|---|---:|---:|"]
for label,path in [(labels[c],root/c/"convergencia.txt") for c in styles]+[("Divisor",root/"Divisor/convergencia_placa.txt"),("Transição soldada",root/"Junta/convergencia.txt")]:
    n,d=bounds(path);lines.append(f"| {label} | {n} | {fmt(d,5)} |")
lines+=["","O scikit-rf verificou a interligação das matrizes S de forma independente. Os cortes com a referência de potência das entradas externas foram exportados e conferidos também nos relatórios nativos de 5,17 GHz. [Comparação por frequência](comparacao.csv) · [Curvas na banda](comparacao_na_banda.png) · [Cortes no centro](cortes_5170.png)"]
(root/"comparacao_P1H.md").write_text("\n".join(lines)+"\n",encoding="utf8")
print("\n".join(lines[4:8]))
