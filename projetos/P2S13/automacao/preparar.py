"""Prepara variantes centrais; somente configuracao, sem abrir HFSS."""
from pathlib import Path
import json,hashlib,shutil
REPO=Path(__file__).resolve().parents[3]
ROOT=Path('D:/dev/EMBRAER/P2S13/R00_Refletor_Dobrado')
SRC=REPO/'projetos/P2M21/quatro_elementos_casamento_banda/c12_raiz_intermediaria'
g=json.loads((SRC/'geometria.json').read_text())
cells=[dict(nome='R1',x=-96,y=0,z=0),dict(nome='R2',x=96,y=0,z=0)]
ports=[dict(name=c['nome']+'_'+p['name'],celula=c['nome'],polarizacao=p['name'],x=c['x']+p['x'],y=p['y'],z=14.949-50,ri=.45975,ro=1.515) for c in cells for p in g['inputs']]
base=dict(fonte=str(SRC),fontes_sha256={n:hashlib.sha256((SRC/n).read_bytes()).hexdigest() for n in ['4_elementos.FCStd','geometria.json','cad/manifesto.json','cad/folhas_solidas.json']},
    celulas=cells,portas=ports,radiadores=8,niveis_radiadores=8,niveis_placas=2,colunas=1,frequencia_GHz=5.17,
    potencia_por_porta_W=.25,fase_graus=0,potencia_total_W=1,nucleos=14,gui=False,sweep=False,
    max_passes=6,min_passes=2,passes_consecutivos=2,max_delta_s=.05,percent_refinement=50,basis_order=1,
    malha='Classic automatico 5, sem refinamentos locais/iniciais, sem MeshLink, DoLambdaRefine=False; adaptacao durante solve 50%',
    metas=dict(ganho_frontal_min_dBi=13,H_min_graus=99,H_max_graus=121,V_min_graus=16.2,V_max_graus=19.8),
    monitoramento_estabilidade_campo_dB=.1,refletor_comprimento_mm=392,refletor_desenvolvido_largura_mm=90,espessura_mm=2,raio_interno_mm=2,K_dobra=.4,
    passo_vertical_mm=48,passo_placas_mm=192,nucleo_z_mm=14.949,
    escopo='Duas PCBs C12 em coluna, geometria e cabos fisicos de 50mm preservados; sem suportes plasticos, conectores N ou rede externa. Ambas polarizacoes e ambas placas em fase.')
plan=[]
for name,b,angle in [('v00_plano',45,0),('v01_b20_a60',20,60),('v02_b30_a60',30,60)]:
    root=ROOT/name
    if root.exists():
        old=json.loads((root/'configuracao.json').read_text())
        assert old['inicio_dobra_y_mm']==b and old['angulo_dobra_graus']==angle
        continue
    root.mkdir(parents=True)
    cfg={**base,'revisao':name,'native':'P2S13.aedt','cad_native':'P2S13.FCStd','design':'Duas_placas','inicio_dobra_y_mm':b,'angulo_dobra_graus':angle}
    (root/'configuracao.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (root/'qualificacao.json').write_text(json.dumps(dict(estado='PREPARANDO_CAD',simulado=False))+'\n')
    shutil.copy2(SRC/'HFSS_14nucleos.acf',root/'HFSS_14nucleos.acf')
    plan.append(name)
(ROOT/'requisitos.json').write_text(json.dumps(dict(projeto='P2S13',estado='EM_ESTUDO',data='2026-11-10',arranjo_confirmado='Duas placas uma acima da outra, oito niveis',referencia_congelada='P2M21 R18',metas=base['metas'],frequencia_GHz=5.17,candidatos_iniciais=plan,convergencia_alvo=.05,max_passes=6,nucleos=14,sweep=False,angulo_convencao='0=plano; +90=bordas para tras, paralelas a normal Z; dobras simetricas em +/-Y. Inicio e a tangencia da face plana superior.',ressalva_vertical='A estimativa isolada indica V~7,63 graus. Dobras laterais uniformes nao demonstram por si a ampliacao vertical requerida.'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('PREPARADOS',plan)
