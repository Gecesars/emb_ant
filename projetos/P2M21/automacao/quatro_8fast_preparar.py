"""Copia a solucao de seis passes; nao altera o projeto de origem nem simula."""
from pathlib import Path
import shutil,json,hashlib,re

SOURCE=Path('D:/dev/EMBRAER/P2M21/R11_Divisor_Ajustes/v21_altura_menos10_casada')
ROOT=Path('D:/dev/EMBRAER/P2M21/R12_Quatro_8Passes_Fast')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not ROOT.exists(),'Nao duplicar a continuacao'
assert not (SOURCE/'P2M21_4_elementos.aedt.lock').exists()
old=json.loads((SOURCE/'resultado.json').read_text());assert old['passes']==6
ROOT.mkdir();folder=ROOT/'antena';folder.mkdir();reference=ROOT/'referencia6';reference.mkdir()
files=['P2M21_4_elementos.aedt','4_elementos.FCStd','configuracao.json','geometria.json','HFSS_14nucleos.acf','layout.png','caminhos_alimentacao.json','sondas.py']
for f in files:shutil.copy2(SOURCE/f,folder/f)
shutil.copytree(SOURCE/'cad',folder/'cad',ignore=shutil.ignore_patterns('*.step'))
shutil.copytree(SOURCE/'P2M21_4_elementos.aedtresults',folder/'P2M21_4_elementos.aedtresults')
baseline=['P2M21_4_elementos.aedt','configuracao.json','convergencia.txt','centro.s2p','resultado.json','malha.json','polar_HV.png','diagramas_HV.png']+[m+'_'+a+'.csv' for m in ['AB','A','B'] for a in 'HV']
for f in baseline:shutil.copy2(SOURCE/f,reference/f)
evidence=reference/'metadados';evidence.mkdir()
for p in (SOURCE/'P2M21_4_elementos.aedtresults').rglob('*'):
    if p.is_file() and p.suffix in ['.EMConvData','.profile','.su']:shutil.copy2(p,evidence/p.name)
copies=[]
for p in (SOURCE/'P2M21_4_elementos.aedtresults').rglob('*'):
    if p.is_file():
        relative=p.relative_to(SOURCE);target=folder/relative
        assert sha(p)==sha(target),relative
        copies.append(dict(arquivo=relative.as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
cfg=json.loads((folder/'configuracao.json').read_text())
cfg.update(max_passes=8,min_passes=8,passes_adicionais_autorizados=2,passes_iniciais=6,variante='R12_continuacao_8_fast',sweep=True,
    sweep_config=dict(nome='Banda_Fast',tipo='Fast',inicio_GHz=5.09,fim_GHz=5.25,passo_MHz=1,pontos=161,campos_no_sweep=False),
    fonte_continuacao=str(SOURCE),diagramas_apenas_GHz=5.17)
(folder/'configuracao.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(ROOT/'origem.json').write_text(json.dumps(dict(fonte=str(SOURCE),native_sha256=sha(SOURCE/'P2M21_4_elementos.aedt'),resultado_sha256=sha(SOURCE/'resultado.json'),arquivos_resultados_copiados=copies,estado='COPIA_BYTE_A_BYTE_CONFIRMADA'),indent=2)+'\n',encoding='utf-8')
(ROOT/'qualificacao.json').write_text(json.dumps(dict(estado='COPIA_PRONTA_AGUARDA_CONFIGURACAO',max_passes_total=8,adicionais=2,nucleos=14),indent=2)+'\n',encoding='utf-8')
print('COPIA_CONFIRMADA',len(copies),sum(x['bytes'] for x in copies))
