"""Validar a convergencia HISTORICA da fonte e identidade fisica, sem inventar passes."""
import sys,json,hashlib,re,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'r06'))
from auditar_convergencia import audit
from auditar_malha import audit as audit_mesh

def validate(root,after_solve=False):
    folder=root/'antena';config=json.loads((folder/'configuracao_hfss.json').read_text())
    assert config['modo']=='malha_fixa_validada_R06'
    source=Path(config['fonte']);raw_source=source.read_bytes()
    assert hashlib.sha256(raw_source).hexdigest()==config['sha256_fonte']
    raw=(folder/config['native']).read_bytes()
    assert re.search(rb'MaximumPasses=0\s',raw) and re.search(rb'MaxDeltaS=0\.02\s',raw)
    assert b'ForceSourceToSolve=false' in raw and b'ImportMesh=true' in raw
    for name,sha in config['secoes_fisicas_sha256'].items():
        pattern=rb"\$begin '"+name.encode()+rb"'[\s\S]*?\$end '"+name.encode()+rb"'"
        s=re.search(pattern,raw_source)[0];n=re.search(pattern,raw)[0]
        assert s==n and hashlib.sha256(n).hexdigest()==sha,name
    convergence=audit(source,write=False);assert convergence['convergencia_aprovada']
    assert convergence['criterio_s_usado']<=.02
    mesh=audit_mesh(source.parent);assert mesh['reparos_major']==0
    result=dict(fonte_convergida=True,sha256_fonte=config['sha256_fonte'],fonte=str(source),
      criterio_s_fonte=convergence['criterio_s_usado'],historico_fonte=convergence['historico'][-2:],
      novos_passes_adaptativos=0,limite_usuario_novos_adaptativos=6,
      modelo_fisico_identico=True,malha_fonte=mesh,
      nota='Convergencia pertence a R06 historica de23passes, nao a tentativa R07 interrompida por memoria.')
    if after_solve:
        newmesh=audit_mesh(folder);assert newmesh['reparos_major']==0
        result['malha_importada']=newmesh
        (folder/'malha.json').write_text(json.dumps(newmesh,indent=2),encoding='utf8')
    (folder/'fonte_malha.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--apos-solve',action='store_true')
    a=p.parse_args();r=validate(a.root,a.apos_solve)
    print(json.dumps({k:v for k,v in r.items() if k not in ('malha_fonte','malha_importada')},indent=2))
