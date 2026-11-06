"""Importa para o checkout somente os resultados finais verificados de uma execução."""
import argparse
import csv
import json
import math
import re
import shutil
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("estudo",type=Path,help="diretório Comparacao_PCB depois de executar o roteiro")
study=parser.parse_args().estudo.resolve()
repo=Path(__file__).resolve().parents[1]
manifest=repo/"automacao/arquivos.json"
lookup=json.loads(manifest.read_text(encoding="utf8"))
files={}
def add(src,dst):
    f=study/src
    assert f.is_file() and f.stat().st_size,(src,"ausente ou vazio")
    files[f]=repo/dst
def mark(src,word):
    assert (study/src).read_text(errors="replace").splitlines()[-1].strip()==word,(src,word)
def conv(src):
    assert re.search(r"Converged\s*:\s*Yes",(study/src).read_text()),src
def read(f):
    with f.open(encoding="utf-8-sig",newline="") as stream:return list(csv.DictReader(stream))
conv("Divisor/convergencia_placa.txt");mark("Divisor/solucao_placa.log","PCB_FEM_COMPLETO")
conv("Junta/convergencia.txt");mark("Junta/solucao.log","FIM")
for src,dst in [("Divisor/Divisor_2x10_PTFE.aedt","hfss/alimentacao/Divisor_2x10_PTFE.aedt"),("Junta/Junta_UT141_P1H.aedt","hfss/alimentacao/Junta_UT141_P1H.aedt")]:
    add(src,dst)
for folder,items in [("Divisor",["convergencia_placa.txt","distribuidor_EM.s22p"]),("Junta",["convergencia.txt","junta.s2p"])]:
    for item in items:add(f"{folder}/{item}",f"resultados/comparacao/{folder.lower()}/{item}")
summary=read(study/"comparacao.csv");frequencies=list(range(5090,5251,10))
assert [int(r["MHz"]) for r in summary]==frequencies
brief=[]
for case,label in [("Continua","placa contínua"),("Separadas","placas separadas")]:
    conv(f"{case}/convergencia.txt");mark(f"{case}/solucao.log","FEM_OK");mark(f"{case}/Sistema/campos.log","CAMPOS_OK")
    check=json.loads((study/case/"Sistema/verificacao.json").read_text())
    assert check["frequencias"]==17 and check["erro_maximo_matriz_S"]<2e-9 and check["passo_angular_graus"]==.25,check
    rows=read(study/case/"Sistema/resultados.csv")
    assert [int(r["MHz"]) for r in rows]==frequencies
    for row,both in zip(rows,summary):
        for key in ["ganho_frontal_dBi","H_deg","V_deg"]:
            x=float(row[key]);assert math.isfinite(x) and abs(x-float(both[case+"_"+key]))<=1e-6
        assert float(row["H_deg"])>0 and float(row["V_deg"])>0
    h=[float(r["H_deg"]) for r in rows];v=[float(r["V_deg"]) for r in rows];g=[float(r["ganho_frontal_dBi"]) for r in rows]
    ok=min(h)>=81 and max(h)<=99 and min(g)>=16
    def fmt(x):return f"{x:.2f}".replace(".",",")
    brief.append(f"| {label.capitalize()} | {fmt(min(h))}° a {fmt(max(h))}° | {fmt(min(v))}° a {fmt(max(v))}° | {fmt(min(g))} dBi | "+("Atende" if ok else "Fora da meta")+" |")
    root=f"resultados/comparacao/{case}"
    add(f"{case}/P1H_{case}.aedt",f"hfss/antenas/P1H_{case}.aedt")
    for item in ["convergencia.txt","painel.s20p"]:add(f"{case}/{item}",root+"/"+item)
    for item in ["resultados.csv","Entrada_H.csv","Entrada_V.csv","balanco.csv","excitacoes_no_painel.csv","verificacao.json","painel_duas_entradas.s2p"]:
        add(f"{case}/Sistema/{item}",root+"/"+item)
for name in ["comparacao.csv","comparacao_na_banda.png","cortes_5170.png"]:add(name,"resultados/comparacao/"+name)
doc=(study/"comparacao_P1H.md").read_text(encoding="utf8").replace("../KiCad_Antenas/Cotacao_JLCPCB.md","../fabricacao/cotacao/Cotacao_JLCPCB.md").replace("medido no FEM","calculado no FEM")
for name in ["comparacao.csv","comparacao_na_banda.png","cortes_5170.png"]:doc=doc.replace("]("+name+")","](../resultados/comparacao/"+name+")")
for source,target in files.items():
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)
    lookup["Comparacao_PCB/"+source.relative_to(study).as_posix()]=target.relative_to(repo).as_posix()
(repo/"documentacao/comparacao_P1H.md").write_text(doc,encoding="utf8")
lookup["Comparacao_PCB/comparacao_P1H.md"]="documentacao/comparacao_P1H.md"
manifest.write_text(json.dumps(dict(sorted(lookup.items())),indent=2,ensure_ascii=False)+"\n",encoding="utf8")
readme=repo/"README.md"
old=readme.read_text(encoding="utf8")
new="**Estado da revisão de PCB:** [relatório HFSS](documentacao/comparacao_P1H.md) · [tabela por frequência](resultados/comparacao/comparacao.csv). Resultados nas duas entradas externas, nos 17 pontos simulados:\n\n| Montagem | Horizontal | Vertical | Menor ganho frontal | Critérios de H e ganho |\n|---|---:|---:|---:|---|\n"+"\n".join(brief)+"\n\n"
out,count=re.subn(r"\*\*Estado da revisão de PCB:\*\*.*?(?=\*\*Materiais e montagem:\*\*)",lambda _:new,old,flags=re.S)
assert count==1
readme.write_text(out,encoding="utf8")
print("\n".join(brief))
