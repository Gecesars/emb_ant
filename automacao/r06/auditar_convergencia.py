"""Auditar S e nove amostras de campo a partir dos resultados nativos HFSS."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def audit(project, write=True, max_delta_s=.008, max_delta_campo=.05):
    native = project.read_bytes().decode('latin1')
    setup_s=[float(x) for x in re.findall(r'MaxDeltaS=([^\s]+)',native)]
    setup_ff=[float(x) for x in re.findall(r'MaxConvergenceDelta=([^\s]+)',native)]
    assert len(setup_s)==1 and len(setup_ff)==9 and len(set(setup_ff))==1
    limit_s=min(max_delta_s,setup_s[0]);limit_ff=min(max_delta_campo,setup_ff[0])
    maximum=int(re.search(r'MaximumPasses=(\d+)',native)[1])
    minimum=int(re.search(r'MinimumPasses=(\d+)',native)[1])
    folder = project.with_suffix('.aedtresults')
    files = list(folder.rglob('*.EMConvData'))
    # Ao continuar um setup, o AEDT pode conservar EMConvData da variacao
    # anterior. Selecionar pelos criterios do nativo, nao por IsConverged.
    candidates=[]
    for file in files:
        text=file.read_text()
        target=re.search(r"ConvTarget='([^']+)'",text)
        upper=re.search(r"MaxPasses='(\d+)'",text)
        lower=re.search(r"MinPasses='(\d+)'",text)
        if (target and upper and lower and abs(float(target[1])-setup_s[0])<1e-12
            and int(upper[1])==maximum and int(lower[1])==minimum):
            candidates.append((file,text))
    assert len(candidates)==1,[(str(p),p.stat().st_mtime) for p,_ in candidates]
    convergence_file,data=candidates[0]
    history = {}
    for block in data.split("$begin 'QuantityValues'")[1:]:
        block = block.split("$end 'QuantityValues'")[0]
        number = int(re.search(r'PassNo=(\d+)', block)[1])
        elements = int(float(re.search(r'SolvedElements\(([^,]+)', block)[1]))
        delta = re.search(r'MaxMagDeltaS\(([^,]+)', block)
        history[number] = dict(passe=number, tetraedros=elements,
                               delta_s=float(delta[1]) if delta else None)
    traces = {}
    for block in native.split("$begin 'CacheItem'")[1:]:
        block = block.split("$end 'CacheItem'")[0]
        title = re.search("Title='([^']+)'", block)
        trace = re.search(r'TraceID=(\d+)', block)
        if title and trace: traces[int(trace[1])] = title[1]
    fields = {}
    cache_files = sorted(folder.rglob('*.ExprCache'), key=lambda p:p.stat().st_mtime)
    assert cache_files, 'Cache de campo ausente'
    # Um setup e uma frequencia. Nao misturar revisoes anteriores da malha.
    cache = cache_files[-1]
    for line in cache.read_text().splitlines():
        m = re.match(r"(\d+)\s+Pass='(\d+)'\s+([^\s]+)", line)
        if m and int(m[1]) in traces:
            fields.setdefault(int(m[2]), {})[traces[int(m[1])]] = float(m[3])
    # EditSetup pode atribuir novos TraceID ao mesmo cache, sem reset de malha.
    # Recuperar somente os passes preservados e conferir suas identidades.
    continuation_path=project.parent/'cache_continuacao.json'
    restored=[]
    if continuation_path.exists():
        continuation=json.loads(continuation_path.read_text(encoding='utf8'))
        reference=project.parent.parent/continuation['pasta_referencia']/'auditoria_convergencia.json'
        assert hashlib.sha256(reference.read_bytes()).hexdigest()==continuation['sha256_auditoria_referencia']
        previous=json.loads(reference.read_text(encoding='utf8'))
        for row in previous['historico']:
            number=row['passe']
            if number not in history:continue
            assert history[number]['tetraedros']==row['tetraedros'],'A malha nao e continuacao da referencia'
            if not fields.get(number):
                assert len(row['campo_dBi'])==9
                fields[number]=row['campo_dBi'];restored.append(number)
    for number, row in history.items():
        row['campo_dBi'] = fields.get(number, {})
        previous = fields.get(number-1, {})
        values = fields.get(number, {})
        row['delta_campo_max_dB'] = (max(abs(values[k]-previous[k]) for k in traces.values())
            if len(values) == len(previous) == len(traces) == 9 else None)
    recent = [history[k] for k in sorted(history)[-2:]]
    s_ok = len(recent) == 2 and all(r['delta_s'] is not None and r['delta_s'] <= limit_s for r in recent)
    ff_ok = len(traces) == 9 and len(recent) == 2 and all(
        r['delta_campo_max_dB'] is not None and r['delta_campo_max_dB'] <= limit_ff for r in recent)
    native_ok = 'IsConverged=true' in data
    minimum_ok = bool(history) and max(history) >= minimum
    maximum_ok = bool(history) and max(history) <= maximum
    result = dict(projeto=str(project), cache_fonte=str(cache), convergencia_fonte=str(convergence_file),
        historicos_de_outras_configuracoes=[str(p) for p in files if p!=convergence_file],
        convergiu_nativo=native_ok,
        criterio_s_usado=limit_s,criterio_campo_dB_usado=limit_ff,
        minimo_passes_configurado=minimum,minimo_passes_atendido=minimum_ok,
        maximo_passes_configurado=maximum,maximo_passes_respeitado=maximum_ok,
        passes_cache_restaurados_da_continuacao=restored,
        s_008_dois_passes=s_ok, campo_005dB_nove_direcoes_dois_passes=ff_ok,
        convergencia_aprovada=bool(native_ok and minimum_ok and maximum_ok and s_ok and ff_ok), historico=list(history.values()))
    if write:
        (project.parent/'auditoria_convergencia.json').write_text(json.dumps(result, indent=2), encoding='utf8')
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('projeto',type=Path)
    result=audit(parser.parse_args().projeto)
    print(json.dumps({k:v for k,v in result.items() if k!='historico'},indent=2))
    print(json.dumps(result['historico'][-1],indent=2))
