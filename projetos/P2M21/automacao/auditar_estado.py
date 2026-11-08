"""Auditoria de leitura: convergencia, corpos reparados e cobertura real da banda."""
import json,re,hashlib
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
repo=Path(__file__).resolve().parents[3]
root=Path('D:/dev/EMBRAER/P2M21/R00_Concepcao');folder=root/'antena'
native=folder/'P2M21_Antena.aedt';text=native.read_text(errors='replace')
ids={}
for block in text.split("$begin 'GeometryPart'")[1:]:
    block=block.split("$end 'GeometryPart'",1)[0]
    name=re.search(r"\bName='([^']+)'",block)
    pid=re.search(r'ParentPartID=(\d+)',block)
    if name and pid:ids[int(pid.group(1))]=name.group(1)
mesh=json.loads((folder/'malha.json').read_text())
volumes=json.loads((folder/'cad/verificacao.json').read_text())['volumes_mm3']
mapped={level:[dict(id=i,nome=ids.get(i),volume_mm3=volumes.get(ids.get(i)))
    for i in mesh['corpos_'+level+'_ids']] for level in ('major','minor')}
assert all(x['nome'] for group in mapped.values() for x in group)
conv=(folder/'convergencia.txt').read_text()
passes=int(re.search(r'Completed\s*:\s*(\d+)',conv).group(1))
delta=float(re.search(r'Current\s*:\s*([\d.eE+-]+)',conv).group(1))
consec=int(re.search(r'Current Consecutive Passes\s*:\s*(\d+)',conv).group(1))
divs={}
for n in (4,8):
    data=json.loads((root/f'divisor_1x{n}/analise.json').read_text())
    assert [round(p['frequencia_GHz']*1000) for p in data['pontos']]==list(range(5090,5251,10))
    divs[n]=dict(pontos=17,passivo=data['passivo'],reciproco=data['reciproco'])
    for pol in 'AB':
        points=data['pontos'];vs=[p[pol]['VSWR'] for p in points];il=[p[pol]['perda_excedente_dB'] for p in points]
        divs[n][pol]=dict(VSWR_min=min(vs),VSWR_max=max(vs),perda_excedente_min_dB=min(il),perda_excedente_max_dB=max(il))
result=dict(estado='NAO_QUALIFICADA_NUMERICAMENTE',termino_execucao_local='2026-11-08T16:43:00-03:00',
 verificacao_local=datetime.now(ZoneInfo('America/Sao_Paulo')).isoformat(),passes=passes,max_passes_usuario=6,
 delta_s_final=delta,delta_s_alvo=.02,passes_consecutivos_aprovados=consec,
 convergiu='Converged : Yes' in conv,reparos=mapped,
 antena_matriz_exportada=(folder/'centro.s64p').exists(),
 campos_exportados=len(list(folder.glob('padroes/*.csv'))),
 banda17_antena_executada=False,circuito_painel_calculado=False,
 ganho_21dBi_por_entrada_confirmado=False,vswr_1_5_por_entrada_confirmado=False,
 nota='Falta qualificacao numerica. Nao e demonstracao de que a antena fisica tenha ganho abaixo21dBi ou VSWR acima1.5. Divisores isolados nao substituem circuito carregado.',
 divisores=divs,sha256_native=hashlib.sha256(native.read_bytes()).hexdigest(),
 sha256_convergencia=hashlib.sha256((folder/'convergencia.txt').read_bytes()).hexdigest())
(root/'diagnostico_20261108.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(passes=passes,delta=delta,reparos=mapped,divisores=divs),ensure_ascii=False,indent=2))
