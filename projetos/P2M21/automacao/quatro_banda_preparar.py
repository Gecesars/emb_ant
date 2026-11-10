"""Cria variante simetrica R13 a partir de dimensoes propostas, sem solver."""
from pathlib import Path
import argparse,json,copy,hashlib
import quatro_ajustar_preparar as builder
from quatro_banda_estimar import ROOT,BASE,VSWR_TARGET

def prepare(name,proposal_file,proposal_key,basis_order=None,dipole_scale=None,min_passes=2):
    assert 2<=min_passes<=6
    data=json.loads(Path(proposal_file).read_text());source=Path(data['fonte'])
    assert hashlib.sha256((source/data['arquivo_s2p']).read_bytes()).hexdigest()==data['s2p_sha256']
    p=copy.deepcopy(json.loads((source/'geometria.json').read_text())['parametros'])
    p.update(data[proposal_key]['fatores'])
    assert not any(p.get('root_stub_l_'+pol,0.) for pol in 'AB'),'Stub apenas estimado; geometria ainda nao implementada. Nao ignorar parametro.'
    p.update(pitch=48.,pcb_z=14.949,adapt=75,diagnostico_campos=False,simetria=True,contorno_centrado=True)
    if basis_order is not None:p['basis_order']=basis_order
    if dipole_scale is not None:p['dipolo_escala_externa']=dipole_scale
    builder.ROOT=ROOT;builder.build(name,p);f=ROOT/name
    cfg=json.loads((f/'configuracao.json').read_text());cfg.update(sweep='Fast apos verificacao dos diagramas centrais',max_passes=6,max_delta_s=.05)
    cfg['min_passes']=min_passes
    if min_passes!=2:
        creator=f/'criar_hfss.py';code=creator.read_text(encoding='utf-8')
        marker="'MinimumPasses:=',2"
        assert code.count(marker)==1
        creator.write_text(code.replace(marker,"'MinimumPasses:=',%d"%min_passes),encoding='utf-8')
    cfg['objetivo']='Minimizar o pior VSWR ativo na banda5.09–5.25GHz; fontes A=B=.5W/0graus; conferir tambem outra entrada casada e preservar diagrama em5.17GHz.'
    cfg.update(max_VSWR=VSWR_TARGET,VSWR_limite_inclusivo=True)
    proposal_bytes=Path(proposal_file).read_bytes()
    (f/'proposta_usada.json').write_bytes(proposal_bytes)
    cfg['origem_proposta']=dict(arquivo=str(proposal_file),chave=proposal_key,fonte_hfss=str(source),sha256=hashlib.sha256(proposal_bytes).hexdigest())
    (f/'configuracao.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    old=json.loads((BASE/'geometria.json').read_text());new=json.loads((f/'geometria.json').read_text())
    for key in ['outline','inputs','vias','passo_vertical_mm','distancia_pcb_refletor_mm']:
        assert old[key]==new[key],key
    # Alteracoes de largura sao nas faixas de sinal; retornos, vias e contorno iguais.
    from shapely.geometry import shape
    before={(x['layer'],x['net']):shape(x['geometry']) for x in old['lands']}
    after={(x['layer'],x['net']):shape(x['geometry']) for x in new['lands']}
    assert before.keys()==after.keys()
    changes={}
    for key in before:
        area=before[key].symmetric_difference(after[key]).area
        changes['/'.join(key)]=area
        allow_dipole=p.get('dipolo_escala_externa',1.)!=1. and key[0]=='B' and key[1]!='SIG_B' and key[1]!='SIG_A'
        if key not in [('F','SIG_A'),('F','SIG_B')] and not allow_dipole:assert area<1e-8,(key,area)
    (f/'alteracoes_geometricas.json').write_text(json.dumps(dict(areas_alteradas_mm2=changes,retornos_iguais=all(changes.get('B/'+net,0)<1e-8 for net in ['RET_A','RET_B']),vias_contorno_iguais=True,dipolo_escala_externa=p.get('dipolo_escala_externa',1.),adaptacao_percent=75,max_passes=6,delta_s=.05,basis_order=p.get('basis_order',-1)),indent=2)+'\n')
    from shapely.geometry import LineString
    paths=[]
    for pol in 'AB':
        for local in [t for t in new['traces'] if t['polarizacao']==pol and t['tipo']=='local']:
            root=next(t for t in new['traces'] if t['polarizacao']==pol and t['tipo']=='raiz' and t['grupo']*local['cx']>0)
            length=sum(LineString(t['linha70']+t['linha50'][1:]).length for t in [root,local])
            paths.append(dict(polarizacao=pol,centro_mm=local['cx'],trilha_mm=length,coax_mm=50.))
    assert max(t['trilha_mm'] for t in paths)-min(t['trilha_mm'] for t in paths)<1e-9
    (f/'caminhos_alimentacao.json').write_text(json.dumps(dict(caminhos=paths,comprimentos_fisicos_iguais=True,nota='A igualdade geometrica nao substitui a verificacao EM de amplitude e fase.'),indent=2)+'\n')
    if p.get('dipolo_escala_externa',1.)!=1.:
        from quatro_dipolos_ajustar import plot_change
        plot_change(BASE/'geometria.json',f/'geometria.json',f/'dipolos_detalhe.png')
    from quatro_banda_detalhar import draw
    draw(f)
    print('VARIANTE_R13_PREPARADA',f)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('nome');a.add_argument('proposta');a.add_argument('chave');a.add_argument('--basis-order',type=int,choices=[-1,0,1,2]);a.add_argument('--dipolo-escala',type=float);a.add_argument('--min-passes',type=int,choices=range(2,7),default=2);x=a.parse_args();prepare(x.nome,x.proposta,x.chave,x.basis_order,x.dipolo_escala,x.min_passes)
