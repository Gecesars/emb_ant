"""Prepara estudo controlado de altura a partir de um caso HFSS ja resolvido."""
from pathlib import Path
import argparse,copy,hashlib,json
from shapely.geometry import shape,LineString
from quatro_ajustar_preparar import build,ROOT

def main(source):
    base=ROOT/source
    cfg=json.loads((base/'configuracao.json').read_text())
    geo=json.loads((base/'geometria.json').read_text())
    result=json.loads((base/'resultado.json').read_text())
    assert result['fisica_ok'] and cfg['parametros']['simetria']
    assert cfg['max_passes']==6 and cfg['max_delta_s']==.05 and cfg['nucleos']==14
    h=cfg.get('distancia_face_inferior_laminado_ao_refletor_mm',16.61)
    cases=[('v19_altura_menos10',round(h*.9,6)),('v20_altura_mais10',round(h*1.1,6))]
    assert not (ROOT/'plano_alturas.json').exists(), 'Nao duplicar estudo de alturas'
    audit=[]
    for name,height in cases:
        params=copy.deepcopy(cfg['parametros']);params['pcb_z']=height
        build(name,params)
        folder=ROOT/name;new=json.loads((folder/'geometria.json').read_text())
        for key in ['outline','vias','inputs','centros_HFSS_X_mm','placa_largura_altura_mm','refletor_planejado_mm']:
            assert new[key]==geo[key],key
        old_shapes={(q['layer'],q['net']):shape(q['geometry']) for q in geo['lands']}
        new_shapes={(q['layer'],q['net']):shape(q['geometry']) for q in new['lands']}
        assert old_shapes.keys()==new_shapes.keys()
        errors={str(k):old_shapes[k].symmetric_difference(new_shapes[k]).area for k in old_shapes}
        assert max(errors.values())<1e-8,errors
        lengths={}
        for pol in 'AB':
            roots=[q for q in new['traces'] if q['polarizacao']==pol and q['tipo']=='raiz']
            locals_=[q for q in new['traces'] if q['polarizacao']==pol and q['tipo']=='local']
            paths=[]
            for local in locals_:
                root=next(q for q in roots if (q['grupo']>0)==(local['cx']>0))
                paths.append(sum(LineString(q['linha70']+q['linha50'][1:]).length for q in [root,local]))
            lengths[pol]=paths
        vals=lengths['A']+lengths['B'];assert max(vals)-min(vals)<1e-8
        (folder/'caminhos_alimentacao.json').write_text(json.dumps(dict(caminhos_impressos_mm=lengths,cabos_mm=[50,50],fontes_W=[.5,.5],fontes_graus=[0,0],escopo='Comprimentos geometricos iguais; sem compensacao externa de fase.'),indent=2)+'\n',encoding='utf-8')
        audit.append(dict(variante=name,altura_mm=height,delta_z_mm=height-h,area_diferente_cobre_mm2=max(errors.values()),vias_iguais=True,contornos_iguais=True,portas_XY_iguais=True,caminhos_mm=lengths,setup_herdado=cfg['parametros']))
    plan=dict(fonte=source,passo_mm=cfg['espacamento_vertical_mm'],altura_nominal_mm=h,variantes=[source]+[q[0] for q in cases],
        criterio_selecao='Melhor candidato numerico entre os ensaios existentes que atende G0>=12 e VSWR<1.3. Nao e prova de otimo global; convergencia incompleta explicitada.',
        fonte_convergiu=result['convergiu'],referencia='Face inferior do laminado ate topo do refletor Z=0; cobre inferior35um fica0.035mm mais perto.',
        controle='Somente transladar PCB e ambos os cabos de50mm emZ; refletor fixo. Mesmas trilhas, radiadores, materiais, contornos, fases, amplitudes e criterios do solver. Nominal reutilizado sem solve adicional.',
        fonte_sha256={f:hashlib.sha256((base/f).read_bytes()).hexdigest() for f in ['P2M21_4_elementos.aedt','geometria.json','configuracao.json','resultado.json','centro.s2p']},auditoria_planar=audit)
    (ROOT/'plano_alturas.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(plan,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('fonte');main(p.parse_args().fonte)
