"""Circuito Nexxim real: S8 do divisor, seis linhas coaxiais e S6 da antena."""
from pathlib import Path
import json,sys
import numpy as np
import skrf as rf
from ansys.aedt.core import Circuit
ROOT=Path('D:/dev/EMBRAER/P2S13/R14_Compacto_Simetrico_SemRadome/c00');OUT=ROOT/'circuito'
project=OUT/'C09_Antena_Nexxim.aedt';assert not project.exists(),'Preservar circuito existente'
result=json.loads((OUT/'resultado.json').read_text());assert result['potencia']['balanco_aprovado']
app=Circuit(project=str(project),design='C09_6Coax_Antena',solution_type='NexximLNA',version='2024.2',new_desktop=True,non_graphical=True,close_on_exit=False)
try:
    sch=app.modeler.schematic;sch.schematic_units='meter';pins={};audit={};sources={}
    for tag,file,xy in [('DIV','divisor.s8p',[.025,0]),('ANT','antena.s6p',[.19,0])]:
        comp=sch.create_touchstone_component(str(OUT/file),location=xy,show_bitmap=False);assert comp
        net=rf.Network(str(OUT/file));assert len(comp.pins)==net.nports;audit[tag]=[p.name for p in comp.pins]
        for name,pin in zip(net.port_names,comp.pins):pins[tag+'/'+name.strip().removesuffix(':1')]=pin
    for i,name in enumerate(['R1_A','R1_B','R2_A','R2_B','R3_A','R3_B']):
        comp=sch.create_touchstone_component(str(OUT/'coaxial.s2p'),location=[.105,.085-i*.034],show_bitmap=False);assert comp
        assert pins['DIV/'+name].connect_to_component(comp.pins[0],page_name='DIV_'+name)
        assert pins['ANT/'+name].connect_to_component(comp.pins[1],page_name='ANT_'+name)
    for pol,y in [('A',.04),('B',-.04)]:
        port=sch.create_interface_port('IN_'+pol,location=[-.03,y]);assert port
        assert pins['DIV/IN_'+pol].connect_to_component(port.pins[0],page_name='ENTRADA_'+pol)
        source=app.assign_power_sinusoidal_excitation_to_ports(['IN_'+pol]);assert source
        source.power_magnitude='0.5W';source.frequency='5.17GHz';source.phase_delay='0deg';source.ac_phase='0deg'
        source.ac_magnitude='14.142135623731V'
        sources[pol]=dict(name=source.name,available_power=source.power_magnitude,phase=source.phase_delay,frequency=source.frequency,
            ac_magnitude=source.ac_magnitude,nota='Normalizacao de ondas de potencia para ganho usa1Wtotal; matrizS independe da amplitude AC.')
    setup=app.create_setup(name='Centro',Data='5.17GHz');assert setup and setup.props['SweepDefinition']['Data']=='5.17GHz'
    app.save_project();assert app.analyze_setup('Centro')
    path=OUT/'nexxim.s2p';assert app.export_touchstone(setup='Centro',output_file=str(path),renormalization=True,impedance=50)
    native=rf.Network(str(path));ref=rf.Network(str(OUT/'conjunto.s2p'));assert len(native.f)==1 and native.f[0]==5.17e9
    err=float(np.max(abs(native.s-ref.s)));np.testing.assert_allclose(native.s,ref.s,atol=2e-6,rtol=0)
    s=native.s[0];g=s@np.ones(2);vs=((1+abs(g))/(1-abs(g))).tolist();matched=((1+abs(np.diag(s)))/(1-abs(np.diag(s)))).tolist()
    proof=dict(matriz_conferida=True,erro_absoluto_max=err,frequencia_Hz=float(native.f[0]),VSWR_ativo=vs,VSWR_outra_casada=matched,
       entradas=sources,pinos=audit,blocos_touchstone=8,cabos_em_HFSS=False,modelo='HFSS S8 + 6xRLGC coaxial + HFSS S6',
       ganho_e_diagramas='Recompostos dos campos complexos por porta da antena com ondas do circuito, conferido contra S2 Nexxim.')
    (OUT/'verificacao_nexxim.json').write_text(json.dumps(proof,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    result.update(nexxim_pendente=False,erro_Nexxim=err,qualificado=bool(result['metas_numericas_atendidas'] and all(x['convergiu'] for x in result['convergencia'].values()) and result['campos_monitorados']['estabilidade_observada']))
    (OUT/'resultado.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    app.save_project();assert app.archive_project(project_path=OUT/'C09_Antena_Nexxim_sem_malhas.aedtz',include_external_files=True,include_results_file=False,
        notes='C09 compacto, duas secoes identicas por ramal; seis cabos iguais apenas no circuito; antena sem radome;5.17GHz. Ver auditorias e limites no relatorio.')
    print('NEXXIM_CONFERIDO',err,'VSWR',vs)
finally:
    app.release_desktop(close_projects=True,close_desktop=True)
