"""Prepara R14: oito celulas C12, 4 placas verticais x 2 colunas; sem solve."""
from pathlib import Path
import json,hashlib,shutil
ROOT=Path('D:/dev/EMBRAER/P2M21/R14_Oito_Celulas')
REPO=Path(__file__).resolve().parents[3]
SOURCE=REPO/'projetos/P2M21/quatro_elementos_casamento_banda/c12_raiz_intermediaria'
assert not ROOT.exists(),'Inspecionar estudo existente; nao sobrescrever.'
ROOT.mkdir(parents=True)
g=json.loads((SOURCE/'geometria.json').read_text())
assert g['placa_largura_altura_mm']==[70,184] and g['pitch']==48
cells=[dict(nome='C%dR%d'%(j+1,i+1),coluna=j+1,nivel_placa=i+1,x=x,y=y,z=0)
       for j,y in enumerate([-36.,36.]) for i,x in enumerate([-288.,-96.,96.,288.])]
ports=[dict(name=c['nome']+'_'+p['name'],celula=c['nome'],polarizacao=p['name'],
            x=c['x']+p['x'],y=c['y']+p['y'],z=14.949-50,ri=.45975,ro=1.515)
       for c in cells for p in g['inputs']]
cfg=dict(revisao='R14_Oito_Celulas',native='P2M21_8celulas.aedt',design='Oito_celulas',
    fonte=str(SOURCE),fontes_sha256={n:hashlib.sha256((SOURCE/n).read_bytes()).hexdigest() for n in ['geometria.json','4_elementos.FCStd','P2M21_4_elementos.aedt']},
    celulas=cells,portas=ports,niveis_placas=4,colunas=2,radiadores=32,niveis_radiadores=16,
    passo_vertical_radiadores_mm=48,passo_vertical_placas_mm=192,passo_horizontal_mm=72,
    folga_placas_vertical_mm=8,folga_placas_horizontal_mm=2,
    placa_largura_altura_mm=[70,184],envolvente_placas_mm=[142,760],refletor_mm=[162,776,2],
    distancia_face_inferior_laminado_ao_refletor_mm=14.949,
    frequencia_GHz=5.17,max_passes=6,min_passes=2,max_delta_s=.05,passes_consecutivos=2,
    nucleos=14,gui=False,sweep=False,basis_order=1,percent_refinement=20,
    monitoramento_estabilidade_campo_dB=.1,monitoramento_campo_nao_altera_parada=True,
    potencia_total_W=1,potencia_por_porta_W=.0625,fase_graus=0,
    malha='Classic automatico5; sem operacoes locais, MeshLink ou LambdaRefine inicial; BasisOrder=1 (First Order); adaptacao20%.',
    cabos_fisicos_com_perdas=True,comprimento_cabo_mm=50,apoios_plasticos=False,
    rede_distribuicao_externa=False,conectores_N=False,
    observacao='Todas as 16 portas coerentes; nao constitui ganho MIMO por entrada. Rede de duas entradas para 16 conexoes sera planejada apos diagramas.',
    referencia_historica='projetos/P2M21/centro_sem_refinamento/continuacao_6_passes',
    limites_referencia='Historico64portas nao convergido; passo52.6x40mm, refletor e alimentacao diferentes; comparacao nao isola somente a modularizacao.')
(ROOT/'configuracao.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
shutil.copy2('D:/dev/EMBRAER/P2M21/R13_Casamento_Banda/c12_raiz_intermediaria/HFSS_14nucleos.acf',ROOT/'HFSS_14nucleos.acf')
(ROOT/'qualificacao.json').write_text(json.dumps(dict(estado='PREPARANDO_CAD',simulado=False),indent=2)+'\n')
print(ROOT)
