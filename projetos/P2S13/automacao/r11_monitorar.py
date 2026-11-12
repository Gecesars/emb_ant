from pathlib import Path
import sys,os,json
repo=Path(__file__).resolve().parents[3];sys.path.insert(0,str(repo/'projetos/P2M21/automacao'))
from oito_celulas_monitorar import progress
root=Path(os.environ.get('P2S13_ROOT','D:/dev/EMBRAER/P2S13/R11_Fabricavel_Radome/a00'))
p=progress(root)
for row in p.get('historico',[]):
    fields=row.get('campos_dBi',{})
    row['ganho_frontal_monitor_dBi']=fields.get('P2S13_Campo_00')
    row.pop('campos_dBi',None)
p['historico']=p.get('historico',[])[-2:]
print(json.dumps(p,indent=2))
