"""Tres PCBs2 identicas: seis niveis e seis fontes iguais/em fase."""
from pathlib import Path
import argparse,json,hashlib,shutil,copy,math
REPO=Path(__file__).resolve().parents[3];ROOT=Path('D:/dev/EMBRAER/P2S13/R05_Tres_Placas2');SRC=Path('D:/dev/EMBRAER/P2S13/R03_Continuacao_M00')
p=argparse.ArgumentParser();p.add_argument('nome');p.add_argument('--inicio',type=float,required=True);p.add_argument('--angulo',type=float,required=True);a=p.parse_args()
assert a.nome.replace('_','').isalnum() and 0<a.inicio<40 and 0<a.angulo<180
folder=ROOT/a.nome;assert not folder.exists();folder.mkdir(parents=True)
cfg=json.loads((SRC/'configuracao.json').read_text());cell=next(c for c in cfg['celulas'] if c['radiadores']==2);src=Path(cell['fonte'])
for n,h in cell['fontes_sha256'].items():assert hashlib.sha256((src/n).read_bytes()).hexdigest()==h,n
ports=json.loads((src/'cad/portas.json').read_text());man=json.loads((src/'cad/manifesto.json').read_text());cells=[];newports=[]
for i,x in enumerate([-96.,0.,96.],1):
    c=copy.deepcopy(cell);c.update(nome='R%d'%i,x=x,y=0.,z=0.);cells.append(c)
    for pt in ports:newports.append({**pt,'name':c['nome']+'_'+pt['name'],'celula':c['nome'],'polarizacao':pt['name'],'x':x+pt['x']})
for k in ['passes_iniciais','passes_adicionais_autorizados','fonte_continuacao','referencia_continuacao','meta_VSWR_placa2']:cfg.pop(k,None)
cfg.update(celulas=cells,portas=newports,niveis_placas=3,solidos_fisicos=1+3*(len(man)-1),potencia_por_porta_W=1/6,passo_placas_mm=96.,
    revisao=a.nome,native='P2S13_TresPCB2.aedt',cad_native='P2S13_TresPCB2.FCStd',design='Tres_Placas2',inicio_dobra_y_mm=a.inicio,angulo_dobra_graus=a.angulo,max_passes=6,min_passes=2,
    escopo='Tres copias identicas da PCB2 ajustada, seis niveis passo48mm; seis cabos50mm fisicos e seis entradas iguais/em fase; sem N, plasticos ou rede externa.',
    estudo='Nova topologia solicitada em11nov: abandona4+2; otimiza inicio/angulo das dobras para H100graus.',
    prioridade='H nominal100graus. Manter ganho13dBi e VSWR<=1.25 como metas; relatar vertical e convergencia.',
    ressalva_alimentacao='Cada placa identica recebe1/3W incidente; cada entrada1/6W a0graus. Igualdade nominal nao elimina acoplamento de borda.',
    criterio_VSWR='Seis entradas ativas iguais/em fase e cada entrada com as demais casadas',meta_VSWR_todas=1.25,fonte_referencia=str(SRC))
cfg['metas'].update(H_alvo_graus=100,H_min_graus=90,H_max_graus=110,H_tolerancia_origem='Tolerancia10% do estudo original; reportar tambem desvio frente ao alvo nominal100.')
alpha=math.radians(a.angulo);tail=45-a.inicio-alpha*2.8;assert tail>0 and a.inicio+2*math.sin(alpha)+tail*math.cos(alpha)>.5
(folder/'configuracao.json').write_text(json.dumps(cfg,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
(folder/'origem.json').write_text(json.dumps(dict(PCB2=str(src),fontes_sha256=cell['fontes_sha256'],centros_placas_X_mm=[-96,0,96],centros_elementos_X_mm=[-120,-72,-24,24,72,120],vao_placas_mm=8,PCBs_identicas=True,substitui='R04_4mais2 interrompido pelo usuario'),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
(folder/'qualificacao.json').write_text('{"estado":"PREPARANDO_CAD","simulado":false}\n');shutil.copy2(SRC/'HFSS_14nucleos.acf',folder/'HFSS_14nucleos.acf')
print(json.dumps(dict(pasta=str(folder),solidos=cfg['solidos_fisicos'],portas=newports)))
