"""Ensaios de seguranca do guarda com processos Python inertes, nunca HFSS."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import time
import psutil
import guard_memoria as g

policy=json.loads(g.POLICY.read_text())
mib=1024**2
healthy=dict(ram_livre_bytes=4*1024*mib,commit_livre_bytes=8*1024*mib)
assert g.decision(policy,healthy,0)==(None,0)
assert g.decision(policy,dict(healthy,ram_livre_bytes=800*mib),0)==(None,1)
assert g.decision(policy,dict(healthy,ram_livre_bytes=800*mib),1)[0]=='RAM_LIVRE_BAIXA_SUSTENTADA_PARADA_PREVENTIVA'
assert g.decision(policy,healthy,1)==(None,0)
assert g.decision(policy,dict(healthy,ram_livre_bytes=400*mib),0)[0]=='RAM_LIVRE_CRITICA_PARADA_PREVENTIVA'
assert g.decision(policy,dict(healthy,commit_livre_bytes=400*mib),0)[0]=='COMPROMETIMENTO_CRITICO_PARADA_PREVENTIVA'
assert g.decision(policy,healthy,0,True)[0]=='ERRO_EXPLICITO_DE_MEMORIA'
try:g.require_enabled(policy)
except RuntimeError as ex:assert 'SUSPENSAS' in str(ex)
else:raise AssertionError('Politica suspensa permitiu execucao')

with tempfile.TemporaryDirectory(prefix='p2m19_guard_test_') as temp:
    p=Path(temp)/'solver.log';p.write_text('normal\n',encoding='utf-16')
    positions={str(p):p.stat().st_size}
    with p.open('a',encoding='utf-16') as f:f.write('SOLVER_OUT_OF_MEMORY\n')
    assert g.new_log_lines([p],positions)
    p.write_text('novo arquivo sem falha\n',encoding='utf-8')
    assert not g.new_log_lines([p],positions)

flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
outsider=subprocess.Popen([sys.executable,'-c','import time; time.sleep(40)'],creationflags=flags)
root=subprocess.Popen([sys.executable,'-c',
    'import subprocess,sys,time; subprocess.Popen([sys.executable,"-c","import time;time.sleep(40)"]);time.sleep(40)'],creationflags=flags)
items=[]
try:
    ref=g.identity(psutil.Process(root.pid))
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        items=g.owned_processes(ref)
        if len(items)>=2:break
        time.sleep(.1)
    assert len(items)==2,items
    fake=dict(ref,criado=ref['criado']-100)
    assert g.same_process(fake) is None
    stop=g.stop_owned(items)
    assert not stop['sobreviventes'],stop
    assert outsider.poll() is None,'Processo alheio foi encerrado'
    assert all(g.same_process(i) is None for i in items)
finally:
    if items:g.stop_owned(items)
    if outsider.poll() is None:outsider.terminate()
    outsider.wait(timeout=5)
    if root.poll() is None:root.terminate()
    root.wait(timeout=5)

record=dict(hora=g.now(),aprovado=True,teste_sem_hfss=True,
    verificacoes=['limiares fisicos e de comprometimento','histerese preventiva e recuperacao',
    'erro explicito OOM','log UTF16 e truncamento','suspensao impede inicio',
    'PID com criacao diferente nao identificado','arvore de 2 processos inertes encerrada',
    'processo alheio preservado'],
    limitacao='Nao se provocou falta real de memoria nem se executou HFSS para testar o guarda.')
g.write_json(g.PROJECT/'gestao_R09/teste_guard_memoria.json',record)
print(json.dumps(record,ensure_ascii=False,indent=2))
