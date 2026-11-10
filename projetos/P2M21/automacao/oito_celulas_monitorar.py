"""Leitura somente dos metadados de adaptacao R14; nao conecta ao solver."""
from pathlib import Path
import json,re,os
ROOT=Path('D:/dev/EMBRAER/P2M21/R14_Oito_Celulas')
def progress(root=None):
    ROOT=Path(root or os.environ.get('P2M21_OITO_ROOT',str(globals()['ROOT'])))
    cfg=json.loads((ROOT/'configuracao.json').read_text());native=(ROOT/cfg['native']).read_text(errors='replace')
    results=(ROOT/cfg['native']).with_suffix('.aedtresults');found=[]
    for path in results.rglob('*.EMConvData'):
        text=path.read_text();m=re.search(r"ConvTarget='([^']+)'",text)
        if m and abs(float(m[1])-cfg['max_delta_s'])<1e-12 and ("MaxPasses='%d'"%cfg['max_passes']) in text and ("MinPasses='%d'"%cfg['min_passes']) in text:found.append((path,text))
    if not found:return dict(estado='sem_historico_adaptativo')
    assert len(found)==1,[str(p) for p,t in found]
    path,text=found[0];hist={};traces={};fields={}
    for block in text.split("$begin 'QuantityValues'")[1:]:
        block=block.split("$end 'QuantityValues'",1)[0]
        num=int(re.search(r'PassNo=(\d+)',block)[1]);ds=re.search(r'MaxMagDeltaS\(([^,]+)',block)
        hist[num]=dict(passe=num,tetraedros=int(float(re.search(r'SolvedElements\(([^,]+)',block)[1])),delta_s=float(ds[1]) if ds else None)
    for block in native.split("$begin 'CacheItem'")[1:]:
        block=block.split("$end 'CacheItem'",1)[0];title=re.search("Title='([^']+)'",block);trace=re.search(r'TraceID=(\d+)',block)
        if title and trace:traces[int(trace[1])]=title[1]
    for p in sorted(results.rglob('*.ExprCache'),key=lambda p:p.stat().st_mtime):
        for line in p.read_text().splitlines():
            m=re.match(r"(\d+)\s+Pass='(\d+)'\s+([^\s]+)",line)
            if m and int(m[1]) in traces:fields.setdefault(int(m[2]),{})[traces[int(m[1])]]=float(m[3])
    for num,row in hist.items():
        row['campos_dBi']=fields.get(num,{})
        prev=fields.get(num-1,{})
        row['delta_campo_max_dB']=max(abs(row['campos_dBi'][k]-prev[k]) for k in traces.values()) if len(prev)==len(row['campos_dBi'])==len(traces)==9 else None
    return dict(fonte=str(path),nativo_convergiu='IsConverged=true' in text,cache_somente_monitoramento=True,historico=[hist[k] for k in sorted(hist)])
if __name__=='__main__':
    p=progress();print(json.dumps({**p,'historico':p.get('historico',[])[-2:]},indent=2))
