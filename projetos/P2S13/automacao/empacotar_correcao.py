"""Arquiva resultado central e evidencias da correcao, sem malhas ou caches de solver."""
from pathlib import Path
import json,shutil,hashlib
REPO=Path(__file__).resolve().parents[3];BASE=REPO/'projetos/P2S13';WORK=Path('D:/dev/EMBRAER/P2S13/R00_Refletor_Dobrado')
FINAL=WORK/'v12_b20_a60_refletor_nativo'
assert json.loads((FINAL/'qualificacao.json').read_text())['estado']=='ANALISE_CONCLUIDA'
assert json.loads((FINAL/'malha_inicial.json').read_text())['reparos_major']==0
records=[]
def copy(source,dest):
    assert source.is_file(),source
    assert not any(x.lower().endswith('.aedtresults') for x in source.parts)
    assert source.suffix.lower() not in ['.g3d','.g3derr','.lock','.ngmesh']
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
    digest=hashlib.sha256(source.read_bytes()).hexdigest();assert hashlib.sha256(dest.read_bytes()).hexdigest()==digest
    records.append(dict(arquivo=dest.relative_to(REPO).as_posix(),fonte=str(source),bytes=source.stat().st_size,sha256=digest))
common=['configuracao.json','resultado.json','historico_passes.json','convergencia.txt','centro.s4p','recursos_matriz.json','mensagens.json','malha.json','hfss_validacao.json','ordem_fontes.json','qualificacao.json','diagramas_HV.png','polar_HV.png','HFSS_14nucleos.acf']
for folder,target in [(WORK/'v00_plano',BASE/'referencia_plana'),(FINAL,BASE/'refletor_nativo_b20_60')]:
    cfg=json.loads((folder/'configuracao.json').read_text());assert not (folder/(cfg['native']+'.lock')).exists()
    for name in common+[cfg['native'],cfg['cad_native']]:copy(folder/name,target/name)
    for f in sorted(folder.glob('*.csv')):
        if f.stem.startswith(('ALL_','POL_','R1_','R2_')):copy(f,target/f.name)
for name in ['geracao_malha.json','malha_inicial.json','estatisticas_malha_inicial.txt','mensagens_malha.json','reconstrucao_refletor.json','conferencia_refletor_nativo.json','Refletor_nativo.step']:
    copy(FINAL/name,BASE/'refletor_nativo_b20_60'/name)
for f in sorted((FINAL/'cad').iterdir()):
    if f.is_file() and f.suffix.lower() in ['.step','.json']:copy(f,BASE/'refletor_nativo_b20_60/cad'/f.name)
for name in ['comparacao.json','comparacao.csv','comparacao_HV.png','comparacao_normalizada.png']:
    copy(WORK/name,BASE/name)
evidence={
 'diagnostico_classic/interrupcao.json':'classic_original_interrompido.json',
 'diagnostico_setup/comparacao_facetas.json':'comparacao_facetas.json',
 'v03_b20_a60_tau/centro_aedt.log':'falha_tau_estrita.txt',
 'v12_b20_a60_refletor_nativo/centro.log':'execucao_rf_nativo.txt',
 'diagnostico_setup/diff_setups.json':'diferencas_setups.json',
 'diagnostico_setup/auditoria_roundtrip_hfss.json':'auditoria_refletor_cabos.json',
 'diagnostico_setup/tentativa_dinamica.json':'interrupcao_dinamica.json',
 'diagnostico_setup/tentativa_aspecto20.json':'interrupcao_aspecto.json',
 'v08_b20_a60_flex/geracao_malha.json':'flex_geracao.json',
 'v08_b20_a60_flex/mensagens_malha.json':'flex_avisos.json',
 'v09_b20_a60_interface/desvios_reparos.json':'flex_desvios_geometricos.json',
 'v10_b20_a60_prioridade/mensagens_malha.json':'prioridade_local_avisos.json',
 'v11_b20_a60_rf_preservado/mensagens_malha.json':'prioridade_ampliada_avisos.json',
 'v11_b20_a60_rf_preservado/mudanca_setup.json':'persistencia_auditada.json',
}
for source,target in evidence.items():copy(WORK/source,BASE/'evidencias_diagnostico'/target)
(BASE/'manifesto_correcao.json').write_text(json.dumps(dict(artefatos=records,total_bytes=sum(x['bytes'] for x in records),excluidos='Malhas, aedtresults, campos volumetricos, g3d/g3derr, locks, caches e tentativas de nativos rejeitados.'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(arquivos=len(records),bytes=sum(x['bytes'] for x in records))))
