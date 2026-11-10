"""Um unico passe adicional, do quinto ao sexto total, preservando a malha."""
from pathlib import Path
import argparse,json,hashlib,shutil,re
from quatro_8fast_auditar import block,geometry,history

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def snapshot(f):
    ref=f/'passe5';assert not ref.exists() and not (f/'P2M21_4_elementos.aedt.lock').exists()
    r=json.loads((f/'resultado.json').read_text());assert r['passes']==5 and r['convergiu'] and r['fisica_ok']
    assert not (f/'triagem3.s2p').exists() and not (f/'banda_fast.s2p').exists()
    ref.mkdir();files=['P2M21_4_elementos.aedt','configuracao.json','convergencia.txt','centro.s2p','resultado.json','malha.json','qualificacao.json','diagrama_comparado.json','comparacao_diagramas.png','polar_HV.png','polar_HV.pdf','diagramas_HV.png']+[m+'_'+a+'.csv' for m in ['AB','A','B'] for a in 'HV']
    for n in files:shutil.copy2(f/n,ref/n)
    cache=[dict(arquivo=p.relative_to(f).as_posix(),sha256=sha(p)) for p in f.rglob('*') if p.is_file() and p.name in ['native.adp','current.ngmesh']]
    assert len(cache)==2,cache
    meta=ref/'metadados';meta.mkdir()
    for p in f.rglob('*.EMConvData'):
        if ref not in p.parents:shutil.copy2(p,meta/(p.name+'.txt'))
    write(f/'sexto_origem.json',dict(passes_iniciais=5,max_passes_total=6,cache=cache,arquivos=[dict(nome=n,sha256=sha(ref/n)) for n in files]))
    cfg=json.loads((f/'configuracao.json').read_text());cfg.update(min_passes=6,max_passes=6,passes_iniciais=5,confirmacao_adicional=1);write(f/'configuracao.json',cfg)
    prepare='''# -*- coding: utf-8 -*-
import os,re,json
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=%r
p=oDesktop.OpenProject(os.path.join(root,'P2M21_4_elementos.aedt'));d=p.SetActiveDesign('Quatro_elementos');an=d.GetModule('AnalysisSetup')
assert not list(an.GetSweeps('Centro'))
d.ExportConvergence('Centro','',os.path.join(root,'antes_sexto_convergencia.txt'))
with open(os.path.join(root,'P2M21_4_elementos.aedt')) as stream:raw=stream.read()
assert 'MaximumPasses=6' in raw and 'MinimumPasses=2' in raw
an.EditSetup('Centro',['NAME:Centro','MinimumPasses:=',6,'Target:=',0.3333])
p.SaveAs(os.path.join(root,'P2M21_4_elementos.aedt'),True);oDesktop.CloseProject(p.GetName())
'''%f.as_posix()
    (f/'sexto_preparar.py').write_text(prepare,encoding='utf-8')
    code=(f/'resolver.py').read_text(encoding='utf-8')
    code=code.replace('    raw=open(native).read()','    with open(native) as stream:raw=stream.read()')
    guard="assert not os.path.exists(os.path.join(root,'convergencia.txt')),'Resultado ja existe; nao duplicar solve.'"
    assert guard in code
    code=code.replace(guard,"assert json.load(open(os.path.join(root,'sexto_preparacao_auditada.json')))['aprovado'];assert not os.path.exists(os.path.join(root,'sexto_executado.json'))")
    code=code.replace("['MaximumPasses=6','MaxDeltaS=0.05'","['MaximumPasses=6','MinimumPasses=6','MaxDeltaS=0.05'")
    code=code.replace("            reports.CreateReport(name,","            if name in list(reports.GetAllReportNames()):reports.DeleteReports([name])\n            reports.CreateReport(name,")
    code=code.replace("    d.Analyze('Centro')","    write('sexto_executado.json',dict(estado='RETOMADA_SOMENTE_PASSE6',max_passes_total=6));d.Analyze('Centro')")
    code=code.replace('SOLVE_INICIADO_4_ELEMENTOS_5170MHz_14NUCLEOS_MAX6','RETOMADA_PASSE6_DE_6_14NUCLEOS')
    (f/'sexto_resolver.py').write_text(code,encoding='utf-8')
    print('SNAPSHOT_PASSE5_PRESERVADO')

def audit_prepare(f):
    a=(f/'passe5/P2M21_4_elementos.aedt').read_text(errors='replace');b=(f/'P2M21_4_elementos.aedt').read_text(errors='replace')
    assert geometry(a)==geometry(b) and geometry(a)
    for n in ['BoundarySetup','MaterialDef','MeshSetup']:
        present=("$begin '"+n+"'") in a
        assert present==(("$begin '"+n+"'") in b),n
        if present:assert block(a,n)==block(b,n),n
    before=block(a,'AnalysisSetup');after=block(b,'AnalysisSetup');expected=before.replace('MinimumPasses=2','MinimumPasses=6')
    inactive={}
    if expected!=after:
        for text in (before,after):
            assert all(flag in text for flag in ['DoLambdaRefine=false','SetLambdaTarget=false','SetPortMinMaxTri=false'])
        normalized=expected
        for old,new in [('Target=0.3333','Target=0.6667'),('PortMinTri=100','PortMinTri=60'),('PortMaxTri=500','PortMaxTri=300')]:
            if old in expected and new in after:normalized=normalized.replace(old,new);inactive[old]=new
        assert normalized==after
    for item in json.loads((f/'sexto_origem.json').read_text())['cache']:assert sha(f/item['arquivo'])==item['sha256']
    assert history(f/'passe5/convergencia.txt')==history(f/'antes_sexto_convergencia.txt')
    write(f/'sexto_preparacao_auditada.json',dict(aprovado=True,geometria_inalterada=True,malha_byte_a_byte_preservada=True,alteracao_ativa='MinimumPasses2->6; MaximumPasses6 mantido',defaults_inativos_normalizados=inactive,lambda_e_restricoes_de_triangulos_de_porta_desativados=True,primeiros_cinco_preservados=True))
    print('RETOMADA_AUDITADA_MAXIMO_SEIS_TOTAL')

def audit_end(f):
    import numpy as np
    old=history(f/'passe5/convergencia.txt');new=history(f/'convergencia.txt');assert len(old)==5 and len(new)==6 and new[:5]==old,(old,new)
    a=json.loads((f/'passe5/resultado.json').read_text());b=json.loads((f/'resultado.json').read_text());assert b['passes']==6
    delta=dict(ganho_dB=b['cortes']['H']['ganho_frontal_dBi']-a['cortes']['H']['ganho_frontal_dBi'],abertura_H_graus=b['cortes']['H']['abertura_graus']-a['cortes']['H']['abertura_graus'],abertura_V_graus=b['cortes']['V']['abertura_graus']-a['cortes']['V']['abertura_graus'],VSWR_ativo=(np.array(b['VSWR_ativo'])-a['VSWR_ativo']).tolist(),VSWR_casado=(np.array(b['VSWR_casado'])-a['VSWR_casado']).tolist())
    write(f/'sexto_continuidade_auditada.json',dict(aprovado=True,primeiros_cinco_identicos=True,apenas_passe_adicional6=True,historico=new,convergiu=b['convergiu'],comparacao5_6=delta,nota='Aprovado refere-se a continuidade. Metas RF e diagramas possuem verificacoes separadas.'))
    print('CONTINUIDADE_SEIS',json.dumps(delta))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('etapa',choices=['snapshot','preparacao','fim']);p.add_argument('pasta');a=p.parse_args();{'snapshot':snapshot,'preparacao':audit_prepare,'fim':audit_end}[a.etapa](Path(a.pasta))
