"""Auditoria de cada bloco HFSS, sem aceitar limite de passes como convergencia."""
from pathlib import Path
import json,re,sys,hashlib
import numpy as np
import skrf as rf
HERE=Path(__file__).parent;REPO=HERE.parents[2]
sys.path[:0]=[str(REPO/'projetos/P2M21/automacao'),str(REPO/'automacao/r06')]
from divisor_variantes_comparar import profile_matrix_solves
from auditar_malha import audit
from oito_celulas_monitorar import progress
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def run(root,network_file):
    root=Path(root);cfg=read(root/'configuracao.json');native=root/cfg['native'];results=native.with_suffix('.aedtresults')
    conv=(root/'convergencia.txt').read_text();grab=lambda x:re.search(x,conv)[1]
    passes=int(grab(r'Completed\s*:\s*(\d+)'));consec=int(grab(r'Current Consecutive Passes\s*:\s*(\d+)'))
    assert passes<=int(grab(r'Maximum\s*:\s*(\d+)'))==6
    assert abs(float(grab(r'Target\s*:\s*([\d.eE+-]+)'))-.05)<1e-10
    metas=[]
    for p in results.rglob('*.EMConvData'):
        t=p.read_text()
        if "MaxPasses='6'" in t and "MinPasses='2'" in t and abs(float(re.search("ConvTarget='([^']+)'",t)[1])-.05)<1e-10:metas.append((p,t))
    assert len(metas)==1
    mp,mt=metas[0];rows={}
    for b in mt.split("$begin 'QuantityValues'")[1:]:
        b=b.split("$end 'QuantityValues'",1)[0];ds=re.search(r'MaxMagDeltaS\(([^,]+)',b)
        row=dict(passe=int(re.search(r'PassNo=(\d+)',b)[1]),tetraedros=int(float(re.search(r'SolvedElements\(([^,]+)',b)[1])),delta_s=float(ds[1]) if ds else None)
        assert row['passe'] not in rows or rows[row['passe']]==row;rows[row['passe']]=row
    hist=[rows[k] for k in sorted(rows)];assert len(hist)==passes
    prefix=re.fullmatch(r'(DV\d+_S\d+)_V\d+',mp.stem)[1];profiles=list(mp.parent.glob(prefix+'_V*.profile'));assert len(profiles)==1
    profile=profiles[0].read_text(errors='replace').replace("\\'","'");tets={}
    for m in re.finditer(r"Name='Adaptive Pass (\d+)'(.*?)(?=Name='Adaptive Pass |\Z)",profile,re.S):
        line=next(x for x in m[2].splitlines() if x.strip().startswith("ProfileItem('Simulation Setup '"))
        tets[int(m[1])]=int(re.search(r"'Tetrahedra', (\d+)",line)[1])
    assert tets=={x['passe']:x['tetraedros'] for x in hist}
    resources=profile_matrix_solves(profile);adap=[x for x in resources if x['passe_adaptativo'] is not None]
    assert [x['passe_adaptativo'] for x in adap]==list(range(1,passes+1)) and all(x['nucleos']==14 for x in adap)
    warnings=re.findall(r'Matrix solver warning:[^\r\n]+',profile)
    messages=read(root/'mensagens.json')
    if list(results.rglob('nominalmesh.g3derr')):mesh=audit(results)
    else:
        assert not any(re.search(r'mesh repair|mesh leak|non-planar mesh|outlines.*preserv',m,re.I) for m in messages)
        mesh=dict(reparos_major=0,reparos_minor=0,arquivo_avisos_presente=False)
    raw=native.read_text(errors='replace');assert "DrivenSolverType='Direct Solver'" in raw
    assert 'Apply=true' in re.search(r"\$begin 'GlobalCurvilinear'(.*?)\$end 'GlobalCurvilinear'",raw,re.S)[1]
    net=rf.Network(str(root/network_file));assert len(net.f)==1 and net.f[0]==5.17e9;np.testing.assert_allclose(net.z0,50)
    sigma=float(np.linalg.svd(net.s[0],compute_uv=False)[0]);recip=float(np.max(abs(net.s[0]-net.s[0].T)))
    power=None
    if (root/'potencia.json').exists():
        power=read(root/'potencia.json');accepted=1-float(np.sum(abs(net.s[0]@np.ones(net.nports)/np.sqrt(net.nports))**2))
        assert abs(power['IncidentPower']['real'][0]-1)<1e-6 and abs(power['AcceptedPower']['real'][0]-accepted)<1e-5
        assert 0<power['RadiatedPower']['real'][0]<=accepted+1e-3
    delta=hist[-1]['delta_s'];converged='Converged : Yes' in conv and delta<=.05 and consec>=2
    field_monitor=None
    if power is not None:
        field_monitor=progress(root)
        assert len(field_monitor['historico'])==passes
        (root/'historico_campos.json').write_text(json.dumps(field_monitor,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    r=dict(passes=passes,delta_s=delta,consecutivos=consec,convergiu=converged,historico=hist,nucleos=[x['nucleos'] for x in adap],
       passividade_sigma_max=sigma,reciprocidade_erro=recip,malha=mesh,avisos_solver=warnings,potencia=power,monitoramento_campos=field_monitor,
       fisicamente_consistente=not warnings and sigma<=1+1e-8 and recip<1e-5 and mesh['reparos_major']==0,
       fontes_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in [cfg['native'],network_file,'configuracao.json']})
    (root/'auditoria_em.json').write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (root/'perfil_recursos.txt').write_text(profile,encoding='utf-8');(root/'convergencia_metadados.txt').write_text(mt,encoding='utf-8')
    return r,net
