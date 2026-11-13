"""Prepara um candidato independente da P2M19; não inicia nenhum solver."""
from pathlib import Path
import argparse,hashlib,json

REPO=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
BASE=Path('D:/dev/EMBRAER/P2M19/R01_16x2_88mm')

def prepare(name,pitch=72,width=178,height=14.949):
    root=BASE.parent/name
    assert not root.exists(),f'Já existe: {root}'
    assert pitch>=72 and width>=pitch+74 and 13.4541<=height<=16.4439
    cfg=json.loads((BASE/'configuracao.json').read_text())
    assert cfg['max_passes']==6 and cfg['max_delta_s']==.05 and cfg['nucleos']==14
    cells=cfg['celulas']
    for c in cells:c['y']=(c['coluna']-1.5)*pitch
    byname={c['nome']:c for c in cells}
    for p in cfg['portas']:
        c=byname[p['celula']]
        p['y']=c['y']+(-32 if p['polarizacao']=='A' else 32)
    cfg.update(revisao='P2M19_'+name,native='P2M19_'+name+'.aedt',cad_native='P2M19_'+name+'.FCStd',
        design='P2M19_'+name,passo_horizontal_mm=pitch,folga_placas_horizontal_mm=pitch-70,
        envolvente_placas_mm=[pitch+70,760],refletor_mm=[width,776,2],
        distancia_face_inferior_laminado_ao_refletor_mm=height,refletor_topo_z_mm=14.949-height,
        meta_H_graus=30,tolerancia_H_graus=None,
        referencia_historica='projetos/P2M19/centro_16x2_88mm',
        referencia_comparacao=str(BASE),
        limites_referencia='R01 não convergiu; diferenças entre candidatos são preliminares até confirmação.',
        controle_comparacao='Mesmo CAD C12, materiais, portas, excitação e setup da R01. Apenas passo horizontal e parâmetros do refletor declarados neste caso.',
        alteracoes_vs_R01=dict(passo_horizontal_mm=[88,pitch],largura_refletor_mm=[178,width],altura_pcb_ao_refletor_mm=[14.949,height]),
        gerador_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    root.mkdir(parents=True);scripts=root/'scripts';scripts.mkdir()
    (root/'configuracao.json').write_text(json.dumps(cfg,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (root/'qualificacao.json').write_text(json.dumps(dict(estado='PREPARANDO_CAD',simulado=False)),encoding='utf-8')
    (root/'HFSS_14nucleos.acf').write_bytes((BASE/'HFSS_14nucleos.acf').read_bytes())
    for filename in ['criar_cad.py','criar_hfss.py','resolver.py','analisar.py','layout.py']:
        text=(HERE/filename).read_text(encoding='utf-8')
        assert BASE.as_posix() in text,filename
        text=text.replace(BASE.as_posix(),root.as_posix())
        text=text.replace('REPO=Path(__file__).resolve().parents[3]',f'REPO=Path({str(REPO)!r})')
        if filename=='criar_cad.py':
            text=text.replace("A.newDocument('P2M19_16x2_88mm')","A.newDocument(cfg['design'])")
            text=text.replace("A.Vector(-rh/2,-rw/2,-rt)","A.Vector(-rh/2,-rw/2,cfg['refletor_topo_z_mm']-rt)")
            text=text.replace("A.Vector(p['x'],p['y'],-rt)","A.Vector(p['x'],p['y'],cfg['refletor_topo_z_mm']-rt)")
        elif filename=='analisar.py':
            text=text.replace("old=REPO/'projetos/P2M21/comparacao_colunas_niveis/R15_Oito_Celulas_8passes'",f'old=Path({str(BASE)!r})')
            text=text.replace("desvio_H_para_20_graus=result['cortes']['H']['abertura_graus']-20","desvio_H_para_30_graus=result['cortes']['H']['abertura_graus']-30")
            text=text.replace('passo_horizontal_mm=88,passo_vertical_mm=48',"passo_horizontal_mm=cfg['passo_horizontal_mm'],passo_vertical_mm=48")
            text=text.replace('R15: 16x2, 48 x 72 mm, cabos50mm; nao convergido','R01: 16x2, 48 x 88 mm; nao convergido')
            text=text.replace('R15_72mm_cabos50mm_nao_convergido','R01_88mm_nao_convergido')
            text=text.replace('Geometrias, passos, refletores e redes diferentes: comparacao historica, sem isolar a causa das diferencas.','R01 e candidato: conferir convergencia antes de atribuir diferencas pequenas a geometria.')
        (scripts/filename).write_text(text,encoding='utf-8')
    manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in scripts.glob('*.py')}
    (root/'scripts_sha256.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(root)
    return root

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('nome');p.add_argument('--passo',type=float,default=72)
    p.add_argument('--refletor',type=float,default=178);p.add_argument('--altura',type=float,default=14.949)
    a=p.parse_args();prepare(a.nome,a.passo,a.refletor,a.altura)
