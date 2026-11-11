"""Prepara candidato de casamento da PCB2 e painel4+2; sem executar HFSS."""
from pathlib import Path
import argparse,json,hashlib,subprocess,sys,shutil
REPO=Path(__file__).resolve().parents[3];ROOT=Path('D:/dev/EMBRAER/P2S13/R02_Casamento_Placa2')
p=argparse.ArgumentParser();p.add_argument('nome');p.add_argument('--width',type=float);p.add_argument('--length',type=float);p.add_argument('--montagem',action='store_true');a=p.parse_args()
assert len(a.nome)==3 and a.nome[0]=='m' and a.nome[1:].isdigit()
folder=ROOT/a.nome;cell=folder/'placa2'
if not a.montagem:
    assert not folder.exists(),folder
    assert a.width is not None and a.length is not None
    subprocess.run([sys.executable,str(Path(__file__).with_name('seis_preparar_celula2.py')),'--out',str(cell),'--width',str(a.width),'--length',str(a.length)],check=True)
else:
    assert not (folder/'configuracao.json').exists()
    base=REPO/'projetos/P2S13/seis_elementos/s02_b10_a90'
    cfg=json.loads((base/'configuracao.json').read_text());new=next(c for c in cfg['celulas'] if c['radiadores']==2)
    files=['2_elementos_simetrica.FCStd','geometria.json','cad/manifesto.json','cad/folhas_solidas.json']
    new.update(fonte=str(cell),fontes_sha256={n:hashlib.sha256((cell/n).read_bytes()).hexdigest() for n in files})
    cfg.update(revisao=a.nome,native='P2S13_Casamento2.aedt',cad_native='P2S13_Casamento2.FCStd',design='Casamento_Placa2',
        estudo='Ajuste simetrico de largura/comprimento dos transformadores da PCB2; PCB4, refletor b10/90, cabos, entradas e radiadores inalterados.',
        meta_VSWR_placa2=1.25,criterio_VSWR='Ativo com quatro entradas iguais/em fase e com outras entradas casadas',fonte_referencia=str(base))
    cfg['solidos_fisicos']=1+sum(len(json.loads((Path(c['fonte'])/'cad/manifesto.json').read_text()))-1 for c in cfg['celulas'])
    (folder/'configuracao.json').write_text(json.dumps(cfg,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    shutil.copy2(base/'HFSS_14nucleos.acf',folder/'HFSS_14nucleos.acf')
    (folder/'qualificacao.json').write_text('{"estado":"PREPARANDO_CAD","simulado":false}\n')
    print(json.dumps(dict(pasta=str(folder),solidos=cfg['solidos_fisicos'])))
