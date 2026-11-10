"""Captura local da entrada do mesher de uma sessao propria; nunca arquivar o G3D no Git."""
from pathlib import Path
import argparse,os,time,json,shutil,psutil
p=argparse.ArgumentParser();p.add_argument('pid',type=int);p.add_argument('destino',type=Path);a=p.parse_args()
proc=psutil.Process(a.pid);assert proc.name().lower()=='ansysedt.exe' and 'P2S13' in ' '.join(proc.cmdline())
a.destino.mkdir(parents=True,exist_ok=True)
for _ in range(150):
    if not proc.is_running():break
    for child in proc.children(recursive=True):
        if child.name().lower()!='hfsscomengine.exe':continue
        folder=Path(os.environ['TEMP'])/('hfss_'+os.environ['COMPUTERNAME']+'_'+str(child.pid)+'.pjt')
        f=folder/'defn_Centrobef_rec.g3d'
        if f.exists():
            before=f.stat().st_size;time.sleep(.3)
            if before!=f.stat().st_size:continue
            shutil.copy2(f,a.destino/'triangulacao_local.g3d')
            for n in ['profile_backup','defn_Centro.truesurface','g3dmessage.err']:
                if (folder/n).exists():shutil.copy2(folder/n,a.destino/n)
            (a.destino/'captura.json').write_text(json.dumps(dict(aedt_pid=a.pid,engine_pid=child.pid,origem=str(f),bytes=before),indent=2)+'\n')
            print('CAPTURADO',before);raise SystemExit(0)
    time.sleep(2)
raise SystemExit('Arquivo intermediario nao capturado')
