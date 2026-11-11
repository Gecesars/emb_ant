"""Prepara uma variacao de refletor; PCBs ajustadas e excitacoes preservadas."""
from pathlib import Path
import argparse,json,hashlib,shutil,math
REPO=Path(__file__).resolve().parents[3]
ROOT=Path('D:/dev/EMBRAER/P2S13/R04_Dobras_Ajustadas')
SRC=Path('D:/dev/EMBRAER/P2S13/R03_Continuacao_M00')
assert not (ROOT/'interrupcao.json').exists(),'Campanha4+2 interrompida pelo usuario; nao preparar novos casos'
p=argparse.ArgumentParser();p.add_argument('nome');p.add_argument('--inicio',type=float,required=True);p.add_argument('--angulo',type=float,required=True);a=p.parse_args()
assert a.nome.replace('_','').isalnum() and 0<a.inicio<40 and 0<a.angulo<180
cfg=json.loads((SRC/'configuracao.json').read_text());alpha=math.radians(a.angulo)
tail=cfg['refletor_desenvolvido_largura_mm']/2-a.inicio-alpha*(cfg['raio_interno_mm']+cfg['K_dobra']*cfg['espessura_mm'])
assert tail>0
end_y=a.inicio+cfg['raio_interno_mm']*math.sin(alpha)+tail*math.cos(alpha)
assert end_y>0.5,'As abas se encontram/cruzam o eixo central'
folder=ROOT/a.nome;assert not folder.exists(),folder;folder.mkdir(parents=True)
for k in ['passes_iniciais','passes_adicionais_autorizados','fonte_continuacao','referencia_continuacao']:cfg.pop(k,None)
cfg.update(revisao=a.nome,native='P2S13_Dobras.aedt',cad_native='P2S13_Dobras.FCStd',design='Dobras_Ajustadas',
    inicio_dobra_y_mm=a.inicio,angulo_dobra_graus=a.angulo,max_passes=6,min_passes=2,
    estudo='Somente inicio/angulo das duas dobras simetricas; PCBs ajustadas, cabos, portas e altura preservados.',
    prioridade='Ganho frontal >=13dBi, H99-121graus (alvo110), VSWR<=1.25 nas quatro entradas ativas e casadas. Vertical informativa nesta etapa.',
    fonte_referencia=str(SRC),criterio_VSWR='Quatro entradas ativas iguais/em fase e cada entrada com as demais casadas',meta_VSWR_todas=1.25)
for c in cfg['celulas']:
    for n,h in c['fontes_sha256'].items():assert hashlib.sha256((Path(c['fonte'])/n).read_bytes()).hexdigest()==h,(c['nome'],n)
(folder/'configuracao.json').write_text(json.dumps(cfg,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
(folder/'qualificacao.json').write_text('{"estado":"PREPARANDO_CAD","simulado":false}\n')
(folder/'origem.json').write_text(json.dumps(dict(referencia=str(SRC),config_sha256=hashlib.sha256((SRC/'configuracao.json').read_bytes()).hexdigest(),alteracao='Refletor: inicio e angulo; novo ciclo max6passes, DeltaS0.05; demais condicoes iguais.'),indent=2)+'\n')
shutil.copy2(SRC/'HFSS_14nucleos.acf',folder/'HFSS_14nucleos.acf')
print(str(folder))
