"""Circuito por frequencia com campos HFSS reais, cabos ideais e aceite17pontos."""
import argparse,csv,json,sys,hashlib
from pathlib import Path
import numpy as np
import skrf
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'r06'))
from circuito import Circuit

FREQ=np.arange(5090,5251,10,dtype=int)
def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,allow_nan=False),encoding='utf8')

def one(root,folder,mhz,out):
    meta=json.loads((folder/'campos.json').read_text())
    assert meta['frequencia_MHz']==mhz and meta['campos']==40
    assert len(list((folder/'padroes').glob('*.csv')))==40
    results={};out.mkdir(parents=True,exist_ok=True)
    for coil in ['corrigida','bruta','sem']:
        c=Circuit(root,coil,antenna_folder=folder,frequency_hz=mhz*1e6)
        result,theta,cuts,feed=c.calculate();results[coil]=result
        assert all(np.isfinite(result[k]).all() for k in ['ganho_frontal_realizado_dBi',
          'abertura_H_graus','abertura_V_graus','VSWR_ativo_AB','VSWR_outro_porto_casado_AB'])
        # Uma reflexao ativa >=1 invalida VSWR mesmo que a rede total seja passiva.
        gamma=c.Sout@np.ones(2,complex)
        assert np.max(abs(gamma))<1,'Reflexao ativa >=1: VSWR nao finito, nao aprovar'
        if coil=='corrigida':
            c.export(out/'componentes')
            np.savez_compressed(out/'campos.npz',theta=theta,H=cuts['H'],V=cuts['V'],excitacoes=feed)
            with (out/'diagrama.csv').open('w',newline='',encoding='utf8') as f:
                w=csv.writer(f);w.writerow(['theta_graus','H_dBi','V_dBi']);w.writerows(zip(theta,cuts['H'],cuts['V']))
    save(out/'resultado.json',results)
    return results

def compare(root,actual):
    source=root.parent/'R06_sem_cabos/circuito/resultado.json'
    previous=json.loads(source.read_text())['corrigida'];values={}
    for key,limit in [('ganho_frontal_realizado_dBi',.05),('abertura_H_graus',.5),('abertura_V_graus',.1),
                      ('VSWR_ativo_AB',.05),('VSWR_outro_porto_casado_AB',.05)]:
        delta=np.asarray(actual[key])-np.asarray(previous[key])
        values[key]=dict(delta=delta.tolist(),limite=limit,aprovado=bool(np.max(abs(delta))<=limit))
    result=dict(referencia=str(source),sha256_referencia=hashlib.sha256(source.read_bytes()).hexdigest(),
                comparacoes=values,estavel=all(v['aprovado'] for v in values.values()))
    save(root/'comparacao_centro.json',result)
    assert result['estavel'],'Centro mudou alem dos limites de estabilidade; investigar antes da banda'

def combine(root):
    paths=[root/'circuito/pontos'/str(m)/'componentes' for m in FREQ]
    output=root/'circuito/componentes';output.mkdir(parents=True,exist_ok=True)
    for file in paths[0].glob('*.s*p'):
        networks=[skrf.Network(str(p/file.name)) for p in paths]
        assert all(n.port_names==networks[0].port_names for n in networks)
        assert all(len(n.f)==1 and abs(n.f[0]-m*1e6)<1 for n,m in zip(networks,FREQ))
        n=skrf.Network(frequency=skrf.Frequency.from_f(FREQ*1e6,unit='Hz'),
                       s=np.concatenate([x.s for x in networks]),z0=50)
        n.port_names=networks[0].port_names;n.write_touchstone(str(output/file.name))
        reread=skrf.Network(str(output/file.name));assert reread.port_names==n.port_names
        np.testing.assert_allclose(reread.s,n.s,atol=1e-12,rtol=0)
    manifests=[json.loads((p/'manifesto.json').read_text()) for p in paths]
    common=manifests[0]
    assert all(m['conexoes']==common['conexoes'] and m['entradas']==common['entradas'] for m in manifests)
    common.pop('frequencia_Hz');common['frequencias_Hz']=(FREQ*1e6).tolist()
    common['fontes_por_frequencia']={str(m):v['fontes'] for m,v in zip(FREQ,manifests)}
    common['nota']='17 pontos HFSS reais; cabos ideais com fase dependente da frequencia e sem atenuacao.'
    save(output/'manifesto.json',common)

def main(root,stage):
    config=json.loads((root/'antena/configuracao_hfss.json').read_text())
    if config.get('modo')=='malha_fixa_validada_R06':
        assert json.loads((root/'antena/fonte_malha.json').read_text())['fonte_convergida']
    else:assert json.loads((root/'antena/auditoria_convergencia.json').read_text())['convergencia_aprovada']
    if stage=='centro':
        result=one(root,root/'centro/5170',5170,root/'circuito/centro')
        compare(root,result['corrigida']);print(json.dumps(result['corrigida'],indent=2));return
    net=skrf.Network(str(root/'antena/antena_banda.s20p'))
    assert net.nports==20 and len(net.f)==17 and len(net.port_names)==20
    np.testing.assert_allclose(net.f,FREQ*1e6,atol=1,rtol=0)
    assert np.isfinite(net.s).all() and np.allclose(net.z0,50)
    reciprocity=float(np.max(abs(net.s-net.s.transpose(0,2,1))))
    passivity=float(np.max(np.linalg.svd(net.s,compute_uv=False)))
    assert reciprocity<1e-6 and passivity<=1.005
    rows=[]
    for k,mhz in enumerate(FREQ):
        folder=root/'pontos'/str(mhz);part=net[k];part.port_names=net.port_names
        part.write_touchstone(str(folder/'antena.s20p'))
        result=one(root,folder,int(mhz),root/'circuito/pontos'/str(mhz))['corrigida'];rows.append(result)
    combine(root)
    checks=[dict(frequencia_MHz=int(r['frequencia_Hz']/1e6),G=r['ganho_frontal_realizado_dBi'],
        H=r['abertura_H_graus'],V=r['abertura_V_graus'],
        VSWR_ativo_A=r['VSWR_ativo_AB'][0],VSWR_ativo_B=r['VSWR_ativo_AB'][1],
        VSWR_casado_A=r['VSWR_outro_porto_casado_AB'][0],VSWR_casado_B=r['VSWR_outro_porto_casado_AB'][1],
        atende=r['criterios_numericos_atendidos']) for r in rows]
    with (root/'circuito/banda17.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(checks[0]));w.writeheader();w.writerows(checks)
    summary=dict(frequencias=17,ganho_min_dBi=min(r['G'] for r in checks),
        ganho_min_frequencia_MHz=min(checks,key=lambda r:r['G'])['frequencia_MHz'],
        H_min_graus=min(r['H'] for r in checks),H_max_graus=max(r['H'] for r in checks),
        VSWR_max=max(r[k] for r in checks for k in ['VSWR_ativo_A','VSWR_ativo_B','VSWR_casado_A','VSWR_casado_B']),
        criterios_rf_atendidos=all(r['atende'] for r in checks),
        pontos_reprovados_MHz=[r['frequencia_MHz'] for r in checks if not r['atende']],
        antena_sigma_max=passivity,antena_erro_reciprocidade=reciprocity,
        metodo='PCBs separadas; campos reais17pontos; cabos ideais somente fase; 2x0.5W/0graus.',
        qualificacao_final_pendente='auditoria da malha e comparacao Nexxim em17pontos',pontos=checks)
    save(root/'circuito/resultado_banda.json',summary);print(json.dumps(summary,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('stage',choices=['centro','banda'])
    a=p.parse_args();main(a.root,a.stage)
