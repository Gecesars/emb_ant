"""Circuito linear R06: matrizes HFSS completas, acoplamento e linhas sem perda."""
import argparse, csv, hashlib, json, sys
from pathlib import Path
import numpy as np
import skrf
from scipy.linalg import block_diag

REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO/'automacao/r05'))
from rede_carregada import beam, read_pattern
F=5.17e9
V=1/(50*95.2e-12)


def line(mm,air_mm=0):
    return np.exp(-2j*np.pi*F*(mm/1000/V+air_mm/1000/299792458))


def read(path):
    n=skrf.Network(str(path));k=int(np.argmin(abs(n.f-F)))
    assert abs(n.f[k]-F)<1 and np.allclose(n.z0,50)
    assert n.port_names and np.isfinite(n.s).all()
    assert np.max(abs(n.s-n.s.transpose(0,2,1)))<1e-6
    assert np.max(np.linalg.svd(n.s,compute_uv=False))<=1.005
    return n,k


class Circuit:
    def __init__(self,root,coil='corrigida',antenna_folder=None,superior_path=None,lengths=None):
        self.root=root;self.parts={};self.names=[];self.links=[];self.coil=coil
        if lengths is None:
            config=root/'configuracao_circuito.json'
            lengths=json.loads(config.read_text(encoding='utf8'))['comprimentos_mm'] if config.exists() else (290,132,135)
        self.lengths=tuple(float(x) for x in lengths)
        input_mm,trunk_mm,branch_mm=self.lengths
        self.antenna_folder=antenna_folder or root/'antena'
        old=root/'cupons' if (root/'cupons').is_dir() else root.parent/'R05_Correcao/cupons'
        paths=[('L',root/'divisor_inferior/divisor.s18p'),
               ('U',superior_path or root/'divisor_superior/divisor.s12p'),('ANT',self.antenna_folder/'antena.s20p')]
        if coil!='sem':paths.extend((('CA',old/'Bobina_r090/cupom.s2p'),('CB',old/'Bobina_r090/cupom.s2p')))
        matrices=[];self.sources={}
        for tag,path in paths:
            n,k=read(path);s=n.s[k].copy()
            if tag.startswith('C') and coil=='corrigida':
                control_path=old/'Controle_fechado/cupom.s2p'
                control,ck=read(control_path)
                self.sources['CONTROLE']=dict(arquivo=str(control_path),sha256=hashlib.sha256(control_path.read_bytes()).hexdigest())
                # Dois acessos iguais de 6 mm: remover apenas a atenuacao do
                # cupom reto de 12 mm. Preservar fase e reflexoes da bobina.
                s/=abs(control.s[ck,1,0])
                assert max(np.linalg.svd(s,compute_uv=False))<=1.00001
            names=[tag+'/'+p.strip().split(':')[0] for p in n.port_names]
            self.parts[tag]=dict(names=names,s=s,network=n,index=k)
            self.names.extend(names);matrices.append(s)
            self.sources[tag]=dict(arquivo=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        self.S=block_diag(*matrices);self.idx={p:i for i,p in enumerate(self.names)}
        assert len(self.idx)==len(self.names)
        for pol in 'AB':
            self.link('L/R'+pol+'1','L/'+pol+'_IN',trunk_mm-.36)
            self.link('L/R'+pol+'2','U/'+pol+'_IN',trunk_mm-.36)
            for group,offset in [('L',0),('U',5)]:
                for i in range(1,6):
                    self.link(group+'/'+pol+str(i),'ANT/E%02d_%s'%(i+offset,pol),branch_mm-.18-1,.965)
            if coil!='sem':self.link('C'+pol+'/Saida','L/R'+pol+'_IN',-4.18)
        input_names=['L/R'+p+'_IN' if coil=='sem' else 'C'+p+'/Entrada' for p in 'AB']
        self.inputs=[self.idx[p] for p in input_names]
        self.input_phase=line(input_mm-.18 if coil=='sem' else input_mm-8)
        self.K=np.zeros_like(self.S)
        used=[]
        for a,b,mm,air in self.links:
            i,j=self.idx[a],self.idx[b];used.extend([i,j]);self.K[i,j]=self.K[j,i]=line(mm,air)
        assert len(set(used))==len(used)
        assert set(used+self.inputs)==set(range(len(self.names)))
        E=np.zeros((len(self.names),2),complex);E[self.inputs,range(2)]=self.input_phase
        self.B=np.linalg.solve(np.eye(len(self.S))-self.S@self.K,self.S@E)
        self.A=E+self.K@self.B
        np.testing.assert_allclose(self.B,self.S@self.A,atol=1e-12)
        self.Sout=self.B[self.inputs]*self.input_phase
        np.testing.assert_allclose(self.Sout,self.Sout.T,atol=1e-8)
        assert max(np.linalg.svd(self.Sout,compute_uv=False))<=1.00001
        self.antidx=[self.idx[p] for p in self.parts['ANT']['names']]

    def link(self,a,b,mm,air=0):self.links.append((a,b,mm,air))

    def calculate(self,excitation=None):
        excitation=np.ones(2,complex)/np.sqrt(2) if excitation is None else np.asarray(excitation,complex)
        incident=self.A@excitation;outgoing=self.B@excitation
        feeding=incident[self.antidx];b=self.Sout@excitation
        cuts={};uniform={}
        for axis in 'HV':
            fields=[]
            for p in self.parts['ANT']['names']:
                theta,field=read_pattern(self.antenna_folder/'padroes'/(p.split('/')[1]+'_'+axis+'.csv'))
                fields.append(field)
            fields=np.stack(fields,axis=-1)
            cuts[axis]=10*np.log10(np.maximum(np.sum(abs(fields@feeding)**2,axis=-1),1e-30))
            uniform[axis]=10*np.log10(np.maximum(np.sum(abs(fields@(np.ones(20)/np.sqrt(20)))**2,axis=-1),1e-30))
            with (self.antenna_folder/('Centro_'+axis+'.csv')).open(encoding='utf-8-sig',newline='') as f:
                rows=list(csv.DictReader(f))
            original=np.array([float(r['dB(RealizedGainTotal) []']) for r in rows])
            np.testing.assert_allclose(uniform[axis],original,atol=.005)
        widths={ax:beam(theta,cut) for ax,cut in cuts.items()};center=int(np.argmin(abs(theta)))
        np.testing.assert_allclose(cuts['H'][center],cuts['V'][center],atol=.005)
        accepted=float(np.sum(abs(incident[self.antidx])**2-abs(outgoing[self.antidx])**2))
        reflection=float(np.sum(abs(b)**2));power=float(np.sum(abs(excitation)**2))
        losses={tag:float(np.sum(abs(incident[[self.idx[p] for p in part['names']]])**2-
                               abs(outgoing[[self.idx[p] for p in part['names']]])**2))
                for tag,part in self.parts.items() if tag!='ANT'}
        np.testing.assert_allclose(accepted+reflection+sum(losses.values()),power,atol=1e-10)
        assert min(losses.values())>=-1e-8
        active=[float((1+abs(b[i]/excitation[i]))/(1-abs(b[i]/excitation[i])))
                if abs(excitation[i])>1e-10 else None for i in range(2)]
        matched=[float((1+abs(self.Sout[i,i]))/(1-abs(self.Sout[i,i]))) for i in range(2)]
        g=float(cuts['H'][center]);h=float(widths['H'][0])
        result=dict(frequencia_Hz=F,bobina=self.coil,comprimentos_fisicos_mm=self.lengths,ganho_frontal_realizado_dBi=g,
                    abertura_H_graus=h,abertura_V_graus=float(widths['V'][0]),
                    VSWR_ativo_AB=active,VSWR_outro_porto_casado_AB=matched,
                    potencia_incidente_W=power,refletida_W=reflection,aceita_antena_W=accepted,
                    perdas_blocos_W=losses,perda_linhas_W=0,
                    excitacoes_antena_amplitude_pp_dB=float(np.ptp(20*np.log10(abs(feeding)))),
                    excitacoes_antena_fase_pp_graus=float(np.ptp(np.angle(feeding/np.mean(feeding),deg=True))),
                    criterios_numericos_atendidos=bool(g>=16 and 81<=h<=99 and all(x is not None and x<1.5 for x in active)
                                                       and max(matched)<1.5))
        return result,theta,cuts,feeding

    def export(self,output):
        output.mkdir(parents=True,exist_ok=True)
        freq=skrf.Frequency.from_f([F],unit='Hz')
        model=skrf.Network(frequency=freq,s=self.Sout[None],z0=50)
        model.port_names=['N_A','N_B']
        model.write_touchstone(str(output/'painel'))
        # Componentes de um ponto e linhas ideais para reproduzir no Circuit.
        component_paths={}
        for tag,part in self.parts.items():
            n=skrf.Network(frequency=freq,s=part['s'][None],z0=50)
            n.port_names=[p.split('/')[1] for p in part['names']]
            n.write_touchstone(str(output/('R06_'+tag)))
            component_paths[tag]='R06_'+tag+'.s%dp'%len(part['names'])
            reread=skrf.Network(str(output/component_paths[tag]))
            assert reread.port_names==n.port_names
            np.testing.assert_allclose(reread.s,n.s,atol=1e-12,rtol=0)
        for i,(_,_,mm,air) in enumerate(self.links):
            t=line(mm,air);n=skrf.Network(frequency=freq,s=np.array([[[0,t],[t,0]]]),z0=50)
            n.port_names=['1','2']
            n.write_touchstone(str(output/('TL%02d'%i)))
        t=self.input_phase
        n=skrf.Network(frequency=freq,s=np.array([[[0,t],[t,0]]]),z0=50)
        n.port_names=['1','2'];n.write_touchstone(str(output/'TL_IN'))
        manifest=dict(componentes=component_paths,conexoes=self.links,
                      entradas=[self.names[i] for i in self.inputs],fontes=self.sources,
                      comprimentos_fisicos_mm=self.lengths,
                      nota='Somente 5.17 GHz. Linhas sem atenuacao; plano de referencia corrigido para terminais HFSS.')
        (output/'manifesto.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);args=parser.parse_args()
    conv=json.loads((args.root/'antena/auditoria_convergencia.json').read_text())
    assert conv['convergencia_aprovada'],'Campo/S da PCB ainda nao convergiu'
    output=args.root/'circuito';output.mkdir(exist_ok=True)
    results={}
    for mode in ['corrigida','bruta','sem']:
        circuit=Circuit(args.root,mode);metrics,theta,cuts,feed=circuit.calculate();results[mode]=metrics
        if mode=='corrigida':
            circuit.export(output/'componentes')
            np.savez_compressed(output/'campos.npz',theta=theta,H=cuts['H'],V=cuts['V'],excitacoes=feed)
            with (output/'diagrama.csv').open('w',newline='',encoding='utf8') as f:
                w=csv.writer(f);w.writerow(['theta_graus','H_dBi','V_dBi']);w.writerows(zip(theta,cuts['H'],cuts['V']))
    (output/'resultado.json').write_text(json.dumps(results,indent=2),encoding='utf8')
    print(json.dumps(results,indent=2))
