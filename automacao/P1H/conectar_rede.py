"""Interconnect two HFSS S matrices and 16 matched 50-ohm UT-141C cables."""
from pathlib import Path
import json,csv,re,argparse
import numpy as np
import skrf as rf
root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument("variante",choices=["Wilkinson","Radial","Soldado","Dez","Nove"])
parser.add_argument("--painel",type=Path,help="Touchstone do painel físico")
parser.add_argument("--divisor",type=Path,help="Touchstone da placa de distribuição")
parser.add_argument("--junta",type=Path,help="Touchstone da transição para a antena")
parser.add_argument("--saida",type=Path,help="Diretório para o sistema recalculado")
parser.add_argument("--passo-mhz",type=int,default=20)
args=parser.parse_args()
radial=args.variante in ("Radial","Soldado")
boardpath=root/{"Radial":"Radial_PTFE","Soldado":"Radial_Soldado","Wilkinson":"Divisor_PTFE","Dez":"Divisor_10X_PTFE","Nove":"Divisor_9X_PTFE"}[args.variante]
elements={"Nove":9,"Dez":10}.get(args.variante,8)
ports=2*elements
panelpath=root/f"Painel_{elements}X"
out=args.saida or root/("Sistema_"+args.variante)
out.mkdir(exist_ok=True)
def network(path,order):
    n=rf.Network(str(path))
    names=n.port_names
    if names is None:
        entries=re.findall(r"!\s*Port\[(\d+)\]\s*=\s*(\S+)",path.read_text(errors="replace"),re.I)
        names=[name for _,name in sorted(entries,key=lambda a:int(a[0]))]
    names=[p.strip().split(":")[0] for p in names]
    assert set(names)==set(order),(names,order)
    assert np.allclose(n.z0,50) and np.isfinite(n.s).all()
    ix=[names.index(p) for p in order]
    return n.f,n.s[:,ix,:][:,:,ix]
names=[f"E016_P{pol}"+(str(i) if i else "") for pol in "AB" for i in range(elements)]
antenna_file=f"centro.s{ports}p" if elements==9 else f"painel_{ports}portas.s{ports}p"
ff,s_ant=network(args.painel or panelpath/antenna_file,names)
fb,s_board=network(args.divisor or boardpath/f"distribuidor_EM.s{ports+2}p",["A_IN","B_IN"]+[f"{p}{i}" for p in "AB" for i in range(1,elements+1)])
assert np.allclose(ff,fb) and np.allclose(ff, [5.17e9] if elements==9 else np.arange(5090,5251,args.passo_mhz)*1e6)
# Datasheet UT-141C. Matched length along the cable between solder planes.
length={"Radial":.195,"Soldado":.192,"Wilkinson":.210,"Dez":.242,"Nove":.222}[args.variante]
if args.variante in ("Dez","Nove"):
    length=json.loads((boardpath/"comprimento_selecionado.json").read_text())["comprimento_mm"]/1000-.003
joint=np.zeros((len(ff),2,2),complex)
joint[:,0,1]=joint[:,1,0]=1
if args.variante in ("Soldado","Dez","Nove"):
    fj,joint=network(args.junta or root/"Transicao_Cabo_P1H"/"junta.s2p",["CABO","P1H"])
    if elements==9:
        mask=np.isclose(fj,5.17e9); fj=fj[mask]; joint=joint[mask]
    assert np.allclose(fj,ff)
velocity=1/(50*95.2e-12)
def dbp(v):return 10*np.log10(v)
data=[];budget=[];s2=[];pair=[]
for idx,(f,sa,sb) in enumerate(zip(ff,s_ant,s_board)):
    loss_per_m=np.interp(f/1e9,[5,10],[27.6,41.6])/30.48
    c=10**(-loss_per_m*length/20)*np.exp(-2j*np.pi*f*length/velocity)
    ii,io,oi,oo=sb[:2,:2],sb[:2,2:],sb[2:,:2],sb[2:,2:]
    sj=joint[idx]
    eye=np.eye(ports)
    to_panel=np.linalg.solve(eye-sj[1,1]*sa,c*sj[1,0]*eye)
    gamma=(c*c*sj[0,0])*eye+(c*sj[0,1])*sa@to_panel
    outputs=np.linalg.solve(eye-oo@gamma,oi)
    amp=to_panel@outputs
    si=ii+io@gamma@outputs
    s2.append(si)
    ain=np.ones(2)/np.sqrt(2)
    sent=outputs@ain
    a=amp@ain
    b=sa@a
    power=np.vdot(a,a).real
    returned=np.linalg.norm(si@ain)**2
    delivered=power-np.linalg.norm(b)**2
    joint_ref=sj[0,0]*c*sent+sj[0,1]*b
    lost_cable=(1-abs(c)**2)*(np.linalg.norm(sent)**2+np.linalg.norm(joint_ref)**2)
    lost_joint=np.linalg.norm(c*sent)**2+np.linalg.norm(b)**2-np.linalg.norm(joint_ref)**2-power
    lost_board=1+np.linalg.norm(c*joint_ref)**2-returned-np.linalg.norm(sent)**2
    assert min(lost_board,lost_cable,delivered)>=-1e-5
    assert abs(1-returned-delivered-lost_cable-lost_board-lost_joint)<1e-10
    # Common phase removed. The normalized excitation sent to HFSS sums to 1 W.
    phase=np.angle(a/a[0],deg=True)
    uniform=np.ones(ports)/np.sqrt(ports)
    gd=20*np.log10(np.max(np.abs((sa@uniform)/uniform)))
    maxcouple=20*np.log10(np.max(np.abs(sa)[np.triu_indices(ports,1)]))
    q=np.round(f/1e6).astype(int)
    data.append(dict(mhz=int(q),incident_w=float(power),sources=[dict(name=n,watts=float(abs(v)**2/power),phase_deg=float(p)) for n,v,p in zip(names,a,phase)]))
    budget.append((q,power,returned,delivered,lost_cable,lost_board,-dbp(power),loss_per_m*length,
                   np.ptp(20*np.log10(abs(a))),np.ptp(phase),gd,maxcouple,
                   -dbp(np.linalg.norm(oi[:,0])**2),-dbp(np.linalg.norm(oi[:,1])**2),20*np.log10(abs(ii[0,1])),lost_joint))
    for n,v,ph in zip(names,a,phase):pair.append((q,n,abs(v)**2,ph))
def save_rows(fname,head,rows):
    with (out/fname).open("w",newline="",encoding="utf-8-sig") as fp:
        w=csv.writer(fp);w.writerow(head.split(","));w.writerows(rows)
save_rows("balanco.csv","MHz,incidente_antenas_W,refletida_entradas_W,aceita_antenas_W,perda_cabos_W,perda_placa_W,correcao_referencia_dB,perda_cabo_ida_dB,dispersao_amplitude_dB,dispersao_fase_deg,pior_reflexao_ativa_direta_dB,maior_Sij_antenas_dB,perda_placa_A_casada_dB,perda_placa_B_casada_dB,S_AB_placa_casada_dB,perda_junta_W",budget)
save_rows("excitacoes_no_painel.csv","MHz,porta,incidente_W,fase_relativa_deg",pair)
(out/"fontes_hfss.json").write_text(json.dumps(data,indent=2))
n=rf.Network(f=ff,s=s2,z0=50,f_unit="Hz",name="painel_duas_entradas");n.port_names=["A_IN","B_IN"]
n.write_touchstone(dir=out,form="ri")
print("Center power balance and network metrics:",budget[len(budget)//2])




