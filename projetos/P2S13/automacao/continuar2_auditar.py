"""Gates: geometria/setup/cache intactos e somente passes7/8 adicionados."""
from pathlib import Path
import json,hashlib,re,sys,difflib,os
ROOT=Path(os.environ.get('P2S13_ROOT','D:/dev/EMBRAER/P2S13/R03_Continuacao_M00'));REF=ROOT/'referencia6'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def block(t,n):return t.split("$begin '"+n+"'",1)[1].split("$end '"+n+"'",1)[0]
def geom(t):return [v.split("$end 'GeometryPart'",1)[0] for v in t.split("$begin 'GeometryPart'")[1:]]
def history(p):return [[int(a),int(b),None if c=='N/A' else float(c)] for a,b,c in re.findall(r'^\s*(\d+)\|\s*(\d+)\|\s*([\d.eE+-]+|N/A)\|',p.read_text(),re.M)]
def main(stage):
    cfg=json.loads((ROOT/'configuracao.json').read_text());a=(REF/cfg['native']).read_text(errors='replace');b=(ROOT/cfg['native']).read_text(errors='replace')
    assert geom(a)==geom(b) and len(geom(a))>0
    for name in ['BoundarySetup','MaterialDef','MeshSetup','CoordinateSystems']:
        if "$begin '"+name+"'" in a:assert block(a,name)==block(b,name),name
    sources=re.findall(r'SourceEntry\([^\n]+',b)
    count=len(cfg['portas']);assert count in [4,6]
    assert len(sources)==count and all(abs(float(re.search("Magnitude='([0-9.e+-]+)W'",s)[1])-1/count)<1e-10 and "Phase='0deg'" in s for s in sources)
    expected=block(a,'AnalysisSetup').replace('MaximumPasses=6','MaximumPasses=8').replace('MinimumPasses=2','MinimumPasses=8')
    actual=block(b,'AnalysisSetup')
    if expected!=actual:
        (ROOT/'setup_diferencas.txt').write_text(''.join(difflib.unified_diff(expected.splitlines(True),actual.splitlines(True))),encoding='utf-8')
        raise AssertionError('Mudanca inesperada no setup; ver setup_diferencas.txt')
    data=dict(aprovado=True,geometria_blocos=len(geom(a)),geometria_materiais_fronteiras_malha_inalterados=True,alteracoes_setup=['MaximumPasses6->8','MinimumPasses2->8'],native_sha256=sha(ROOT/cfg['native']))
    origin=json.loads((ROOT/'origem.json').read_text())
    for e in origin['referencias']:assert sha(REF/e['arquivo'])==e['sha256']
    if stage=='preparar':
        checked=[]
        for e in origin['arquivos_resultados_copiados']:
            p=ROOT/e['arquivo']
            if p.name in ['native.adp','current.ngmesh'] or p.name.startswith('fields.'):
                assert sha(p)==e['sha256'],str(p);checked.append(e['arquivo'])
        assert len(checked)>=8 and any(p.endswith('native.adp') for p in checked)
        assert history(REF/'convergencia.txt')==history(ROOT/'antes_convergencia.txt')
        data.update(cache_malha_campos_preservados=checked,historico6_preservado=True);out='preparacao_auditada.json'
    elif stage=='final':
        old=history(REF/'convergencia.txt');new=history(ROOT/'convergencia.txt')
        assert len(old)==6 and len(new)==8 and old==new[:6],(old,new)
        sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'projetos/P2M21/automacao'))
        from oito_celulas_monitorar import progress
        full=progress(ROOT)['historico'];previous=json.loads((REF/'historico_passes.json').read_text())['historico']
        assert len(full)==8 and full[:6]==previous,'Metadados completos dos seis passes mudaram'
        source=Path(origin['fonte']);assert sha(source/cfg['native'])==origin['native_sha256']
        for e in origin['arquivos_resultados_copiados']:assert sha(source/e['arquivo'])==e['sha256']
        data.update(primeiros_seis_identicos=True,campos_e_DeltaS_completos_preservados=True,origem6_nao_alterada=True,novos_passes=[7,8],historico=new);out='continuidade_auditada.json'
    else:raise ValueError(stage)
    (ROOT/out).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');print(out,'APROVADO')
if __name__=='__main__':main(sys.argv[1])
