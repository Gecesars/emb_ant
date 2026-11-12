"""Pacote R12: preparado nao copia o AEDT ativo; final exige nativo fechado."""
from pathlib import Path
import json,hashlib,shutil,argparse
ROOT=Path('D:/dev/EMBRAER/P2S13/R12_Curvilinear_Simplificado')
REPO=Path(__file__).resolve().parents[3];OUT=REPO/'projetos/P2S13/curvilinear_simplificado'
ap=argparse.ArgumentParser();ap.add_argument('--final',action='store_true');args=ap.parse_args()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cfg=read(ROOT/'configuracao.json');proof=read(ROOT/'setup_confirmado.json');cad=read(ROOT/'cad/simplificacao.json')
assert cad['aprovado'] and proof['curvilinear'] and proof['solver']=='Direct Solver' and proof['max_passes']==6
if args.final:
    assert not list(ROOT.glob('*.aedt.lock'))
    assert read(ROOT/'qualificacao.json')['estado']=='SOLVE_EXPORTADO_AGUARDA_AUDITORIA'
    result=read(ROOT/'resultado.json')
    assert result['fontes_sha256'][cfg['native']]==sha(ROOT/cfg['native'])
items=[]
def copy(n):
    s=ROOT/n;d=OUT/n;assert s.is_file(),s
    d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s,d)
    assert sha(s)==sha(d)
    items.append(dict(arquivo=str(d.relative_to(REPO)).replace('\\','/'),sha256=sha(d),bytes=d.stat().st_size))
for n in ['configuracao.json',cfg['cad_native'],'HFSS_14nucleos.acf','setup_confirmado.json','hfss_validacao.json','geometria_importada.json',
          'cad/simplificacao.json','cad/manifesto.json','cad/folhas_solidas.json','cad/portas.json','cad/intersecoes.json','cad/geometria_esperada.json','cad/reabertura.json','cad/enig_hfss.json']:
    copy(Path(n))
if args.final:
    for n in [cfg['native'],'resultado.json','centro.s2p','convergencia.txt','historico_passes.json','convergencia_campos.json',
        'conferencia_perfil.json','recursos_matriz.json','auditoria_solver_matricial.json','malha.json','mensagens.json',
        'potencia.json','potencia_conferida.json','polar_HV.png','simetria_vertical.png','pipeline.json','qualificacao.json','estado.json',
        'recuperacao_auditoria.json','ordem_fontes.json']:
        if (ROOT/n).exists():copy(Path(n))
    for pattern in ['ALL_*.csv','POL_*.csv','IN_*.csv','diagrama_*.csv']:
        for p in ROOT.glob(pattern):copy(Path(p.name))
s=(ROOT/'README.md').read_text(encoding='utf-8')
state='Calculo em andamento; sem resultados RF nesta copia. O AEDT ativo permanece somente na pasta de trabalho.'
if args.final:state='Calculo encerrado. '+('Metas nominais atendidas.' if result['validacao_nominal'] else 'Validacao RF pendente/reprovada; consultar resultado.json.')
(OUT/'README.md').write_bytes((s+'\n## Estado do pacote\n\n'+state+'\n').encode('utf-8'))
items.append(dict(arquivo=str((OUT/'README.md').relative_to(REPO)).replace('\\','/'),sha256=sha(OUT/'README.md'),bytes=(OUT/'README.md').stat().st_size))
(OUT/'manifesto.json').write_text(json.dumps(dict(tipo='FINAL_EXPORTADO' if args.final else 'PREPARADO_EM_CALCULO',
    arquivos=items,excluidos=['aedtresults','malhas','g3derr','camposvolumetricos','locks']),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps(dict(destino=str(OUT),arquivos=len(items),estado=state),ensure_ascii=False))
