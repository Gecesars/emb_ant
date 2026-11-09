"""Ensaio central simplificado em uma instancia GUI ja aberta do AEDT 2024 R2."""
import argparse
import hashlib
import json
import shutil
import traceback
from datetime import datetime
from pathlib import Path

import pythoncom
import win32com.client

ROOT = Path('D:/dev/EMBRAER/P2M21/R08_Dois_Verticais_Sem_Suportes')
SOURCE = Path('D:/dev/EMBRAER/P2M21/R07_Dois_Verticais_GUI/d48p0/Dois_Verticais_d48p0.aedt')
NATIVE = ROOT / 'Dois_Verticais_48mm_Sem_Suportes.aedt'
PROJECT = NATIVE.stem
ACF = SOURCE.parent.parent / 'HFSS_14nucleos.acf'


def write(name, data):
    (ROOT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def log(message):
    line = datetime.now().astimezone().isoformat() + ' ' + message
    print(line, flush=True)
    with (ROOT / 'execucao.log').open('a', encoding='utf-8') as handle:
        handle.write(line + '\n')


def attach(pid):
    rot = pythoncom.GetRunningObjectTable()
    ctx = pythoncom.CreateBindCtx(0)
    target = 'ElectronicsDesktop.2024.2.0:%d' % pid
    moniker = next(m for m in rot.EnumRunning() if m.GetDisplayName(ctx, None) == target)
    return win32com.client.Dispatch(rot.GetObject(moniker).QueryInterface(pythoncom.IID_IDispatch))


def sources(sol, active=None):
    ports = list(sol.GetAllSources())
    assert sorted(ports) == ['A', 'B'], ports
    sol.EditSources([['IncludePortPostProcessing:=', False, 'SpecifySystemPower:=', False]] + [
        ['Name:=', s + ':1', 'Magnitude:=', ('0.5W' if active is None else '1W' if s == active else '0W'),
         'Phase:=', '0deg'] for s in ports])


def prepare(desktop, pid):
    assert not ROOT.exists(), 'Pasta existente; examinar antes de preparar novamente.'
    ROOT.mkdir(parents=True)
    shutil.copy2(SOURCE, NATIVE)
    shutil.copy2(ACF, ROOT / ACF.name)
    write('configuracao.json', dict(
        native=NATIVE.name, fonte=str(SOURCE), fonte_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        espacamento_vertical_mm=48, radiadores=2, colunas=1, divisoes_impressas_1x2=2,
        cabos=2, comprimento_cabo_mm=50, cabos_fisicos_com_perdas=True,
        apoios_plasticos=False, frequencia_GHz=5.17, max_passes=6, max_delta_s=.04,
        nucleos=14, gui=True, aedt_pid=pid, sweep=False,
        potencia_por_porta_W=.5, fase_graus=0,
        malha='Classic automatica, sem refinamento local nem LambdaRefine; adaptacao20% durante solve.',
        escolha='Variante48mm era a ultima em calculo antes do encerramento anterior. Nao implica espacamento otimo.',
        escopo='Remove somente Apoio_POM_0/1; preserva PCB, metal, refletor, soldas e PTFE dos cabos.',
        grafica='Instancia existente; renderizacao da GUI por CPU nao foi configurada nem comprovada.'))
    desktop.RestoreWindow()
    p = desktop.OpenProject(str(NATIVE))
    d = p.SetActiveDesign('PCB_separada')
    e = d.SetActiveEditor('3D Modeler')
    before = set(e.GetObjectsInGroup('Solids'))
    removed = ['Apoio_POM_0', 'Apoio_POM_1']
    assert set(removed) <= before, before
    materials = {n: e.GetPropertyValue('Geometry3DAttributeTab', n, 'Material') for n in removed}
    assert all('pom' in str(v).lower() for v in materials.values()), materials
    e.Delete(['NAME:Selections', 'Selections:=', ','.join(removed)])
    after = set(e.GetObjectsInGroup('Solids'))
    assert before - after == set(removed) and not after - before
    setup = d.GetModule('AnalysisSetup')
    setup.EditSetup('Centro', ['NAME:Centro', 'MaximumPasses:=', 6])
    assert not list(setup.GetSweeps('Centro'))
    sources(d.GetModule('Solutions'))
    desktop.SetRegistryFromFile(str(ROOT / ACF.name))
    desktop.SetRegistryString('Desktop/ActiveDSOConfigurations/HFSS', 'P2M21_14nucleos')
    assert desktop.GetRegistryString('Desktop/ActiveDSOConfigurations/HFSS') == 'P2M21_14nucleos'
    validation = d.ValidateDesign()
    errors = list(desktop.GetMessages(p.GetName(), d.GetName(), 2))
    assert validation == 1 and not errors, (validation, errors)
    p.Save()
    # Close/reopen only this copied project to verify the saved setup, not another session.
    desktop.CloseProject(p.GetName())
    text = NATIVE.read_text(errors='replace')
    analysis = text.split("$begin 'AnalysisSetup'", 1)[1].split("$end 'AnalysisSetup'", 1)[0]
    assert 'MaximumPasses=6' in analysis and 'MaxDeltaS=0.04' in analysis
    assert 'DoLambdaRefine=false' in analysis and '5.17GHz' in analysis
    assert 'AnsoftClassic' in text
    assert all("Name='%s'" % n not in text for n in removed)
    write('preparacao.json', dict(validacao=validation, erros=errors, removidos=materials,
        solidos_antes=len(before), solidos_depois=len(after), restantes=sorted(after),
        max_passes=6, delta_s=.04, nucleos=14, gui_pid=pid,
        fonte_preservada=hashlib.sha256(SOURCE.read_bytes()).hexdigest() == json.loads((ROOT/'configuracao.json').read_text(encoding='utf-8'))['fonte_sha256']))
    p = desktop.OpenProject(str(NATIVE))
    d = p.SetActiveDesign('PCB_separada')
    d.SetActiveEditor('3D Modeler').FitAll()
    write('qualificacao.json', dict(estado='PREPARADO_GUI_ABERTA', pid=pid, max_passes=6))
    log('PREPARADO_SEM_SUPORTES_6PASSES_GUI_EXISTENTE')


def solve(desktop, pid):
    state = json.loads((ROOT/'qualificacao.json').read_text(encoding='utf-8'))
    assert state['estado'] == 'PREPARADO_GUI_ABERTA', state
    p = desktop.SetActiveProject(PROJECT)
    d = p.SetActiveDesign('PCB_separada')
    setup = d.GetModule('AnalysisSetup')
    assert not list(setup.GetSweeps('Centro'))
    assert not any(n.startswith('Apoio_POM') for n in d.SetActiveEditor('3D Modeler').GetObjectsInGroup('Solids'))
    desktop.SetRegistryFromFile(str(ROOT/ACF.name))
    desktop.SetRegistryString('Desktop/ActiveDSOConfigurations/HFSS', 'P2M21_14nucleos')
    sol = d.GetModule('Solutions')
    sources(sol)
    p.Save()
    write('qualificacao.json', dict(estado='EM_CALCULO_GUI', pid=pid, inicio=datetime.now().astimezone().isoformat()))
    log('SOLVE_INICIADO_5170MHz_14NUCLEOS_MAX6')
    d.Analyze('Centro')
    d.ExportConvergence('Centro', '', str(ROOT/'convergencia.txt'))
    messages = list(desktop.GetMessages(p.GetName(), d.GetName(), 0))
    errors = list(desktop.GetMessages(p.GetName(), d.GetName(), 2))
    write('mensagens.json', messages)
    assert not errors, errors
    sol.ExportNetworkData('', ['Centro : LastAdaptive'], 3, str(ROOT/'centro.s2p'), ['All'], True, 50, 'S', -1, 1, 15, False, True, False)
    reports = d.GetModule('ReportSetup')
    for mode, active in [('AB', None), ('A', 'A'), ('B', 'B')]:
        sources(sol, active)
        for axis, phi in [('H', 90), ('V', 0)]:
            name = mode+'_'+axis
            reports.CreateReport(name, 'Far Fields', 'Rectangular Plot', 'Centro : LastAdaptive', ['Context:=', 'HV'],
                ['Theta:=', ['All'], 'Phi:=', [str(phi)+'deg'], 'Freq:=', ['5170MHz']],
                ['X Component:=', 'Theta', 'Y Component:=', ['dB(RealizedGainTotal)', 'dB(GainTotal)', 'dB(DirTotal)',
                 're(rETheta)', 'im(rETheta)', 're(rEPhi)', 'im(rEPhi)']])
            reports.ExportToFile(name, str(ROOT/(name+'.csv')), False)
    sources(sol)
    p.Save()
    d.SetActiveEditor('3D Modeler').FitAll()
    write('qualificacao.json', dict(estado='SOLVE_EXPORTADO_AGUARDA_AUDITORIA', pid=pid, fim=datetime.now().astimezone().isoformat()))
    log('SOLVE_EXPORTADO_GUI_PRESERVADA')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('etapa', choices=['preparar', 'resolver'])
    parser.add_argument('--pid', type=int, required=True)
    args = parser.parse_args()
    desktop = attach(args.pid)
    try:
        (prepare if args.etapa == 'preparar' else solve)(desktop, args.pid)
    except Exception:
        if ROOT.exists():
            log(traceback.format_exc())
        raise
