"""Execucao HFSS com parada por memoria, sem repeticao automatica.

--snapshot apenas registra recursos; --run requer politica liberada explicitamente.
O guarda inicia sua propria sessao AEDT e so encerra essa arvore identificada.
"""
from pathlib import Path
import argparse
import ctypes
import datetime
import json
import os
import re
import subprocess
import time
import psutil

PROJECT = Path(__file__).resolve().parents[1]
POLICY = PROJECT / 'politica_execucao.json'
AEDT = Path('C:/Program Files/AnsysEM/v242/Win64/ansysedt.exe')
WORKSPACE = Path('D:/dev/EMBRAER/P2M19')
OOM = re.compile(r'out.of.memory|not enough (?:physical |virtual )?memory|insufficient memory|SOLVER_OUT_OF_MEMORY|memory allocation (?:failed|failure)|failed to allocate memory', re.I)


def now():
    return datetime.datetime.now().astimezone().isoformat()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(path)


def snapshot():
    vm = psutil.virtual_memory()
    result = dict(hora=now(),ram_total_bytes=vm.total,ram_livre_bytes=vm.available)
    if os.name == 'nt':
        class PERF(ctypes.Structure):
            _fields_ = [('cb',ctypes.c_ulong)] + [(n,ctypes.c_size_t) for n in [
                'CommitTotal','CommitLimit','CommitPeak','PhysicalTotal','PhysicalAvailable',
                'SystemCache','KernelTotal','KernelPaged','KernelNonpaged','PageSize']] + [
                (n,ctypes.c_ulong) for n in ['HandleCount','ProcessCount','ThreadCount']]
        p = PERF();p.cb=ctypes.sizeof(p)
        func=ctypes.WinDLL('psapi',use_last_error=True).GetPerformanceInfo
        func.argtypes=[ctypes.POINTER(PERF),ctypes.c_ulong];func.restype=ctypes.c_int
        if not func(ctypes.byref(p),p.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        result.update(commit_total_bytes=p.CommitTotal*p.PageSize,
                      commit_limite_bytes=p.CommitLimit*p.PageSize,
                      commit_livre_bytes=(p.CommitLimit-p.CommitTotal)*p.PageSize)
    return result


def decision(policy, sample, consecutive, oom=False):
    """Funcao pura, separada da terminacao de processos para ensaios seguros."""
    mib=1024**2
    count=consecutive+1 if sample['ram_livre_bytes'] < policy['ram_livre_preventiva_MiB']*mib else 0
    if oom:return 'ERRO_EXPLICITO_DE_MEMORIA',count
    if sample['ram_livre_bytes'] < policy['ram_livre_emergencia_MiB']*mib:
        return 'RAM_LIVRE_CRITICA_PARADA_PREVENTIVA',count
    if sample.get('commit_livre_bytes',float('inf')) < policy['commit_livre_emergencia_MiB']*mib:
        return 'COMPROMETIMENTO_CRITICO_PARADA_PREVENTIVA',count
    if count >= policy['amostras_consecutivas_preventiva']:
        return 'RAM_LIVRE_BAIXA_SUSTENTADA_PARADA_PREVENTIVA',count
    return None,count


def identity(proc):
    try:
        return dict(pid=proc.pid,criado=proc.create_time(),nome=proc.name(),comando=proc.cmdline())
    except (psutil.NoSuchProcess,psutil.AccessDenied):return None


def same_process(item):
    try:
        p=psutil.Process(item['pid'])
        return p if abs(p.create_time()-item['criado'])<0.001 else None
    except (psutil.NoSuchProcess,psutil.AccessDenied):return None


def owned_processes(root):
    p=same_process(root)
    if p is None:return []
    try:children=p.children(recursive=True)
    except (psutil.NoSuchProcess,psutil.AccessDenied):children=[]
    return [i for i in [identity(p)]+[identity(c) for c in children] if i]


def stop_owned(items):
    """Nao busca por nome, nao mata outros AEDTs e confere criacao contra reuso de PID."""
    records=[]
    root=same_process(items[0]) if items else None
    if root:
        try:root.suspend()
        except (psutil.NoSuchProcess,psutil.AccessDenied):pass
    for item in reversed(items):
        p=same_process(item)
        row=dict(pid=item['pid'],identidade=item['criado'])
        if p is None:row['acao']='ja_encerrado_ou_identidade_diferente'
        else:
            try:p.terminate();row['acao']='terminacao_solicitada'
            except psutil.NoSuchProcess:row['acao']='ja_encerrado'
            except psutil.AccessDenied:row['acao']='acesso_negado'
        records.append(row)
    survivors=[]
    for item in items:
        p=same_process(item)
        if p:
            try:p.wait(timeout=5)
            except psutil.TimeoutExpired:survivors.append(item)
            except psutil.NoSuchProcess:pass
    return dict(acoes=records,sobreviventes=survivors)


def new_log_lines(paths, positions):
    matches=[]
    for path in paths:
        path=Path(path)
        if not path.is_file():continue
        previous=positions.get(str(path),0)
        size=path.stat().st_size
        if size<previous:previous=0
        with path.open('rb') as f:
            f.seek(max(0,previous-512))
            raw=f.read()
        positions[str(path)]=size
        # Logs AEDT podem ser UTF-16; a remocao de NUL preserva termos ASCII.
        text=raw.replace(b'\x00',b'').decode('utf-8',errors='replace')
        matches.extend(dict(arquivo=str(path),linha=line[-1200:]) for line in text.splitlines() if OOM.search(line))
    return matches


def require_enabled(policy):
    if policy['simulacoes_suspensas']:
        raise RuntimeError('SIMULACOES SUSPENSAS PELO USUARIO; nenhum processo foi iniciado.')
    if not policy['interromper_por_memoria'] or policy['reinicio_automatico']:
        raise RuntimeError('Politica invalida: parada por memoria obrigatoria e repeticao proibida.')


def run(case, script, policy):
    require_enabled(policy)
    case=Path(case).resolve();script=Path(script).resolve()
    if not case.is_relative_to(WORKSPACE.resolve()) or not script.is_relative_to(case):
        raise ValueError('Pasta ou script fora do projeto autorizado.')
    if not script.is_file():raise FileNotFoundError(script)
    if (case/'bloqueio_memoria.json').exists():
        raise RuntimeError('Existe parada de memoria: investigar e obter nova orientacao, sem repetir.')
    running=[p.info for p in psutil.process_iter(['pid','name']) if (p.info['name'] or '').lower() in ['hf3d.exe','g3dmesher.exe','hfsscomengine.exe']]
    if running:raise RuntimeError('Existe solver ativo; nao iniciar outro: '+str(running))
    initial=snapshot();reason,_=decision(policy,initial,0)
    if reason or initial['ram_livre_bytes']<policy['ram_livre_preventiva_MiB']*1024**2:
        write_json(case/'preflight_memoria.json',dict(estado='NAO_INICIADO',motivo=reason or 'RAM_INSUFICIENTE_PARA_INICIAR',memoria=initial))
        raise RuntimeError('Memoria insuficiente antes de iniciar; evidencia registrada.')
    log=case/'guard_aedt.log'
    # Recusa sobrescrever execucao anterior, mesmo bem-sucedida.
    if (case/'processo_guard.json').exists():raise RuntimeError('Guarda ja executado nesta pasta; revisar estado antes de qualquer nova execucao.')
    logs=list(case.glob('*.log'))+list(case.glob('antena/*.log'))+[log]
    positions={str(p):p.stat().st_size for p in logs if p.exists()}
    proc=subprocess.Popen([str(AEDT),'-ng','-LogFile',str(log),'-RunScriptAndExit',str(script)],
                          creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    root=identity(psutil.Process(proc.pid))
    write_json(case/'processo_guard.json',dict(hora=now(),raiz=root,script=str(script),memoria_inicial=initial))
    count=0
    registered={(root['pid'],root['criado']):root}
    try:
        while True:
            sample=snapshot()
            logs=list(case.glob('*.log'))+list(case.glob('antena/*.log'))
            lines=new_log_lines(logs,positions)
            for item in owned_processes(root):registered[(item['pid'],item['criado'])]=item
            items=[item for item in registered.values() if same_process(item) is not None]
            code=proc.poll()
            if code is not None and not lines and not items:
                write_json(case/'guard_conclusao.json',dict(hora=now(),exit_code=code,memoria_final=sample,erro_memoria=False))
                return code
            reason,count=decision(policy,sample,count,bool(lines))
            write_json(case/'memoria_atual.json',dict(memoria=sample,amostras_baixas=count,processos=items))
            if reason:
                state={}
                for filename in ['pipeline.json','qualificacao.json','historico_passes.json']:
                    p=case/filename
                    if p.exists() and p.stat().st_size<2**20:
                        try:state[filename]=json.loads(p.read_text(encoding='utf-8-sig'))
                        except (ValueError,OSError):pass
                report=dict(hora=now(),estado='PARADA_MEMORIA',motivo=reason,memoria=sample,processos=items,mensagens=lines,estado_disponivel=state,
                            script=str(script),reinicio_automatico=False,ultimos_resultados_preservados=True)
                write_json(case/'parada_memoria.json',report)
                write_json(case/'bloqueio_memoria.json',report)
                write_json(case/'pipeline.json',dict(estado='PARADA_MEMORIA',motivo=reason,atualizado=now()))
                report['terminacao']=stop_owned(items)
                write_json(case/'parada_memoria.json',report)
                return 86
            time.sleep(policy['intervalo_monitor_s'])
    except BaseException as exc:
        # Nunca abandonar um solver sem guarda operacional.
        for item in owned_processes(root):registered[(item['pid'],item['criado'])]=item
        items=[item for item in registered.values() if same_process(item) is not None]
        report=dict(hora=now(),estado='GUARDA_FALHOU_PARADA',erro=repr(exc),processos=items,reinicio_automatico=False)
        write_json(case/'falha_guard.json',report)
        write_json(case/'bloqueio_memoria.json',report)
        report['terminacao']=stop_owned(items)
        write_json(case/'falha_guard.json',report)
        raise


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--snapshot',type=Path)
    ap.add_argument('--run',action='store_true')
    ap.add_argument('--case',type=Path)
    ap.add_argument('--script',type=Path)
    args=ap.parse_args()
    if args.snapshot:
        data=snapshot();write_json(args.snapshot,data);print(json.dumps(data));return 0
    if not args.run or not args.case or not args.script:ap.error('Use --snapshot ARQUIVO ou --run --case PASTA --script SCRIPT')
    return run(args.case,args.script,json.loads(POLICY.read_text(encoding='utf-8-sig')))


if __name__=='__main__':raise SystemExit(main())
