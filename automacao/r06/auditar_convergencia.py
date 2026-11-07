"""Auditar S e nove amostras de campo a partir dos resultados nativos HFSS."""
import argparse
import json
import re
from pathlib import Path


def audit(project):
    native = project.read_bytes().decode('latin1')
    folder = project.with_suffix('.aedtresults')
    files = list(folder.rglob('*.EMConvData'))
    assert len(files) == 1, files
    data = files[0].read_text()
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
    for number, row in history.items():
        row['campo_dBi'] = fields.get(number, {})
        previous = fields.get(number-1, {})
        values = fields.get(number, {})
        row['delta_campo_max_dB'] = (max(abs(values[k]-previous[k]) for k in traces.values())
            if len(values) == len(previous) == len(traces) == 9 else None)
    recent = [history[k] for k in sorted(history)[-2:]]
    s_ok = len(recent) == 2 and all(r['delta_s'] is not None and r['delta_s'] <= .008 for r in recent)
    ff_ok = len(traces) == 9 and len(recent) == 2 and all(
        r['delta_campo_max_dB'] is not None and r['delta_campo_max_dB'] <= .05 for r in recent)
    native_ok = 'IsConverged=true' in data
    result = dict(projeto=str(project), cache_fonte=str(cache), convergencia_fonte=str(files[0]),
        convergiu_nativo=native_ok,
        s_008_dois_passes=s_ok, campo_005dB_nove_direcoes_dois_passes=ff_ok,
        convergencia_aprovada=bool(native_ok and s_ok and ff_ok), historico=list(history.values()))
    (project.parent/'auditoria_convergencia.json').write_text(json.dumps(result, indent=2), encoding='utf8')
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('projeto',type=Path)
    result=audit(parser.parse_args().projeto)
    print(json.dumps({k:v for k,v in result.items() if k!='historico'},indent=2))
    print(json.dumps(result['historico'][-1],indent=2))
