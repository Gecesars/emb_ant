"""Conferencia independente Nexxim nos17pontos, sem solve HFSS adicional."""
import argparse,json
from pathlib import Path
import numpy as np
import skrf
from ansys.aedt.core import Circuit

parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);args=parser.parse_args()
folder=args.root/'circuito';data=folder/'componentes';manifest=json.loads((data/'manifesto.json').read_text())
project=folder/'P1H_R07_Circuito.aedt';assert not project.exists(),'Nao sobrescrever circuito ja executado'
app=Circuit(project=str(project),design='Banda17_PCBs_separadas',solution_type='NexximLNA',
            version='2024.2',new_desktop=True,non_graphical=True,close_on_exit=False)
try:
    sch=app.modeler.schematic;sch.schematic_units='meter';pins={};pin_audit={}
    positions={'L':(.03,0),'U':(.12,0),'ANT':(.21,0),'CA':(.03,-.10),'CB':(.12,-.10)}
    for tag,file in manifest['componentes'].items():
        comp=sch.create_touchstone_component(str(data/file),location=list(positions[tag]),show_bitmap=False)
        assert comp;net=skrf.Network(str(data/file));assert len(comp.pins)==net.nports and len(net.f)==17
        pin_audit[tag]=[p.name for p in comp.pins]
        for label,pin in zip(net.port_names,comp.pins):pins[tag+'/'+label.strip()]=pin
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
    setup=app.create_setup(name='Banda17',Data='LINC 5.09GHz 5.25GHz 17')
    assert setup and setup.props['SweepDefinition']['Data']=='LINC 5.09GHz 5.25GHz 17'
    app.save_project();(folder/'pinos_circuito.json').write_text(json.dumps(pin_audit,indent=2),encoding='utf8')
    assert app.analyze_setup('Banda17')
    path=folder/'nexxim.s2p'
    assert app.export_touchstone(setup='Banda17',output_file=str(path),renormalization=True,impedance=50)
    native=skrf.Network(str(path));independent=skrf.Network(str(data/'painel.s2p'))
    assert len(native.f)==17;np.testing.assert_allclose(native.f,np.arange(5090,5251,10)*1e6,atol=1,rtol=0)
    error=float(np.max(abs(native.s-independent.s)))
    np.testing.assert_allclose(native.s,independent.s,atol=2e-6,rtol=0)
    (folder/'verificacao_nexxim.json').write_text(json.dumps(dict(matriz_s_independente_conferida=True,
        erro_absoluto_max=error,frequencias_Hz=native.f.tolist(),componentes=len(manifest['componentes']),
        enlaces=len(manifest['conexoes'])+2),indent=2),encoding='utf8')
    app.save_project()
    assert app.archive_project(project_path=folder/'P1H_R07_Circuito_sem_malhas.aedtz',
        include_external_files=True,include_results_file=False,
        notes='R07:17pontos HFSS reais5090-5250MHz; PCBs separadas, cabos ideais sem perdas; sem malhas.')
    print('NEXXIM_R07_CONFERIDO',error)
finally:app.release_desktop(close_projects=True,close_desktop=True)
