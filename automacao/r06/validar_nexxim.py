"""Verificar importacao/ordem de portas e solver Nexxim com cupom HFSS conhecido."""
from pathlib import Path
import json,numpy as np,skrf
from ansys.aedt.core import Circuit

root=Path('D:/dev/EMBRAER/P1H/R06_sem_cabos/circuito_verificacao');root.mkdir(exist_ok=True)
source=Path('D:/dev/EMBRAER/P1H/R05_Correcao/cupons/Bobina_r090/cupom.s2p')
project=root/'Verificacao_Nexxim_Conexoes.aedt';assert not project.exists()
app=Circuit(project=str(project),design='Verificar_S2P',solution_type='NexximLNA',version='2024.2',
    new_desktop=True,non_graphical=True,close_on_exit=False)
try:
    sch=app.modeler.schematic;sch.schematic_units='meter'
    block=sch.create_touchstone_component(str(source),location=[0,0],show_bitmap=False)
    assert block and len(block.pins)==2
    print('PINOS',[(p.name,p.location) for p in block.pins],flush=True)
    for i in range(2):
        port=sch.create_interface_port('P'+str(i+1),location=[-.03+i*.06,.04])
        assert block.pins[i].connect_to_component(port.pins[0],page_name='E'+str(i))
    setup=app.create_setup(name='Centro',Data='5.17GHz');assert setup
    print('SETUP',setup.props,flush=True)
    app.save_project();assert app.analyze_setup('Centro')
    target=root/'nexxim.s2p'
    assert app.export_touchstone(setup='Centro',output_file=str(target),renormalization=True,impedance=50)
    source_net=skrf.Network(str(source));actual=skrf.Network(str(target))
    error=float(np.max(abs(actual.s[0]-source_net.s[8])))
    np.testing.assert_allclose(actual.s[0],source_net.s[8],atol=2e-6,rtol=0)
    (root/'verificacao.json').write_text(json.dumps(dict(pinos=[p.name for p in block.pins],erro_max=error,
        frequencias_Hz=actual.f.tolist(),status='API_PORTAS_SOLVER_CONFERIDOS'),indent=2),encoding='utf8')
    app.save_project();print('NEXXIM_OK',error,flush=True)
finally:app.release_desktop(close_projects=True,close_desktop=True)
