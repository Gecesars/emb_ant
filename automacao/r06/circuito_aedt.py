"""Reproduzir o circuito R06 no Ansys Circuit/Nexxim e comparar a matriz final."""
import argparse,json
from pathlib import Path
import numpy as np
import skrf
from ansys.aedt.core import Circuit

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);args=parser.parse_args()
folder=args.root/'circuito';data=folder/'componentes'
manifest=json.loads((data/'manifesto.json').read_text())
project=folder/'P1H_R06_Circuito.aedt'
assert not project.exists(),'Preservar o circuito ja criado; usar outra pasta para nova tentativa.'
app=Circuit(project=str(project),design='PCB_divisores_sem_perda_cabos',solution_type='NexximLNA',
            version='2024.2',new_desktop=True,non_graphical=True,close_on_exit=False)
try:
    sch=app.modeler.schematic;sch.schematic_units='meter'
    components={};pins={};pin_audit={}
    positions={'L':(.03,0),'U':(.12,0),'ANT':(.21,0),'CA':(.03,-.10),'CB':(.12,-.10)}
    for tag,file in manifest['componentes'].items():
        comp=sch.create_touchstone_component(str(data/file),location=list(positions[tag]),show_bitmap=False)
        assert comp
        net=skrf.Network(str(data/file));assert len(comp.pins)==net.nports
        pin_audit[tag]=[p.name for p in comp.pins]
        # Touchstone symbol terminal order follows the file port order.
        for label,pin in zip(net.port_names,comp.pins):pins[tag+'/'+label.strip()]=pin
        components[tag]=comp
    for i,(first,second,_,_) in enumerate(manifest['conexoes']):
        comp=sch.create_touchstone_component(str(data/('TL%02d.s2p'%i)),
            location=[.03+(i%6)*.045,-.16-(i//6)*.035],show_bitmap=False)
        assert comp and len(comp.pins)==2
        assert pins[first].connect_to_component(comp.pins[0],page_name='L%02d_A'%i)
        assert pins[second].connect_to_component(comp.pins[1],page_name='L%02d_B'%i)
    for i,first in enumerate(manifest['entradas']):
        comp=sch.create_touchstone_component(str(data/'TL_IN.s2p'),location=[.21+i*.08,-.10],show_bitmap=False)
        assert pins[first].connect_to_component(comp.pins[1],page_name='IN_'+str(i))
        port=sch.create_interface_port('N_'+('AB'[i]),location=[.21+i*.08,-.07])
        assert comp.pins[0].connect_to_component(port.pins[0],page_name='EXT_'+str(i))
    setup=app.create_setup(name='Centro',Data='5.17GHz')
    assert setup and setup.props['SweepDefinition']['Data']=='5.17GHz'
    app.save_project()
    (folder/'pinos_circuito.json').write_text(json.dumps(pin_audit,indent=2),encoding='utf8')
    assert app.analyze_setup('Centro')
    path=folder/'nexxim.s2p'
    assert app.export_touchstone(setup='Centro',output_file=str(path),renormalization=True,impedance=50)
    native=skrf.Network(str(path));independent=skrf.Network(str(data/'painel.s2p'))
    assert len(native.f)==1 and abs(native.f[0]-5.17e9)<1
    assert native.port_names is None or len(native.port_names)==2
    error=float(np.max(abs(native.s-independent.s)))
    np.testing.assert_allclose(native.s,independent.s,atol=2e-6,rtol=0)
    (folder/'verificacao_nexxim.json').write_text(json.dumps(dict(
        matriz_s_independente_conferida=True,erro_absoluto_max=error,frequencia_Hz=float(native.f[0]),
        componentes=len(manifest['componentes']),enlaces=len(manifest['conexoes'])+2),indent=2),encoding='utf8')
    app.save_project()
    assert app.archive_project(project_path=folder/'P1H_R06_Circuito_sem_malhas.aedtz',
        include_external_files=True,include_results_file=False,
        notes='R06: Touchstone completos e linhas ideais em 5.17 GHz; sem resultados de solver ou malhas.')
    print('CIRCUITO_NEXXIM_CONFERIDO',error)
finally:
    app.release_desktop(close_projects=True,close_desktop=True)
