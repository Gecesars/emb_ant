"""Confere que a variacao geometrica fica somente nos transformadores simetricos."""
from pathlib import Path
import argparse,json
from shapely.geometry import shape
p=argparse.ArgumentParser();p.add_argument('placa');args=p.parse_args()
old=Path('D:/dev/EMBRAER/P2S13/R01_Seis_Elementos/celula2_simetrica');new=Path(args.placa)
a=json.loads((old/'geometria.json').read_text());b=json.loads((new/'geometria.json').read_text())
x={(l['layer'],l['net']):shape(l['geometry']) for l in a['lands']};y={(l['layer'],l['net']):shape(l['geometry']) for l in b['lands']}
assert x.keys()==y.keys();changes=[]
for k in x:
    area=x[k].symmetric_difference(y[k]).area
    if area>1e-8:changes.append(dict(layer=k[0],net=k[1],area_alterada_mm2=area))
assert {(r['layer'],r['net']) for r in changes}=={('F','SIG_A'),('F','SIG_B')}
assert a['outline']==b['outline'] and a['inputs']==b['inputs'] and a['vias']==b['vias']
assert b['simetria']['sinal_A_vs_B_espelhado_mm2']<1e-8 and b['simetria']['retorno_A_vs_B_espelhado_mm2']<1e-8
assert max(b['simetria']['comprimentos_ramos_mm'])-min(b['simetria']['comprimentos_ramos_mm'])<1e-9
report=dict(mudancas=changes,radiadores_retornos_portas_vias_outline_preservados=True,simetria=b['simetria'],escopo='Comparacao dos poligonos: somente sinais frontais A/B alterados; novos sinais simetricos, caminhos iguais.')
(new/'alteracoes_conferidas.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
