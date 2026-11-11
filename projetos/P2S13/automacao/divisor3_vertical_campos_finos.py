"""Reexporta campos existentes da antena em grade0.01grau; nao executa Analyze."""
from pathlib import Path
import json,hashlib
from ansys.aedt.core import Hfss
ANT=Path('D:/dev/EMBRAER/P2S13/R06_Continuacao_Tres2')
OUT=Path('D:/dev/EMBRAER/P2S13/R09_Correcao_Divisor/antena_grade_fina')
OUT.mkdir(exist_ok=True)
native=ANT/'P2S13_TresPCB2.aedt';sha=hashlib.sha256(native.read_bytes()).hexdigest()
cfg=json.loads((ANT/'configuracao.json').read_text());ports=[p['name'] for p in cfg['portas']]
app=Hfss(project=str(native),design=cfg['design'],version='2024.2',new_desktop=True,non_graphical=True,close_on_exit=False)
try:
    assert app.insert_infinite_sphere(name='VerticalFino',theta_start=-2,theta_stop=2,theta_step=.01,phi_start=0,phi_stop=0,phi_step=1)
    reports=app.oreportsetup
    for name,chosen in [('ALL',ports)]+[(p,[p]) for p in ports]:
        assert app.edit_sources({p+':1':('%.16gW'%(1./len(chosen)) if p in chosen else '0W','0deg') for p in ports},include_port_post_processing=False)
        report='Fino_'+name
        reports.CreateReport(report,'Far Fields','Rectangular Plot','Centro : LastAdaptive',['Context:=','VerticalFino'],
            ['Theta:=',['All'],'Phi:=',['0deg'],'Freq:=',['5170MHz']],
            ['X Component:=','Theta','Y Component:=',['dB(RealizedGainTotal)','re(rETheta)','im(rETheta)','re(rEPhi)','im(rEPhi)']])
        reports.ExportToFile(report,str(OUT/(name+'_V.csv')),False)
    (OUT/'origem.json').write_text(json.dumps(dict(native=str(native),native_sha256=sha,
        S6_sha256=hashlib.sha256((ANT/'centro.s6p').read_bytes()).hexdigest(),frequencia_GHz=5.17,
        novo_solve=False,theta_inicio=-2,theta_fim=2,theta_passo=.01,phi=0),indent=2))
finally:
    app.close_project(save=False)
    app.release_desktop(close_projects=False,close_desktop=True)
    assert hashlib.sha256(native.read_bytes()).hexdigest()==sha
