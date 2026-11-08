"""Consolidar evidencias finais sem executar nova simulacao eletromagnetica."""
import csv, hashlib, json, sys
from datetime import datetime
from pathlib import Path
import numpy as np
from circuito import Circuit, read_pattern

root=Path(sys.argv[1])
def load(name):return json.loads((root/name).read_text(encoding='utf8'))
conv=load('antena/auditoria_convergencia.json')
comparison=load('circuito/comparacao_malhas.json')
nexxim=load('circuito/verificacao_nexxim.json')
assert conv['convergencia_aprovada'] and conv['minimo_passes_atendido']
assert comparison['estabilidade_local_aprovada'] and comparison['reparo_major_final']==0
assert comparison['pasta_referencia']=='antena_estrita21'
assert nexxim['matriz_s_independente_conferida']
c=Circuit(root);result,theta,cuts,feeding=c.calculate()
assert result['criterios_numericos_atendidos']
saved=load('circuito/resultado.json')['corrigida']
for key in ['ganho_frontal_realizado_dBi','abertura_H_graus','abertura_V_graus']:
    assert abs(result[key]-saved[key])<1e-10
uniform={}
for axis in 'HV':
    fields=np.stack([read_pattern(c.antenna_folder/'padroes'/(p.split('/')[1]+'_'+axis+'.csv'))[1]
                     for p in c.parts['ANT']['names']],axis=-1)
    recomposed=10*np.log10(np.maximum(np.sum(abs(fields@(np.ones(20)/np.sqrt(20)))**2,axis=-1),1e-30))
    with (c.antenna_folder/('Centro_'+axis+'.csv')).open(encoding='utf-8-sig',newline='') as f:
        direct=np.array([float(row['dB(RealizedGainTotal) []']) for row in csv.DictReader(f)])
    uniform[axis]=float(np.max(abs(recomposed-direct)))
matrices={}
for tag,part in c.parts.items():
    matrix=part['s']
    matrices[tag]=dict(valor_singular_max=float(np.max(np.linalg.svd(matrix,compute_uv=False))),
        reciprocidade_erro_max=float(np.max(abs(matrix-matrix.T))))
balance=result['potencia_incidente_W']-result['refletida_W']-result['aceita_antena_W']-sum(result['perdas_blocos_W'].values())
summary=dict(estado='qualificado_numericamente_em_5.17GHz',instante_consolidacao=datetime.now().astimezone().isoformat(),
    metodo='PCBs completas separadas; circuito com matrizes S e campos complexos; cabos ideais sem atenuacao; N ideal.',
    resultado=result,convergencia=dict(passe=conv['historico'][-1]['passe'],tetraedros=conv['historico'][-1]['tetraedros'],
        delta_s_ultimos2=[x['delta_s'] for x in conv['historico'][-2:]],
        campo_delta_ultimos2_dB=[x['delta_campo_max_dB'] for x in conv['historico'][-2:]]),
    estabilidade=comparison['diferencas'],reparos_major=0,matrizes_centro=matrices,
    recomposicao_uniforme_erro_max_dB=uniform,balanco_potencia_residuo_W=balance,nexxim=nexxim,
    fontes=c.sources,banda_completa_qualificada=False,medicao_fisica=False)
(root/'circuito/qualificacao_final.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
for name in ['configuracao_circuito.json','mecanica/rastreabilidade.json']:
    data=load(name);data['estado']='Geometria verificada; RF qualificado numericamente em 5.17GHz, sem perdas nos cabos'
    data['qualificacao_rf']='circuito/qualificacao_final.json'
    (root/name).write_text(json.dumps(data,indent=2),encoding='utf8')
print(json.dumps({k:summary[k] for k in ['estado','convergencia','recomposicao_uniforme_erro_max_dB','balanco_potencia_residuo_W','matrizes_centro']},indent=2))
