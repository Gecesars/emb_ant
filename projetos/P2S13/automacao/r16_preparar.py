"""PVC DN100 nominal: nova campanha, sem alterar as fontes R14/R15."""
from pathlib import Path
import json,shutil,hashlib
ROOT=Path('D:/dev/EMBRAER/P2S13/R16_Tubo_PVC');CASE=ROOT/'dn100'
ANT=Path('D:/dev/EMBRAER/P2S13/R14_Compacto_Simetrico_SemRadome/c00/antena')
BASE=Path('D:/dev/EMBRAER/P2S13/R15_Casamento_C09/c02')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
fit=read(ROOT/'encaixe_preliminar.json');assert fit['tubos'][1]['folga_radial_conservadora_mm']>1
tube=dict(DN=100,De_mm=101.6,espessura_mm=1.8,Di_mm=98.0,comprimento_mm=350,
    eixo='X',centro_y_mm=0,centro_z_mm=fit['centro_z_mm'],tampas=False,bolsa=False,
    material='PVC_referencia_preliminar',er=2.68,tand=.008,
    fonte_dimensoes='https://www.tigre.com.br/produto/tubo-serie-normal-6m',codigo_6m='11031030',
    ficha='https://tigresite.s3.amazonaws.com/2023/07/FT_Esgoto-Serie-Normal_2023_final_compressed-1.pdf',
    fonte_referencia_dieletrica='https://iemsl.engr.tamu.edu/services/material-characterization-services/material-characterization-examples/',
    ressalva_material='Hipotese em 5.17GHz; referencia de filme PVC em 10.2-52.2GHz, NAO propriedade medida/certificada do tubo Tigre. Composto/lote podem diferir.',
    folga_conservadora_mm=fit['tubos'][1]['folga_radial_conservadora_mm'])
assert not CASE.exists(),'Preservar campanha existente'
CASE.mkdir()
cfg=read(BASE/'configuracao.json');cfg.update(revisao='R16_PVC_DN100',radome=tube,radome_presente=True,
    escopo='Tres placas de dois elementos dentro de tubo PVC aberto; antena e divisor HFSS separados; cabos somente no circuito.',
    metodo_RF='Novo S6 da antena com PVC, novo S8 do divisor com PVC; seis cabos RLGC iguais no Nexxim.',
    criterio_prioritario='Minimizar o maior VSWR ativo nas duas entradas iguais/em fase; abertura apenas informativa.',
    antena_reutilizada=None,campos_volumetricos_locais=False,
    alteracoes_autorizadas='12nov: incluir tubo PVC de dimensoes comerciais, priorizar menor VSWR; HFSS separado max6/DeltaS0.05/14cores; cabos somente no circuito.')
cfg['fontes_antena_historicas_sha256']=cfg.pop('fontes_antena_sha256',{})
cfg['metas']['abertura_H_obrigatoria']=False
cfg['modelos_RF_ativos']=dict(antena='antena/PCB_Tubo_DN100.aedt',divisor='divisor/Divisor_Tubo_DN100.aedt',circuito='circuito/C09_PVC_Nexxim.aedt')
write(CASE/'configuracao.json',cfg)
for block,src,old,new in [('antena',ANT,'PCB_SemCabos.aedt','PCB_Tubo_DN100.aedt'),('divisor',BASE/'divisor','Divisor_Duplo3.aedt','Divisor_Tubo_DN100.aedt')]:
    dest=CASE/block;dest.mkdir();shutil.copy2(src/old,dest/new);shutil.copy2(src/'HFSS_14nucleos.acf',dest/'HFSS_14nucleos.acf')
    bc=read(src/'configuracao.json');bc.update(native=new,radome=tube,radome_presente=True,revisao='R16_PVC_DN100_'+block,
        nucleo_preservado=old,bloco=block,fonte=str(src/old),fonte_sha256=hashlib.sha256((src/old).read_bytes()).hexdigest(),
        pipe_center_z_local_mm=tube['centro_z_mm'] if block=='antena' else cfg['divisor_translacao_z_mm']-tube['centro_z_mm'])
    write(dest/'configuracao.json',bc)
write(CASE/'estado.json',dict(estado='PREPARADO',tubo=tube,fonte_antena=str(ANT),fonte_divisor=str(BASE/'divisor')))
print('R16 preparada sem resultados copiados',CASE)
