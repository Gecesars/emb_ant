"""Congela R12 seis passes e copia resultados para somente passes 7/8."""
from pathlib import Path
import json,shutil,hashlib,ast
SOURCE=Path('D:/dev/EMBRAER/P2S13/R12_Curvilinear_Simplificado')
ROOT=Path('D:/dev/EMBRAER/P2S13/R12_Continuacao8')
HERE=Path(__file__).parent
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def change(s,a,b):
    assert a in s,a
    return s.replace(a,b)
assert not ROOT.exists(),'Continuacao existente; nao duplicar'
cfg=read(SOURCE/'configuracao.json');r=read(SOURCE/'resultado.json')
assert r['passes']==6 and cfg['max_passes']==6 and len(cfg['portas'])==2
assert cfg['solver_type']=='Direct Solver' and cfg['curvilinear'] and cfg['nucleos']==14 and not cfg['sweep']
assert not (SOURCE/(cfg['native']+'.lock')).exists()
ROOT.mkdir();ref=ROOT/'referencia6';ref.mkdir()
static=[cfg['native'],cfg['cad_native'],'configuracao.json','HFSS_14nucleos.acf','hfss_validacao.json','conferencia_reconstrucao.json','geometria_importada.json','setup_confirmado.json']
for n in static:shutil.copy2(SOURCE/n,ROOT/n)
shutil.copytree(SOURCE/'cad',ROOT/'cad')
baseline=[cfg['native'],'configuracao.json','convergencia.txt','resultado.json','historico_passes.json','convergencia_campos.json','recursos_matriz.json','malha.json','centro.s2p','polar_HV.png','potencia.json']+[p.name for p in SOURCE.glob('*.csv')]
refs=[]
for n in sorted(set(baseline)):
    shutil.copy2(SOURCE/n,ref/n);assert sha(SOURCE/n)==sha(ref/n)
    refs.append(dict(arquivo=n,sha256=sha(ref/n)))
results=Path(cfg['native']).with_suffix('.aedtresults');entries=[]
shutil.copytree(SOURCE/results,ROOT/results)
for p in (SOURCE/results).rglob('*'):
    if p.is_file():
        rel=p.relative_to(SOURCE);h=sha(p);assert sha(ROOT/rel)==h
        entries.append(dict(arquivo=rel.as_posix(),bytes=p.stat().st_size,sha256=h))
cfg.update(revisao='R12_Continuacao8',max_passes=8,min_passes=8,passes_iniciais=6,passes_adicionais_autorizados=2,fonte_continuacao=str(SOURCE),referencia_continuacao=str(ref))
write(ROOT/'configuracao.json',cfg)
write(ROOT/'origem.json',dict(fonte=str(SOURCE),native_sha256=sha(SOURCE/cfg['native']),referencias=refs,arquivos_resultados_copiados=entries))
write(ROOT/'qualificacao.json',dict(estado='COPIA_PRONTA_AGUARDA_CONFIGURACAO'))
# Reusar API parcial comprovada, sem criar setup, cache ou geometria.
s=(HERE/'continuar2_aedt.py').read_text(encoding='utf-8-sig')
s=change(s,'len(ports) in [4,6]','len(ports)==2')
old="        sources(sol,ports);p.Save();oDesktop.CloseProject(p.GetName());p=None\n        write('qualificacao.json'"
fine=(HERE/'r12_resolver.py').read_text(encoding='utf-8-sig')
fine=fine[fine.index("    sources(sol,ports)\n    reports.CreateReport('ALL_V_fino'"):fine.index("    sources(sol,ports);p.SaveAs(native,True)")]
fine=fine.replace("    reports.CreateReport('ALL_V_fino'", "    if 'ALL_V_fino' in list(reports.GetAllReportNames()):reports.DeleteReports(['ALL_V_fino'])\n    reports.CreateReport('ALL_V_fino'")
fine='\n'.join('    '+line for line in fine.splitlines())+'\n'
s=change(s,old,fine+old)
ast.parse(s);(HERE/'r12_continuar_aedt.py').write_text(s,encoding='utf-8')
s=(HERE/'continuar2_auditar.py').read_text(encoding='utf-8-sig')
s=change(s,'count in [4,6]','count==2')
s=change(s,"(REF/'historico_passes.json').read_text()", "(REF/'convergencia_campos.json').read_text()")
s=change(s,"assert len(checked)>=8", "assert len(checked)>=6")
ast.parse(s);(HERE/'r12_continuar_auditar.py').write_text(s,encoding='utf-8')
s=(HERE/'r12_analisar.py').read_text(encoding='utf-8-sig')
s=change(s,"assert passes<=int(grab(r'Maximum\\s*:\\s*(\\d+)'))==6", "assert passes==int(grab(r'Maximum\\s*:\\s*(\\d+)'))==cfg['max_passes']==8")
s=change(s,'"MaxPasses=\'6\'" in t and "MinPasses=\'2\'" in t', '"MaxPasses=\'8\'" in t and "MinPasses=\'8\'" in t')
s=change(s,'R12 curvilinear — antena','R12 continuação 7/8 — antena')
s=change(s,"    fig.text(.5,.84,'PRELIMINAR — malha não convergida',ha='center',color='darkorange',weight='bold')", "    fig.text(.5,.84,'PRELIMINAR — malha não convergida',ha='center',color='darkorange',weight='bold')\nelif not r['validacao_nominal']:\n    fig.text(.5,.84,'ΔS convergiu — metas RF e estabilidade de campo pendentes',ha='center',color='darkorange',weight='bold')")
s=change(s,"    fig.suptitle('PRELIMINAR — 5,17 GHz | entradas 0,5 W / 0° | malha não convergida',color='darkorange')", "    fig.suptitle('PRELIMINAR — 5,17 GHz | entradas 0,5 W / 0° | malha não convergida',color='darkorange')\nelif not r['validacao_nominal']:\n    fig.suptitle('PRELIMINAR — 5,17 GHz | entradas 0,5 W / 0° | metas RF pendentes',color='darkorange')")
s=change(s,"profiles=list(mp.parent.glob(prefix+'_V*.profile'));assert len(profiles)==1,profiles", """profiles=[]
for candidate in mp.parent.glob(prefix+'_V*.profile'):
    raw_profile=candidate.read_text(errors='replace').replace("\\\\'","'")
    candidate_tets={}
    for block in re.finditer(r"Name='Adaptive Pass (\\d+)'(.*?)(?=Name='Adaptive Pass |\\Z)",raw_profile,re.S):
        line=next((x for x in block[2].splitlines() if x.strip().startswith("ProfileItem('Simulation Setup '")),None)
        if line:candidate_tets[int(block[1])]=int(re.search(r"'Tetrahedra', (\\d+)",line)[1])
    if candidate_tets=={x['passe']:x['tetraedros'] for x in hist}:profiles.append(candidate)
assert len(profiles)==1,profiles""")
ast.parse(s);(HERE/'r12_continuar_analisar.py').write_text(s,encoding='utf-8')
print(json.dumps(dict(arquivos_copiados=len(entries),bytes=sum(e['bytes'] for e in entries),malha_preservada=True)))
