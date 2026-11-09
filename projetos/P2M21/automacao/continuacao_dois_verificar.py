"""Auditoria da continuacao solicitada, sem novo solve ou alteracao de malha."""
import os,sys,json
from pathlib import Path
root=Path(os.environ['P2M21_UNIFORME'])
import uniforme_verificar as u

def prepare():
    cfg=u.read(root/'configuracao.json');p=root/'antena'/cfg['native']
    before=(root/'resultado_4_passes'/cfg['native']).read_text(errors='replace');after=p.read_text(errors='replace')
    def setup(t):return t.split("$begin 'AnalysisSetup'",1)[1].split("$end 'AnalysisSetup'",1)[0]
    assert setup(before).replace('MaximumPasses=4','MaximumPasses=6').replace('MinimumPasses=2','MinimumPasses=6')==setup(after)
    assert u.geometry(before)==u.geometry(after)
    assert after.count("Magnitude='0.015625W'")==64 and 'DoLambdaRefine=false' in setup(after)
    assert "$begin 'Banda17'" not in setup(after)
    old=u.read(root/'resultado_4_passes/auditoria_centro.json');assert old['convergencia']['passes']==4
    data=dict(max_passes=6,min_passes=6,dois_passes_adicionais=True,geometria_preservada=True,
      alteracoes_apenas_min_max_passes=True,native_sha256=u.sha(p),referencia_quatro_sha256=u.sha(root/'resultado_4_passes'/cfg['native']))
    u.write(root/'verificacao_continuacao.json',data);print(json.dumps(data))

if __name__=='__main__':
    if sys.argv[1]=='preparacao':prepare()
    else:
        u.check('centro')
        audit=u.read(root/'antena/auditoria_centro.json');assert audit['convergencia']['passes']==6
        history=u.read(root/'antena/historico_centro.json')['historico']
        old=u.read(root/'resultado_4_passes/historico_centro.json')['historico']
        assert [(x['passe'],x['tetraedros'],x['delta_s']) for x in history[:4]]==[(x['passe'],x['tetraedros'],x['delta_s']) for x in old]
        print('SEIS_PASSES_COM_QUATRO_PRESERVADOS')
