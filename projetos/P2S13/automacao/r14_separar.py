"""Preparar EM separado e circuitos; cabos existem somente no CAD mecanico/Nexxim."""
from pathlib import Path
import json,shutil
ROOT=Path('D:/dev/EMBRAER/P2S13/R14_Compacto_Simetrico_SemRadome/c00');ANT=ROOT/'antena';ANT.mkdir(exist_ok=True)
c=json.loads((ROOT/'configuracao.json').read_text());assert not (ANT/'PCB_SemCabos.aedt').exists()
c['metodo_RF']='HFSS separado: S6 antena sem cabos, S8 divisor; Nexxim com seis linhas coaxiais de mesmo comprimento. Sem radome.'
c['cabos']['comprimento_entre_portas_EM_mm']=c['cabos']['comprimento_mm']-.18
c['cabos']['referencias']='Porta local antena0.18mm abaixo do substrato; terminaçao local incluida no S6. Restante do eixo do cabo no circuito.'
c['integral_HFSS_cancelado_antes_do_solver']=True
(ROOT/'configuracao.json').write_text(json.dumps(c,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
a=dict(c);a.update(native='PCB_SemCabos.aedt',cad_native='PCB_SemCabos.FCStd',design='TresPCB2_SemCabos',portas=[dict(p,z=14.769) for p in c['portas_coaxiais']],
  portas_total=6,potencia_por_porta_W=1/6,radome_presente=False,fonte_divisor=None,
  escopo='Tres PCBs radiantes e refletor. Seis portas diretas em terminais locais0.18mm; sem cabos, sem divisor, sem radome.',
  revisao='R14_Antena_S6',campos_volumetricos_locais=False)
(ANT/'configuracao.json').write_text(json.dumps(a,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
for d in [ANT,ROOT/'divisor']:shutil.copy2(ROOT/'HFSS_14nucleos.acf',d/'HFSS_14nucleos.acf')
(ROOT/'pipeline.json').write_text(json.dumps(dict(estado='INTEGRAL_NAO_SIMULAR_SUBSTITUIDO_POR_EM_SEPARADO',autorizacao='Pedido usuario12nov: nao simular cabosHFSS; executar circuitoNexxim'),indent=2)+'\n')
print('EM_SEPARADO_CONFIGURADO')
