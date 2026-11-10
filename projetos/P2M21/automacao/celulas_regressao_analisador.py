"""Reprocessa a referencia conhecida em copia isolada; nunca modifica R14."""
from pathlib import Path
import json,shutil,os,subprocess,sys,hashlib
source=Path('D:/dev/EMBRAER/P2M21/R14_Oito_Celulas')
dest=source.parent/'comparacao_colunas_niveis/regressao_analisador'
assert not dest.exists();dest.mkdir()
cfg=json.loads((source/'configuracao.json').read_text())
names=[cfg['native'],'configuracao.json','qualificacao.json','convergencia.txt','centro.s16p']+[p.name for p in source.glob('*.csv')]
for name in names:shutil.copy2(source/name,dest/name)
tree=(source/cfg['native']).with_suffix('.aedtresults')
for p in tree.rglob('*'):
    if p.is_file() and (p.suffix in ['.profile','.EMConvData','.ExprCache'] or p.name=='nominalmesh.g3derr'):
        out=dest/p.relative_to(source);out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
env=dict(os.environ,P2M21_OITO_ROOT=str(dest))
with (dest/'analise.log').open('w') as f:subprocess.run([sys.executable,str(Path(__file__).with_name('oito_celulas_analisar.py'))],env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
a=json.loads((source/'resultado.json').read_text());b=json.loads((dest/'resultado.json').read_text())
keys=['passes','delta_s','convergiu','VSWR_ativo','VSWR_casado','potencia_aceita_W','maior_singular','reciprocidade','cortes','grupos_polarizacao','recomposicao','potencia','fisica_ok','estavel_nove_sondas','validado_numericamente']
assert all(a[k]==b[k] for k in keys)
proof=dict(aprovado=True,campos_comparados=keys,resultado_original_sha256=hashlib.sha256((source/'resultado.json').read_bytes()).hexdigest(),resultado_reprocessado_sha256=hashlib.sha256((dest/'resultado.json').read_bytes()).hexdigest(),fonte_preservada=True)
(dest.parent/'regressao_analisador.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print('REGRESSAO_NUMERICA_EXATA_APROVADA')
