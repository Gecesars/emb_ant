"""Consulta somente leitura da continuacao de 8 para 10 passes da P2M19."""
from pathlib import Path
import sys,json,subprocess,datetime
ROOT=Path('D:/dev/EMBRAER/P2M19/R06_72mm_ref146_10passes')
sys.path.insert(0,'D:/dev/EMBRAER/emb_ant/projetos/P2M21/automacao')
from oito_celulas_monitorar import progress
def monitor():
    out=dict(hora=datetime.datetime.now().isoformat(),pasta=str(ROOT))
    for name in ['pipeline.json','qualificacao.json','falha.json']:
        if (ROOT/name).exists():out[name]=json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
    p=progress(ROOT);out['progresso']={**p,'historico':p.get('historico',[])[-2:]}
    ps="Get-CimInstance Win32_Process | Where-Object {$_.Name -match 'ansysedt|hf3d|HFSSCOMENGINE|G3dMesher'} | Select-Object ProcessId,ParentProcessId,Name,CommandLine | ConvertTo-Json -Compress"
    proc=subprocess.run(['powershell','-NoProfile','-Command',ps],capture_output=True,text=True)
    assert proc.returncode==0,proc.stderr
    out['processos']=json.loads(proc.stdout) if proc.stdout.strip() else []
    return out
if __name__=='__main__':print(json.dumps(monitor(),ensure_ascii=False,indent=2))
