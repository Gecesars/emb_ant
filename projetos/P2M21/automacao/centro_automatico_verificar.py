"""Verificar setup sem pre-refinamento e resultados apenas em 5,17 GHz."""
import os,sys,json,re,hashlib,csv
from pathlib import Path
root=Path(os.environ.get('P2M21_UNIFORME','D:/dev/EMBRAER/P2M21/R04_Centro_Classic'))
os.environ['P2M21_UNIFORME']=str(root)
import uniforme_verificar as common

def prepare():
    cfg=common.read(root/'configuracao.json');path=root/'antena'/cfg['native']
    source=Path(cfg['fonte']);text=path.read_text(errors='replace')
    assert common.sha(source)==cfg['fonte_sha256']
    assert common.geometry(text)==common.geometry(source.read_text(errors='replace'))
    analysis=text.split("$begin 'AnalysisSetup'",1)[1].split("$end 'AnalysisSetup'",1)[0]
    transition=root/'transicao_4passes/P2M21_Ganho_Diagrama_antes_retomada.aedt'
    if transition.exists():
        old=transition.read_text(errors='replace').split("$begin 'AnalysisSetup'",1)[1].split("$end 'AnalysisSetup'",1)[0]
        assert old.replace('MaximumPasses=6','MaximumPasses=4')==analysis,'Alteracao alem do limite de passes no AnalysisSetup.'
    for term in ['MaxDeltaS=0.04','MaximumPasses=%d'%cfg['max_passes'],'MinimumConvergedPasses=2','BasisOrder=-1','DoLambdaRefine=false',"Frequency='5.17GHz'",'ImportMesh=false']:
        assert term in analysis,term
    assert "$begin 'Banda17'" not in analysis and 'RangeStart=' not in analysis
    operations=text.split("$begin 'MeshOperations'",1)[1].split("$end 'MeshOperations'",1)[0]
    assert '$begin' not in operations,operations
    settings=text.split("$begin 'MeshSettings'",1)[1].split("$end 'MeshSettings'",1)[0]
    assert "MeshMethod='AnsoftClassic'" in settings
    assert 'UseAlternativeMeshMethodsAsFallBack=false' in settings
    assert 'UseAutoLength=true' in settings and 'SliderMeshSettings=5' in settings
    assert text.count("Magnitude='0.015625W'")==64
    info=common.read(root/'antena/preparacao.json');assert info['validacao']==1 and not info['erros'] and not info['sweeps']
    data=dict(geometria_preservada=True,blocos_geometria=len(common.geometry(text)),max_passes=cfg['max_passes'],
      delta_s=.04,basis_order=-1,lambda_refine=False,mesher='AnsoftClassic',operacoes_locais=0,sweeps=0,frequencia_GHz=5.17,
      potencia_incidente_total_W=1,portas=64,native_sha256=common.sha(path),fonte_sha256=common.sha(source))
    common.write(root/'antena/verificacao_preparacao.json',data);print(json.dumps(data))

def plot():
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    data=common.read(root/'antena/auditoria_centro.json');row=data['pontos'][0]
    fig,axs=plt.subplots(1,2,figsize=(12,4.5))
    for ax,axis,window in zip(axs,'HV',[(-90,90),(-10,10)]):
        with (root/'antena/centro/5170'/('Uniforme_'+axis+'.csv')).open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
        theta=np.array([float(r['Theta [deg]']) for r in rows]);gain=np.array([float(r['dB(RealizedGainTotal) []']) for r in rows])
        front=abs(theta)<=90;peak=float(gain[front].max());ax.plot(theta,gain-peak)
        ax.axhline(-3,color='#a63c27',ls=':');ax.set(xlim=window,ylim=(-30,1),xlabel='Angulo (graus)',ylabel='Nivel relativo (dB)',title=f'{axis}: {row["abertura_"+axis+"_graus"]:.2f} graus');ax.grid(alpha=.3)
    label='AUDITADO' if data['aprovado'] else 'PRELIMINAR / NAO QUALIFICADO'
    conv=data['convergencia']
    fig.suptitle(f'P2M21 16 x 2 — 5,17 GHz — ganho frontal {row["ganho_frontal_total_realizado_dBi"]:.2f} dBi\n{conv["passes"]} passes; Delta S = {conv["delta_s"]:.6f} — {label}')
    fig.tight_layout();fig.savefig(root/'diagramas_5170MHz.png',dpi=180);plt.close(fig)

if __name__=='__main__':
    stage=sys.argv[1]
    if stage=='preparacao':prepare()
    elif stage=='centro':
        try:common.check('centro')
        finally:
            if (root/'antena/auditoria_centro.json').exists():plot()
    else:raise ValueError('Somente preparacao ou centro; nenhum sweep autorizado.')
