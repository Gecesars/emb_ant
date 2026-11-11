"""Confere a rede proposta carregada pelo S6 real no Nexxim, somente5.17GHz."""
from pathlib import Path
import json,shutil
import numpy as np
import skrf as rf
from ansys.aedt.core import Circuit

ROOT=Path('D:/dev/EMBRAER/P2S13/R07_Divisor_Duplo3')
SOURCE=Path('D:/dev/EMBRAER/P2S13/R06_Continuacao_Tres2')
OUT=ROOT/'circuito';OUT.mkdir(exist_ok=True)
project=OUT/'P2S13_Divisor_Duplo3.aedt'
assert not project.exists(),'Circuito ja criado; nao sobrescrever nem resolver em duplicidade.'
shutil.copy2(ROOT/'Wilkinson_ajustado_1x3.s4p',OUT/'Wilkinson_ajustado_1x3.s4p')
shutil.copy2(SOURCE/'centro.s6p',OUT/'antena.s6p')
app=Circuit(project=str(project),design='Duplo1x3_Carregado',solution_type='NexximLNA',
    version='2024.2',new_desktop=True,non_graphical=True,close_on_exit=False)
try:
    sch=app.modeler.schematic;sch.schematic_units='meter';comps={};pins={};audit={}
    for tag,file,xy in [('DA','Wilkinson_ajustado_1x3.s4p',[.02,.04]),
                        ('DB','Wilkinson_ajustado_1x3.s4p',[.02,-.04]),
                        ('ANT','antena.s6p',[.14,0])]:
        comp=sch.create_touchstone_component(str(OUT/file),location=xy,show_bitmap=False);assert comp
        net=rf.Network(str(OUT/file));assert len(comp.pins)==net.nports
        comps[tag]=comp;audit[tag]=[p.name for p in comp.pins]
        for label,pin in zip(net.port_names,comp.pins):pins[tag+'/'+label.strip().removesuffix(':1')]=pin
    for pol,y in [('A',.07),('B',-.07)]:
        port=sch.create_interface_port('IN_'+pol,location=[0,y]);assert port
        assert pins['D'+pol+'/IN'].connect_to_component(port.pins[0],page_name='EXT_'+pol)
        for i in range(1,4):
            assert pins['D'+pol+'/R'+str(i)].connect_to_component(pins['ANT/R'+str(i)+'_'+pol],page_name='R'+str(i)+'_'+pol)
    setup=app.create_setup(name='Centro',Data='5.17GHz')
    assert setup and setup.props['SweepDefinition']['Data']=='5.17GHz'
    app.save_project();assert app.analyze_setup('Centro')
    path=OUT/'nexxim.s2p';assert app.export_touchstone(setup='Centro',output_file=str(path),renormalization=True,impedance=50)
    n=rf.Network(str(path));ref=rf.Network(str(ROOT/'Wilkinson_ajustado_conjunto.s2p'))
    assert len(n.f)==1 and n.f[0]==5.17e9
    err=float(np.max(abs(n.s-ref.s)));np.testing.assert_allclose(n.s,ref.s,atol=2e-6,rtol=0)
    (OUT/'verificacao_nexxim.json').write_text(json.dumps(dict(erro_absoluto_max=err,
        matriz_conferida=True,pinos=audit,frequencia_Hz=5.17e9,
        nota='Verifica interconexao S4+S4+S6; nao valida o modelo fisico do divisor ou a malha da antena.'),indent=2)+'\n')
    app.save_project()
    assert app.archive_project(project_path=OUT/'P2S13_Divisor_Duplo3_sem_malhas.aedtz',
        include_external_files=True,include_results_file=False,
        notes='Plano preliminar: S4 microstrip analitico e S6 HFSS8passes. Somente5.17GHz; sem malhas.')
    print('NEXXIM_CONFERIDO',err)
finally:
    app.release_desktop(close_projects=True,close_desktop=True)
