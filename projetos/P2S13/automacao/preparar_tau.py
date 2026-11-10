"""Copias exatas do CAD para diagnostico de geracao de malha TAU estrita."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path('D:/dev/EMBRAER/P2S13/R00_Refletor_Dobrado')
e=[]
for old,new in [('v01_b20_a60','v03_b20_a60_tau'),('v02_b30_a60','v04_b30_a60_tau')]:
    src=ROOT/old;dst=ROOT/new
    assert not dst.exists(),dst
    dst.mkdir();(dst/'cad').mkdir()
    before=json.loads((src/'configuracao.json').read_text());cfg=dict(before)
    cfg.update(revisao=new,mesh_method='AnsoftTAU',malha='TAU estrito automatico 5; Flex e fallback desativados, sem refinamentos locais/iniciais, sem MeshLink, DoLambdaRefine=False; adaptacao durante solve 50%',referencia_geometria_identica=old)
    (dst/'configuracao.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
    (dst/'qualificacao.json').write_text(json.dumps(dict(estado='CAD_IDENTICO_PREPARADO_TAU',simulado=False))+'\n')
    files=[src/'P2S13.FCStd',src/'HFSS_14nucleos.acf']+list((src/'cad').glob('*.step'))+[src/'cad'/n for n in ['manifesto.json','folhas_solidas.json','portas.json','intersecoes.json','reabertura.json']]
    copied=[]
    for f in files:
        target=dst/f.relative_to(src);shutil.copy2(f,target)
        sha=hashlib.sha256(f.read_bytes()).hexdigest();assert hashlib.sha256(target.read_bytes()).hexdigest()==sha
        copied.append(dict(arquivo=f.relative_to(src).as_posix(),sha256=sha))
    e.append(dict(origem=old,destino=new,arquivos_identicos=copied,alteracoes_configuracao=[k for k in cfg if cfg.get(k)!=before.get(k)]))
(ROOT/'diagnostico_classic/copias_tau.json').write_text(json.dumps(e,indent=2)+'\n')
q=ROOT/'v01_b20_a60/qualificacao.json';r=json.loads(q.read_text());r.update(estado='INTERROMPIDO_GERACAO_INICIAL_SEM_PASSE_RF',evidencia='../diagnostico_classic/interrupcao.json');q.write_text(json.dumps(r,indent=2)+'\n')
r=json.loads((ROOT/'requisitos.json').read_text());r['diagnostico_mesher']='Classic inicial interrompido apos 56,66 minutos; comparar TAU estrito com CAD identico, sem relaxamento geometrico.';r['candidatos_tau']=[x['destino'] for x in e];(ROOT/'requisitos.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(e,indent=2))
