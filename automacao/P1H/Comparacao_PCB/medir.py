"""Measure the actual two-input patterns and verify the connected microwave network independently."""
import csv,json,runpy,sys
from pathlib import Path
import numpy as np
import skrf as rf
from skrf.circuit import Circuit

base=Path(__file__).resolve().parent
case=sys.argv[1]
folder=base/case;system=folder/"Sistema"
measure=runpy.run_path(str(base.parent/"medir_corte.py"))["medir"]
panel=rf.Network(str(folder/"painel.s20p"))
divider=rf.Network(str(base/"Divisor/distribuidor_EM.s22p"))
joint=rf.Network(str(base/"Junta/junta.s2p"))
coupled=rf.Network(str(system/"painel_duas_entradas.s2p"))
assert all(len(n.f)==len(panel.f) and np.allclose(n.f,panel.f,rtol=0,atol=.1) for n in (divider,joint,coupled))
assert len(panel.f)==17
atten=np.interp(panel.f/1e9,[5.,10.],[27.6,41.6])/30.48
cable_length=.251
delay=cable_length*50*95.2e-12
propagation=10**(-atten*cable_length/20)*np.exp(-2j*np.pi*panel.f*delay)
s=np.zeros((len(panel.f),2,2),complex);s[:,0,1]=s[:,1,0]=propagation
coax=rf.Network(frequency=panel.frequency,s=s,z0=50,name="UT141C")
connections=[]
for pol in "AB":
    connections.append([(Circuit.Port(panel.frequency,"Port_"+pol),0),(divider,divider.port_names.index(pol+"_IN"))])
    for i in range(10):
        name=pol+str(i+1);segment=coax**joint;segment.name=name
        antname="E016_P"+pol+(str(i) if i else "")
        connections.extend([[(divider,divider.port_names.index(name)),(segment,0)],[(segment,1),(panel,panel.port_names.index(antname))]])
error=float(np.max(abs(Circuit(connections).network.s-coupled.s)))
assert error<2e-9
inputs=json.loads((system/"fontes_hfss.json").read_text())
rows=[]
for entry in inputs:
    f=entry["mhz"];power=entry["incident_w"]
    corrected=[];unloaded=[]
    for tag in ("H","V"):
        path=system/f"Rede_{tag}_{f}.csv"
        direct=folder/f"Direto_{tag}_{f}.csv"
        theta,db=np.loadtxt(path,skiprows=1,delimiter=",",usecols=(2,3)).T
        correction=10*np.log10(power)
        data=db+correction
        g=float(data[np.isclose(theta,0)].item()); m=measure(path)
        assert len(data)==1441 and abs(m[-1]-.25)<1e-9 and abs(m[-2]-.25)<1e-9
        corrected.append((g,m[4],m[0]))
        direct_data=np.loadtxt(direct,skiprows=1,delimiter=",",usecols=(2,3))
        unloaded.append(float(direct_data[np.isclose(direct_data[:,0],0),1].item()))
        if f==5170:
            native=np.loadtxt(system/f"HFSS_{tag}_5170.csv",skiprows=1,delimiter=",")
            assert np.allclose(native[:,2],theta) and np.allclose(native[:,4],data,atol=1e-7)
    assert abs(corrected[0][0]-corrected[1][0])<1e-5 and abs(unloaded[0]-unloaded[1])<1e-6
    h,v=corrected
    rows.append([f,h[1],v[1],h[0],h[0]-16,unloaded[0],h[2],v[2]])
with (system/"resultados.csv").open("w",encoding="utf-8-sig",newline="") as out:
    w=csv.writer(out);w.writerow(["MHz","H_deg","V_deg","ganho_frontal_dBi","margem_dB","ganho_direto_dBi","pico_H_deg","pico_V_deg"])
    for r in rows:w.writerow([r[0],*[round(v,6) for v in r[1:]]])
(system/"verificacao.json").write_text(json.dumps({"frequencias":len(rows),"erro_maximo_matriz_S":error,"passo_angular_graus":.25},indent=2))
print(case,rows[8],min(r[3] for r in rows),max(r[1] for r in rows),"independent S-matrix difference",error)
