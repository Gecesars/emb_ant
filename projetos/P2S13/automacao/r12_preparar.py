"""Nova representacao simplificada R12; preserva R11 e nao executa solver."""
from pathlib import Path
import json,hashlib,shutil
SRC=Path('D:/dev/EMBRAER/P2S13/R11_Fabricavel_Radome/a00')
ROOT=Path('D:/dev/EMBRAER/P2S13/R12_Curvilinear_Simplificado')
ROOT.mkdir(exist_ok=True)
assert not (ROOT/'configuracao.json').exists(),'R12 ja preparado'
cfg=json.loads((SRC/'configuracao.json').read_text(encoding='utf-8'))
cfg.update(revisao='R12_Curvilinear_Simplificado',native='P2S13_Curvilinear.aedt',cad_native='P2S13_Curvilinear.FCStd',
    design='Conjunto_Curvilinear',fonte_integral=str(SRC),basis_order=1,percent_refinement=30,
    solver_type='Direct Solver',curvilinear=True,max_passes=6,min_passes=2,passes_consecutivos=2,max_delta_s=.05,
    estudo='Simplificar emendas de mesmo material dos seis cabos, preservar geometria externa e ativar curvilineos.',
    criterio_VSWR='Duas entradas externas ativas iguais/em fase; outra entrada casada reportada adicionalmente.',
    escopo='Mesmo conjunto fisico R11: 3PCBs2, seis cabos50mm, C08 e radome FR4 2mm. Emendas contiguas homogeneas unidas sem mudanca de material/envelope.',
    malha='Classic automatico slider5, curvilinear global ativo, sem operacoes locais e sem refinamento lambda inicial.',
    alteracoes_autorizadas='Pedido12nov: melhorar/simplificar simulacao e marcar use curvilinear elements.',
    referencia_sha256={n:hashlib.sha256((SRC/n).read_bytes()).hexdigest() for n in ['configuracao.json','P2S13_Radome.FCStd','P2S13_Radome.aedt','resultado.json']})
for k in ['prioridade_superficies','refinamentos_locais','passes_adicionais_autorizados']:cfg.pop(k,None)
(ROOT/'configuracao.json').write_text(json.dumps(cfg,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
shutil.copy2(SRC/'HFSS_14nucleos.acf',ROOT/'HFSS_14nucleos.acf')
(ROOT/'estado.json').write_text(json.dumps(dict(estado='PREPARACAO_CAD',novo_solve=False),indent=2)+'\n')
print(ROOT)
