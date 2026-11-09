"""Prepara o ensaio R10 de quatro radiadores, sem iniciar o solver."""
from pathlib import Path
import hashlib,json,shutil

REPO=Path(__file__).resolve().parents[3]
SCRIPTS=Path(__file__).parent
ROOT=Path('D:/dev/EMBRAER/P2M21/R10_Quatro_Verticais')
SRC=REPO/'projetos/P2M21/planejamento/4_elementos/planejamento.json'
assert not ROOT.exists(),'Examinar pasta existente antes de repetir a preparacao.'
ROOT.mkdir(parents=True)
g=json.loads(SRC.read_text(encoding='utf-8'))
base=json.loads((REPO/'projetos/P2M21/dois_verticais_divisor/variantes/v05_B_longo_inferior_15/geometria.json').read_text(encoding='utf-8'))
assert g['radiadores']==4 and g['entradas_externas']==2 and not g['shorts']
g.update(estado='GEOMETRIA_PREPARADA_PARA_HFSS',h=.76,cu=.035,pitch=48,
    inputs=[dict(name=p['name'],x=p['x'],y=p['y'],sig='SIG_'+p['name'],ret='RET_'+p['name']) for p in g['entradas']],
    cabo=base['cabo'],pcb_z=16.61,refletor_z=0)
(ROOT/'geometria.json').write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
cfg=dict(native='P2M21_4_elementos.aedt',design='Quatro_elementos',
    fonte=str(SRC),fonte_sha256=hashlib.sha256(SRC.read_bytes()).hexdigest(),
    radiadores=4,colunas=1,espacamento_vertical_mm=48,placa_largura_altura_mm=[70,178.8],
    refletores_mm=[90,194.8,2],divisores_1x4=2,estagios_1x2_por_polarizacao=3,
    cabos_fisicos_com_perdas=True,comprimento_cabo_mm=50,apoios_plasticos=False,
    frequencia_GHz=5.17,max_passes=6,max_delta_s=.04,min_passes=2,passes_consecutivos=2,
    nucleos=14,gui=False,sweep=False,potencia_por_porta_W=.5,fase_graus=0,
    malha='Classic automatico 5; sem MeshLink, sem operacoes locais e sem LambdaRefine; adaptacao20%.',
    materiais='RO4350B .76mm, cobre35um, ENIG nominal da v05, PTFE e perdas fisicas dos coaxiais.',
    escopo='Modulo de quatro elementos completo com rede impressa e dois cabos retos; sem conector N.')
(ROOT/'configuracao.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
shutil.copy2('D:/dev/EMBRAER/P2M21/R09_Divisor_Simetria/HFSS_14nucleos.acf',ROOT/'HFSS_14nucleos.acf')

def replace(code,old,new):
    assert old in code,old
    return code.replace(old,new)

cad=(SCRIPTS/'dois_verticais_cad.py').read_text(encoding='utf-8')
cad=replace(cad,'Tres placas de dois elementos: dois coaxiais fisicos e refletor local.','Quatro elementos com dois coaxiais fisicos e refletor local; sem apoios plasticos.')
cad=replace(cad,"root=Path('D:/dev/EMBRAER/P2M21/R07_Dois_Verticais_GUI')",'root=Path('+repr(str(ROOT))+')')
cad=replace(cad,"for folder in [root/'d48p0',root/'d52p6',root/'d56p0']:",'for folder in [root]:')
cad=replace(cad,"'Dois_'+folder.name","'Quatro_Elementos'")
cad=replace(cad,"'Dois_Verticais.FCStd'","'4_elementos.FCStd'")
cad=replace(cad,'ref=box(x0-8,-31,-2,x1-x0+16,66,2)','ref=box(x0-8,-45,-2,x1-x0+16,90,2)')
start=cad.index('    # Suportes de poliacetal');end=cad.index('    d.recompute();',start)
cad=cad[:start]+cad[end:]
(ROOT/'criar_cad.py').write_text(cad.rstrip()+'\n',encoding='utf-8')

code=(REPO/'projetos/P2M21/dois_verticais_divisor/reproducao/criar_hfss.py').read_text(encoding='utf-8')
code=replace(code,'Criar tres projetos HFSS separados. Nao executa solver automaticamente.','Criar o projeto HFSS de quatro elementos. Nao executa solver automaticamente.')
code=replace(code,'import os,json,sys,traceback',"import os,json,sys,traceback\nimport ScriptEnv\nScriptEnv.Initialize('Ansoft.ElectronicsDesktop')")
import re
code,n=re.subn(r'^root=.*$', 'root='+repr(str(ROOT)),code,flags=re.M);assert n==1
code,n=re.subn(r'^for folder,filename in .*:$',"for folder,filename in [('', 'P2M21_4_elementos')]:",code,flags=re.M);assert n==1
code=replace(code,"'PCB_separada'","'Quatro_elementos'")
code=replace(code,'Dois elementos verticais e divisores impressos','Quatro elementos verticais e dois divisores 1:4 impressos')
code=replace(code,"p.Save();e.FitAll();log('CRIADO_VALIDADO '+filename)","p.Save();oDesktop.CloseProject(p.GetName());log('CRIADO_VALIDADO_HEADLESS '+filename)")
(ROOT/'criar_hfss.py').write_text(code.rstrip()+'\n',encoding='utf-8')
(ROOT/'qualificacao.json').write_text(json.dumps(dict(estado='AGUARDA_CAD_E_CRIACAO_HFSS',sweep=False,gui=False),indent=2)+'\n',encoding='utf-8')
print(ROOT)
