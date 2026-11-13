"""Fila local finita: acompanha R02 e executa R03/R04 serialmente, sem cron."""
from pathlib import Path
from datetime import datetime
import hashlib,json,os,subprocess,sys,time,traceback
import psutil

REPO=Path(__file__).resolve().parents[3]
WORK=Path('D:/dev/EMBRAER/P2M19')
ROOT=WORK/'Campanha_72mm_20261113'
CASES=['R02_16x2_72mm','R03_72mm_ref162','R04_72mm_ref146']
ROOT.mkdir(exist_ok=True)
LOCK=ROOT/'fila.lock'

def save(name,obj):
    temp=ROOT/(name+'.tmp')
    temp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    os.replace(temp,ROOT/name)

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def now():return datetime.now().astimezone().isoformat()
def log(message):
    with (ROOT/'fila.log').open('a',encoding='utf-8') as f:f.write(now()+' '+message+'\n')
    print(message,flush=True)

def solver_active():
    return [p.pid for p in psutil.process_iter(['name']) if (p.info['name'] or '').lower() in ['hf3d.exe','g3dmesher.exe']]

def wait_resources(case):
    start=time.time()
    while True:
        if (ROOT/'PARAR_APOS_CASO').exists():raise InterruptedError('Parada solicitada antes de novo caso')
        active=solver_active();free=psutil.virtual_memory().available/2**30
        if not active and free>=16 and psutil.disk_usage('D:/').free>4*2**30:return
        save('estado.json',dict(estado='AGUARDANDO_RECURSOS',proximo=case.name,solvers=active,livre_GiB=free,atualizado=now()))
        if time.time()-start>3600:raise RuntimeError('Recursos indisponíveis por uma hora; nenhum aplicativo alheio foi encerrado')
        time.sleep(15)

def inspect_case(case):
    cfg=read(case/'configuracao.json')
    assert cfg['max_passes']==6 and cfg['max_delta_s']==.05 and cfg['nucleos']==14
    assert cfg['frequencia_GHz']==5.17 and not cfg['sweep']
    assert cfg['passo_horizontal_mm']==72 and cfg['niveis_radiadores']==16 and cfg['colunas']==2
    assert len(cfg['portas'])==16 and cfg['potencia_por_porta_W']==.0625 and cfg['fase_graus']==0
    assert read(case/'cad/intersecoes.json')['aprovado']
    for name,digest in read(case/'scripts_sha256.json').items():
        assert hashlib.sha256((case/'scripts'/name).read_bytes()).hexdigest()==digest,name
    return cfg

def follow_process(process,case):
    created=process.create_time()
    while process.is_running() and process.create_time()==created:
        state=read(case/'pipeline.json') if (case/'pipeline.json').exists() else {}
        save('estado.json',dict(estado='EXECUTANDO',caso=case.name,pipeline_pid=process.pid,pipeline=state,atualizado=now()))
        try:process.wait(timeout=15);break
        except psutil.TimeoutExpired:pass

def execute(case):
    inspect_case(case)
    existing=case/'processo_criacao.json'
    if existing.exists():
        state=read(case/'pipeline.json')
        if state['estado']=='CONCLUIDO_AGUARDA_REVISAO':return
        if state['estado']=='REQUER_VERIFICACAO':raise RuntimeError(state)
        proc=psutil.Process(state['pipeline_pid'])
        cmd=' '.join(proc.cmdline()).lower().replace('/','\\')
        assert 'executar_estudo.ps1' in cmd and str(case).lower() in cmd,(proc.pid,cmd)
        log('ACOMPANHANDO '+case.name+' PID '+str(proc.pid))
        follow_process(proc,case)
    else:
        wait_resources(case)
        runner=REPO/'projetos/P2M19/automacao/executar_estudo.ps1'
        with (case/'pipeline_stdout.log').open('wb') as out,(case/'pipeline_stderr.log').open('wb') as err:
            p=subprocess.Popen(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(runner),'-Pasta',str(case)],stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
            log('INICIANDO '+case.name+' PID '+str(p.pid))
            follow_process(psutil.Process(p.pid),case)
    state=read(case/'pipeline.json')
    assert state['estado']=='CONCLUIDO_AGUARDA_REVISAO',state

def main():
    with LOCK.open('x',encoding='utf-8') as f:json.dump(dict(pid=os.getpid(),inicio=now()),f)
    try:
        plan=dict(tipo='Lote local finito de HFSS, sem agendamento recorrente',
            casos=CASES,limite_passes_por_caso=6,total_maximo_passes_novos=18,
            frequencia_GHz=5.17,nucleos=14,delta_s=.05,sweep=False,
            placas_preservadas=True,alteracoes='Colunas 72 mm; refletor 178, 162 e 146 mm; demais parâmetros iguais.',
            resultado_sem_convergencia='Exploratório; nunca aprovado nem promovido como validado.',
            condicoes_interrupcao=['Erro do solver ou exportação','Reparo Major','Balanço de potência inválido','Passividade ou reciprocidade inválida','Arquivo PARAR_APOS_CASO'],
            inicio=now(),controller_pid=os.getpid())
        save('plano.json',plan)
        results=[]
        for name in CASES:
            if (ROOT/'PARAR_APOS_CASO').exists():raise InterruptedError('Parada após caso solicitada')
            case=WORK/name;execute(case);r=read(case/'resultado.json')
            assert r['passes']<=6 and r['nucleos']==14 and r['frequencia_GHz']==5.17
            assert r['fisica_ok'] and r['balanco_potencia_valido'] and r['major']==0,'Auditoria física reprovada: '+name
            summary=dict(caso=name,passes=r['passes'],delta_s=r['delta_s'],convergiu=r['convergiu'],
                ganho_dBi=r['cortes']['H']['ganho_frontal_dBi'],H_graus=r['cortes_finos']['H']['abertura_graus'],V_graus=r['cortes_finos']['V']['abertura_graus'],
                SLL_H_dB=r['cortes']['H']['SLL']['nivel_dB'],SLL_V_dB=r['cortes']['V']['SLL']['nivel_dB'],validado_numericamente=r['validado_numericamente'])
            results.append(summary);save('resultados_parciais.json',results)
            log('CONCLUIDO '+json.dumps(summary,ensure_ascii=False))
        save('estado.json',dict(estado='LOTE_CONCLUIDO_REVISAR',atualizado=now(),casos=results,
            qualificados=[r['caso'] for r in results if r['validado_numericamente'] and r['ganho_dBi']>=19],
            observacao='Abertura e lóbulos serão comparados sem tolerância de aprovação inventada.'))
        log('FILA_CONCLUIDA')
    except Exception:
        save('estado.json',dict(estado='REQUER_VERIFICACAO',erro=traceback.format_exc(),atualizado=now()))
        log(traceback.format_exc());raise
    finally:LOCK.unlink(missing_ok=True)

if __name__=='__main__':main()
