"""Confere as larguras reais nas juntas planas, sem executar CAD ou RF."""
from pathlib import Path
import argparse,json,math
from shapely.geometry import shape,LineString

def audit(folder):
    folder=Path(folder);g=json.loads((folder/'geometria.json').read_text());p=g['parametros']
    assert p.get('root_flat_sections',False),'Auditoria especifica para transicoes planas'
    rows=[]
    for trace in g['traces']:
        if trace['tipo']!='raiz':continue
        pol=trace['polarizacao']
        metal=shape(next(v['geometry'] for v in g['lands'] if v['layer']=='F' and v['net']=='SIG_'+pol))
        width=g['lines'][str(math.sqrt(2)*50)]['w_mm']*p['root_w_'+pol]
        sections=[dict(linha=trace['linha70'],largura_mm=width)]+trace.get('secoes_adicionais',[])
        tail=trace.get('linha50_final',trace['linha50'])
        sections.append(dict(linha=tail[:2],largura_mm=trace['largura_segmento_pos_mm']))
        for index,sec in enumerate(sections):
            a,b=sec['linha'];sign=1 if b[0]>a[0] else -1;y=a[1]
            samples=[a[0]+sign*.01,(a[0]+b[0])/2]
            if index<len(sections)-1:samples.append(b[0]-sign*.01)
            for x in samples:
                actual=metal.intersection(LineString([(x,y-3),(x,y+3)])).length
                assert abs(actual-sec['largura_mm'])<2e-6,(pol,trace['grupo'],index,x,actual,sec['largura_mm'])
                rows.append(dict(polarizacao=pol,ramo=trace['grupo'],secao=index+1,x_mm=x,largura_real_mm=actual,largura_prevista_mm=sec['largura_mm']))
    result=dict(aprovado=True,amostras=rows,tolerancia_mm=2e-6,metodo='Cortes do cobre real junto as transicoes e no centro. Na cauda, evita-se a curva em mitra.')
    (folder/'transicoes_auditadas.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('TRANSICOES_OK',folder.name,len(rows))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('pasta');a=p.parse_args();audit(a.pasta)
