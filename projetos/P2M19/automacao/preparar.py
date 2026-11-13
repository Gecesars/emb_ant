"""P2M19 R01: preparar cópias separadas, sem executar solver."""
from pathlib import Path
import json, hashlib, shutil
REPO=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
OLD=REPO/'projetos/P2M21/automacao'
ROOT=Path('D:/dev/EMBRAER/P2M19/R01_16x2_88mm')
SOURCE=REPO/'projetos/P2M21/quatro_elementos_casamento_banda/c12_raiz_intermediaria'
assert not ROOT.exists(), 'Pasta existente: inspecionar antes de repetir'
ROOT.mkdir(parents=True)
cfg=json.loads((REPO/'projetos/P2M21/comparacao_colunas_niveis/R16_Oito_Celulas_78mm/configuracao.json').read_text())
g=json.loads((SOURCE/'geometria.json').read_text())
cells=[dict(nome=f'C{j+1}R{i+1}',coluna=j+1,nivel_placa=i+1,x=(i-1.5)*192,y=(j-.5)*88,z=0) for j in range(2) for i in range(4)]
ports=[dict(name=c['nome']+'_'+p['name'],celula=c['nome'],polarizacao=p['name'],x=c['x']+p['x'],y=c['y']+p['y'],z=14.769,ri=.525,ro=1.515) for c in cells for p in g['inputs']]
cfg.update(revisao='P2M19_R01_16x2_88mm',native='P2M19_16x2_88mm.aedt',cad_native='P2M19_16x2_88mm.FCStd',design='P2M19_16x2',
  fonte=str(SOURCE),celulas=cells,portas=ports,passo_horizontal_mm=88,folga_placas_horizontal_mm=18,
  envolvente_placas_mm=[158,760],refletor_mm=[178,776,2],cabos_fisicos_com_perdas=False,comprimento_cabo_mm=0,
  terminal_local_mm=.18,curvilinear=True,solver_type='Direct Solver',
  malha='Classic automático5, curvilinear; sem operações locais, MeshLink ou LambdaRefine inicial. First Order, adaptação20%.',
  controle_comparacao='Projeto novo. Passo horizontal88mm; refletor178mm mantém margem10mm para placas. Cabos50mm das referências removidos; terminais locais0.18mm.',
  observacao='Somente5.17GHz, 16 portas diretas iguais/em fase, 1Wtotal; sem rede externa, cabos, N, radome ou suportes plásticos. Ganho total, não MIMO por entrada.',
  meta_ganho_frontal_dBi=19,meta_H_graus=20,tolerancia_H_graus=None,
  fontes_sha256={n:hashlib.sha256((SOURCE/n).read_bytes()).hexdigest() for n in ['geometria.json','4_elementos.FCStd','P2M21_4_elementos.aedt']})
for n,d in [('configuracao.json',cfg),('qualificacao.json',dict(estado='PREPARANDO_CAD',simulado=False))]:
 (ROOT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
acf=(SOURCE/'HFSS_14nucleos.acf').read_text().replace('P2M21_14nucleos','P2M19_14nucleos')
(ROOT/'HFSS_14nucleos.acf').write_text(acf)

# Os scripts criar_cad.py, criar_hfss.py e resolver.py são fontes versionadas próprias.
print(ROOT)
