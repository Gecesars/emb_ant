"""Pos-processa campos radiados existentes, sem novo solve e sem salvar o nativo."""
from pathlib import Path
import os, json, hashlib
import numpy as np
import skrf as rf
from ansys.aedt.core import Hfss
ROOT=Path(os.environ['P2S13_DIV3_ROOT'])
native=ROOT/'Divisor_Duplo3.aedt'
sha=hashlib.sha256(native.read_bytes()).hexdigest()
sd=rf.Network(str(ROOT/'divisor_ordenado.s8p')).s[0]
sa=rf.Network('D:/dev/EMBRAER/P2S13/R06_Continuacao_Tres2/centro.s6p').s[0]
ai=np.ones(2)/np.sqrt(2)
a=np.linalg.solve(np.eye(6)-sd[2:,2:]@sa,sd[2:,:2]@ai)
incident=np.r_[ai,sa@a]
ports=['IN_A','IN_B','R1_A','R1_B','R2_A','R2_B','R3_A','R3_B']
expected=float(np.sum(abs(incident)**2)-np.sum(abs(sd@incident)**2))
app=Hfss(project=str(native),design='Duplo1x3_Planar',version='2024.2',new_desktop=True,non_graphical=True,close_on_exit=False)
try:
    assert app.insert_infinite_sphere(name='DiagnosticoRadiacao',theta_start=0,theta_stop=180,theta_step=2,phi_start=0,phi_stop=360,phi_step=2)
    assert app.edit_sources({p+':1':('%.16gW'%abs(v)**2,'%.16gdeg'%np.angle(v,deg=True)) for p,v in zip(ports,incident)},include_port_post_processing=False)
    quantities=app.post.available_report_quantities(report_category='Antenna Parameters',solution='Centro : LastAdaptive',context='DiagnosticoRadiacao')
    (ROOT/'quantidades_perdas.json').write_text(json.dumps(quantities,indent=2))
    expr=[q for q in ['RadiatedPower','AcceptedPower','IncidentPower','RadiationEfficiency','SystemEfficiency'] if q in quantities]
    assert 'RadiatedPower' in expr,quantities
    data=app.oreportsetup.GetSolutionDataPerVariation('Antenna Parameters','Centro : LastAdaptive',
        ['Context:=','DiagnosticoRadiacao'],['Freq:=',['All']],expr)
    assert data
    values={e:dict(real=list(data[0].GetRealDataValues(e)),units=data[0].GetDataUnits(e)) for e in expr}
    result=dict(fontes_carregadas=[dict(porta=p,potencia_W=float(abs(v)**2),fase_graus=float(np.angle(v,deg=True))) for p,v in zip(ports,incident)],
        perda_total_S8_W=expected,quantidades=values,novo_solve=False,nativo_sha256=sha)
    (ROOT/'diagnostico_perdas.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
finally:
    app.close_project(save=False)
    app.release_desktop(close_projects=False,close_desktop=True)
    assert hashlib.sha256(native.read_bytes()).hexdigest()==sha
