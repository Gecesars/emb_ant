"""Arquiva variantes calculadas sem malhas ou campos volumetricos."""
from pathlib import Path
import json,hashlib,shutil
REPO=Path(__file__).resolve().parents[3];ROOT=Path('D:/dev/EMBRAER/P2S13/R04_Dobras_Ajustadas');OUT=REPO/'projetos/P2S13/dobras_placas_ajustadas';OUT.mkdir(exist_ok=True);entries=[]
def cp(p):
    assert p.is_file(),p
    assert not any(t.lower().endswith('.aedtresults') for t in p.parts)
    assert p.suffix.lower() not in ['.g3derr','.fld','.adp','.ngmesh','.lock']
    dest=OUT/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    h=hashlib.sha256(p.read_bytes()).hexdigest();assert hashlib.sha256(dest.read_bytes()).hexdigest()==h
    entries.append(dict(arquivo=dest.relative_to(REPO).as_posix(),fonte=str(p),sha256=h,bytes=p.stat().st_size))
for n in ['comparacao.json','comparacao.csv','comparacao_HV.png','perfis_refletor.png','entrega.json','auditoria_campanha.json']:cp(ROOT/n)
if (ROOT/'interrupcao.json').exists():cp(ROOT/'interrupcao.json')
for p in sorted(ROOT.glob('d*/resultado.json')):
    folder=p.parent;c=json.loads((folder/'configuracao.json').read_text());assert not (folder/(c['native']+'.lock')).exists()
    for n in [c['native'],c['cad_native'],'HFSS_14nucleos.acf','configuracao.json','origem.json','resultado.json','convergencia.txt','historico_passes.json','recursos_matriz.json','ordem_fontes.json','malha.json','malha_inicial.json','estatisticas_malha_inicial.txt','geracao_malha.json','mensagens.json','mensagens_malha.json','hfss_validacao.json','conferencia_reconstrucao.json','diagramas_HV.png','polar_HV.png','centro.s4p','cad/AL5052.step']:cp(folder/n)
    for f in sorted(folder.glob('*.csv')):
        if f.stem.startswith(('ALL_','POL_','R1_','R2_')):cp(f)
    for f in sorted((folder/'cad').glob('*.json')):cp(f)
(OUT/'manifesto.json').write_text(json.dumps(dict(artefatos=entries,total_bytes=sum(e['bytes'] for e in entries),excluidos='Malhas,aedtresults,g3derr,campos volumetricos,locks; referencia preservada na R03.'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(artefatos=len(entries),bytes=sum(e['bytes'] for e in entries))))
