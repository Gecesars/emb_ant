"""Variantes autorizadas: 78 mm entre colunas, depois cinco PCBs por coluna."""
from pathlib import Path
import json,shutil
BASE=Path('D:/dev/EMBRAER/P2M21/R14_Oito_Celulas')
old=json.loads((BASE/'configuracao.json').read_text())
g=json.loads((Path(old['fonte'])/'geometria.json').read_text())
plan=[]
for tag,levels,pitch in [('R16_Oito_Celulas_78mm',4,78),('R17_Dez_Celulas_78mm',5,78)]:
    root=BASE.parent/tag;assert not root.exists(),root
    root.mkdir();cfg=dict(old)
    cells=[dict(nome=f'C{j+1}R{i+1}',coluna=j+1,nivel_placa=i+1,x=(i-(levels-1)/2)*192,y=(j-.5)*pitch,z=0) for j in range(2) for i in range(levels)]
    ports=[dict(name=c['nome']+'_'+p['name'],celula=c['nome'],polarizacao=p['name'],x=c['x']+p['x'],y=c['y']+p['y'],z=14.949-50,ri=.45975,ro=1.515) for c in cells for p in g['inputs']]
    height=184+(levels-1)*192
    cfg.update(revisao=tag,native='P2M21_%dcelulas_%dmm.aedt'%(levels*2,pitch),cad_native='P2M21_%dcelulas_%dmm.FCStd'%(levels*2,pitch),design='Celulas_%dx2'%levels,
        celulas=cells,portas=ports,niveis_placas=levels,radiadores=levels*8,niveis_radiadores=levels*4,
        passo_horizontal_mm=pitch,folga_placas_horizontal_mm=pitch-70,envolvente_placas_mm=[pitch+70,height],
        refletor_mm=[162,height+16,2],potencia_por_porta_W=1/len(ports),
        observacao='Todas as entradas coerentes, 1 W total. Estudo apenas em 5.17 GHz. Nao comprova ganho MIMO por entrada.',
        controle_comparacao='Largura do refletor mantida em 162 mm. R16 muda apenas o passo horizontal e os furos coaxiais. R17 acrescenta um nivel de PCB em cada coluna e estende o refletor 192 mm.',
        fonte_referencia_8passes='D:/dev/EMBRAER/P2M21/R15_Oito_Celulas_8passes')
    for name,data in [('configuracao.json',cfg),('qualificacao.json',dict(estado='PREPARANDO_CAD',simulado=False))]:
        (root/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    shutil.copy2(BASE/'HFSS_14nucleos.acf',root/'HFSS_14nucleos.acf')
    plan.append(dict(root=str(root),niveis_placas=levels,colunas=2,portas=len(ports),max_passes=6,delta_s=.05,sem_sweep=True))
out=BASE.parent/'comparacao_colunas_niveis';out.mkdir(exist_ok=True)
(out/'plano.json').write_text(json.dumps(dict(referencia='R15_Oito_Celulas_8passes',variantes=plan,frequencia_GHz=5.17,nucleos=14,serial=True),indent=2)+'\n',encoding='utf-8')
print(json.dumps(plan,indent=2))
