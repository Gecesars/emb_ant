"""Prepara conjunto 4+2 simetrico e tres dobras; nenhum solve."""
from pathlib import Path
import json,hashlib,shutil
REPO=Path(__file__).resolve().parents[3];ROOT=Path('D:/dev/EMBRAER/P2S13/R01_Seis_Elementos')
base=json.loads((REPO/'projetos/P2S13/refletor_nativo_b20_60/configuracao.json').read_text())
four=REPO/'projetos/P2M21/quatro_elementos_casamento_banda/c12_raiz_intermediaria';two=ROOT/'celula2_simetrica'
cells=[];ports=[];count=1
for name,folder,native,x,nlevels in [('R1',four,'4_elementos.FCStd',-48.,4),('R2',two,'2_elementos_simetrica.FCStd',96.,2)]:
    files=[native,'geometria.json','cad/manifesto.json','cad/folhas_solidas.json']
    cells.append(dict(nome=name,fonte=str(folder),cad_native=native,x=x,y=0.,z=0.,radiadores=nlevels,fontes_sha256={n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in files}))
    count+=len(json.loads((folder/'cad/manifesto.json').read_text()))-1
    for p in json.loads((folder/'cad/portas.json').read_text()):
        ports.append({**p,'name':name+'_'+p['name'],'celula':name,'polarizacao':p['name'],'x':x+p['x']})
base.pop('fonte',None);base.pop('fontes_sha256',None)
base.update(celulas=cells,portas=ports,radiadores=6,niveis_radiadores=6,solidos_fisicos=count,refletor_comprimento_mm=296.,passo_placas_mm=144.,
    escopo='PCB4 C12 preservada e nova PCB2 simetrica derivada das etapas locais C12; seis niveis com passo48, quatro cabos50mm fisicos, quatro fontes iguais0.25W/0graus. Sem N, suportes ou rede externa.',
    prioridade='Abertura horizontal; manter ganho e vertical relatados contra metas originais.',
    ressalva_alimentacao='Entradas iguais nao implicam igual potencia por radiador: placa2 recebe nominalmente o dobro por elemento. Fase eletrica entre modulos deve ser verificada nos campos.',
    refletor_construcao='nativo',exigir_malha_sem_reparos=True)
names=[]
for name,b,a in [('s00_b20_a60',20,60),('s01_b20_a90',20,90),('s02_b10_a90',10,90)]:
    folder=ROOT/name;assert not folder.exists(),folder;folder.mkdir()
    cfg={**base,'revisao':name,'native':'P2S13_6elementos.aedt','cad_native':'P2S13_6elementos.FCStd','design':'Seis_elementos','inicio_dobra_y_mm':b,'angulo_dobra_graus':a}
    (folder/'configuracao.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (folder/'qualificacao.json').write_text('{"estado":"PREPARANDO_CAD","simulado":false}\n')
    shutil.copy2(four/'HFSS_14nucleos.acf',folder/'HFSS_14nucleos.acf');names.append(name)
(ROOT/'requisitos.json').write_text(json.dumps(dict(data='2026-11-10',arranjo='Uma placa4 mais uma placa2, seis niveis verticais; nova alimentacao2 simetrica como C12',prioridade='Horizontal99–121graus',metas=base['metas'],variantes=names,max_passes=6,delta_s=.05,nucleos=14,frequencia_GHz=5.17,sweep=False),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(variantes=names,solidos_fisicos=count,portas=ports)))
