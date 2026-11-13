"""Registra revisão e recuperação de pós-processamento, sem conectar ao HFSS."""
from pathlib import Path
from datetime import datetime
import hashlib, json, shutil

ROOT=Path('D:/dev/EMBRAER/P2M19/R01_16x2_88mm')
def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

result=json.loads((ROOT/'resultado.json').read_text())
assert result['passes']==6 and result['nucleos']==14
assert result['frequencia_GHz']==5.17 and result['fisica_ok']
assert not result['convergiu'] and not result['validado_numericamente']
previous=json.loads((ROOT/'pipeline.json').read_text(encoding='utf-8-sig'))
if previous['estado']=='REQUER_VERIFICACAO':
    shutil.copy2(ROOT/'pipeline.json',ROOT/'evidencias/pipeline_analise_original.json')
write(ROOT/'evidencias/recuperacao_analise.json',dict(
    motivo='Diferença de 0,0000561464 dB entre esferas HV e Centro_fino excedeu o assert inicial de 1e-7 dB.',
    alteracao='Conferência entre relatórios passou a 0,001 dB, com diferenças registradas em resultado.json.',
    criterio_RF_delta_s=.05,criterio_RF_alterado=False,novos_passes=0,
    contextos=result['consistencia_contextos'],analise_reexecutada=True))
images=['polar_HV.png','comparacao_diagramas.png','acoplamento_vswr.png','montagem_frontal.png','montagem_duas_faces.png']
write(ROOT/'revisao_visual.json',dict(
    revisado_em=datetime.now().isoformat(),status='PRELIMINAR_NAO_CONVERGIDO',
    observacao='Cinco imagens inspecionadas; figuras RF legíveis e identificadas como preliminares. Lóbulos laterais fortes preservados nos gráficos.',
    imagens=[dict(arquivo=n,sha256=hashlib.sha256((ROOT/n).read_bytes()).hexdigest()) for n in images]))
write(ROOT/'pipeline.json',dict(estado='CONCLUIDO_REVISADO_PRELIMINAR',
    atualizado=datetime.now().isoformat(),passes_executados=6,
    convergiu=False,ganho_19_numerico=result['metas']['ganho_total_19dBi'],
    sem_nova_simulacao=True,recuperacao='evidencias/recuperacao_analise.json'))
print('Revisão registrada; resultado preliminar, sem novo solve.')
