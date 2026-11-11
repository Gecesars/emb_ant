"""Confere S8 HFSS+S6 HFSS no Nexxim, sem sweep ou novos passes FEM."""
from pathlib import Path
import json,shutil,os
import numpy as np
import skrf as rf
from ansys.aedt.core import Circuit
ROOT=Path(os.environ.get('P2S13_DIV3_ROOT','D:/dev/EMBRAER/P2S13/R08_Divisor_HFSS'));OUT=ROOT/'circuito';OUT.mkdir(exist_ok=True)
ANT=Path('D:/dev/EMBRAER/P2S13/R06_Continuacao_Tres2')
project=OUT/'P2S13_Divisor_EM_Circuito.aedt';assert not project.exists()
shutil.copy2(ROOT/'divisor_ordenado.s8p',OUT/'divisor.s8p');shutil.copy2(ANT/'centro.s6p',OUT/'antena.s6p')
app=Circuit(project=str(project),design='S8_HFSS_S6_Antena',solution_type='NexximLNA',version='2024.2',new_desktop=True,non_graphical=True,close_on_exit=False)
try:
    sch=app.modeler.schematic;sch.schematic_units='meter';pins={};audit={}
    for tag,file,xy in [('DIV','divisor.s8p',[.03,0]),('ANT','antena.s6p',[.15,0])]:
        comp=sch.create_touchstone_component(str(OUT/file),location=xy,show_bitmap=False);assert comp
        net=rf.Network(str(OUT/file));assert len(comp.pins)==net.nports;audit[tag]=[p.name for p in comp.pins]
        for name,pin in zip(net.port_names,comp.pins):pins[tag+'/'+name.strip().removesuffix(':1')]=pin
    for pol,y in [('A',.06),('B',-.06)]:
        port=sch.create_interface_port('IN_'+pol,location=[0,y]);assert port
        assert pins['DIV/IN_'+pol].connect_to_component(port.pins[0],page_name='EXT_'+pol)
        for i in range(1,4):
            n='R%d_%s'%(i,pol);assert pins['DIV/'+n].connect_to_component(pins['ANT/'+n],page_name=n)
    setup=app.create_setup(name='Centro',Data='5.17GHz');assert setup
    app.save_project();assert app.analyze_setup('Centro')
    path=OUT/'nexxim.s2p';assert app.export_touchstone(setup='Centro',output_file=str(path),renormalization=True,impedance=50)
    n=rf.Network(str(path));ref=rf.Network(str(ROOT/'conjunto.s2p'));assert len(n.f)==1 and n.f[0]==5.17e9
    error=float(np.max(abs(n.s-ref.s)));np.testing.assert_allclose(n.s,ref.s,atol=2e-6,rtol=0)
    (OUT/'verificacao_nexxim.json').write_text(json.dumps(dict(erro_absoluto_max=error,matriz_conferida=True,pinos=audit,frequencia_Hz=5.17e9),indent=2)+'\n')
    app.save_project();assert app.archive_project(project_path=OUT/'P2S13_Divisor_EM_sem_malhas.aedtz',include_external_files=True,include_results_file=False,notes='S8 HFSS divisor duplo1:3 + S6 antena,5.17GHz. Sem malhas; limites de convergencia no relatorio.')
    print('NEXXIM_CONFERIDO',error)
finally:app.release_desktop(close_projects=True,close_desktop=True)
