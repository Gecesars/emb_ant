"""Nova revisao fabricavel C07, sem sobrescrever os modelos de origem."""
from pathlib import Path
import json,hashlib,shutil
BASE=Path('D:/dev/EMBRAER/P2S13/R11_Fabricavel_Radome')
SRC=Path('D:/dev/EMBRAER/P2S13/R09_Correcao_Divisor/c07_centro')
ANT=Path('D:/dev/EMBRAER/P2S13/R06_Continuacao_Tres2')
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
    div=BASE/'d00';div.mkdir(parents=True,exist_ok=True)
    assert not (div/'configuracao.json').exists()
    c=json.loads((SRC/'configuracao.json').read_text())
    c={k:v for k,v in c.items() if not k.startswith('nominal_')}
    c.update(revisao='C08_DFM_d00',native='Divisor_Duplo3.aedt',design='Duplo1x3_Planar',
             fabricacao=dict(furo_acabado_mm=1.10,ilha_diametro_mm=1.80,metalizacao_mm=.018,recuo_terra_mm=.30,
                             cobre_mm=.035,acabamento='ENIG',mascara=False,serigrafia=False),
             fonte_C07=str(SRC),fonte_sha256={n:sha(SRC/n) for n in ['Divisor_Duplo3.aedt','Divisor_Duplo3.FCStd','configuracao.json']})
    dump(div/'configuracao.json',c)
    shutil.copy2(SRC/'HFSS_14nucleos.acf',div/'HFSS_14nucleos.acf')
    cfg=json.loads((ANT/'configuracao.json').read_text())
    cfg['portas_coaxiais']=cfg.pop('portas')
    dz=-35.231
    cfg['portas']=[dict(p,x=p['x'],y=-p['y'],z=-p['z']+dz) for p in c['portas'] if p['name'].startswith('IN_')]
    cfg.update(native='P2S13_Radome.aedt',cad_native='P2S13_Radome.FCStd',design='Conjunto_Radome',
               revisao='R11_integral_d00',max_passes=6,min_passes=2,basis_order=2,percent_refinement=50,
               potencia_por_porta_W=.5,portas_total=2,fonte_antena=str(ANT),fonte_divisor=str(div),
               estudo='C07 corrigida para fabricacao e conjunto integral com radome FR4 de 2 mm.',
               criterio_VSWR='Duas entradas externas ativas iguais/em fase; outra entrada casada reportada adicionalmente.',
               divisor_rotacao_x_graus=180,divisor_translacao_z_mm=dz,exigir_malha_sem_reparos=False,
               radome=dict(material='Isola_370HR_nominal',er=3.92,tand=.025,espessura_mm=2.,
                           inner_min_mm=[-155,-40,-45],inner_max_mm=[155,40,35],
                           fonte='https://isola-group.com/wp-content/uploads/data-sheets/370hr.pdf',
                           frequencia_ficha_GHz=5,modelo='FR4 sem cobre, isotropico; valores tipicos, nao certificado de lote'),
               metas=dict(ganho_frontal_min_dBi=12,VSWR_max=1.25,pico_V_alvo_graus=0,pico_V_tolerancia_graus=.5,
                          assimetria_principal_max_dB=.2),
               escopo='3 PCBs2 + seis cabos50mm com perdas + divisor duplo1:3 fabricavel + radome FR4 2mm. Duas portas ideais50ohm internas; conectores externos e vedacoes nao caracterizados.')
    for key in ['passes_iniciais','passes_adicionais_autorizados','fonte_continuacao','referencia_continuacao','prioridade','ressalva_alimentacao']:
        cfg.pop(key,None)
    full=BASE/'a00';full.mkdir(exist_ok=True)
    dump(full/'configuracao.json',cfg);shutil.copy2(SRC/'HFSS_14nucleos.acf',full/'HFSS_14nucleos.acf')
    dump(BASE/'estado.json',dict(estado='PREPARACAO',solver_novo=False))
    print(BASE)
