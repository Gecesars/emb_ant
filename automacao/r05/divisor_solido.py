# -*- coding: utf-8 -*-
"""Verificar ENIG unilateral sobre Cu volumetrico no divisor isolado."""
import json
import os
import re
import sys
import traceback
import ScriptEnv
sys.path.insert(0, os.path.dirname(__file__))
from enig_solido import apply
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root = os.environ['P1H_DIVISOR_SOLIDO']

def log(value):
    with open(os.path.join(root, 'solucao.log'), 'a') as stream:
        stream.write(str(value) + '\n')

try:
    project = oDesktop.OpenProject(os.path.join(root, 'Divisor_solido.aedt'))
    design = project.SetActiveDesign('Duplo_radial')
    editor = design.SetActiveEditor('3D Modeler')
    boundaries = design.GetModule('BoundarySetup')
    geometry = json.load(open(os.path.join(root, 'geometria.json')))
    sheets = sorted(name for name in editor.GetObjectsInGroup('Sheets')
                    if name == 'GND' or name.startswith(('Estrela_', 'Anel_')))
    assert len(sheets) == len(geometry['ports']) + 3
    boundaries.DeleteBoundaries(['Cobre_35um'])
    records = {}
    for name in sheets:
        z = geometry['h'] if name.startswith('Estrela_') else 0.
        outward = 1 if name.startswith('Estrela_') else -1
        before = set(editor.GetObjectsInGroup('Sheets'))
        editor.DuplicateAlongLine(['NAME:Selections', 'Selections:=', name, 'NewPartsModelFlag:=', 'Model'],
            ['NAME:DuplicateToAlongLineParameters', 'CreateNewObjects:=', True,
             'XComponent:=', '0mm', 'YComponent:=', '0mm', 'ZComponent:=', '100mm', 'Numclones:=', '2'],
            ['NAME:Options', 'DuplicateAssignments:=', False])
        copies = set(editor.GetObjectsInGroup('Sheets')) - before
        assert len(copies) == 1
        probe = list(copies)[0]
        editor.ThickenSheet(['NAME:Selections', 'Selections:=', probe, 'NewPartsModelFlag:=', 'Model'],
            ['NAME:SheetThickenParameters', 'Thickness:=', '1mm', 'BothSides:=', False])
        bounds = [float(v) for v in editor.GetObjectBoundingBox(probe)]
        normal = 1 if bounds[5] > z + 100.5 else -1
        assert abs(bounds[5] - bounds[2] - 1) < 1e-6
        editor.Delete(['NAME:Selections', 'Selections:=', probe])
        editor.ThickenSheet(['NAME:Selections', 'Selections:=', name, 'NewPartsModelFlag:=', 'Model'],
            ['NAME:SheetThickenParameters', 'Thickness:=', str(.035*outward*normal)+'mm', 'BothSides:=', False])
        if name == 'GND':
            tools = [prefix + p[0] for p in geometry['ports'] for prefix in ('Blindagem_', 'Solda_ext_')]
        elif name.startswith('Estrela_'):
            tools = ['Solda_top_' + p[0] for p in geometry['ports'] if p[0][0] == name[-1]]
        else:
            tools = ['Central_' + name[5:]]
        editor.Subtract(['NAME:Selections', 'Blank Parts:=', name, 'Tool Parts:=', ','.join(tools)],
            ['NAME:SubtractParameters', 'KeepOriginals:=', True])
        records[name] = dict(base_z_mm=z, exposto=outward, espessura_mm=.035)
    apply(project, design, records, os.path.join(root, 'enig_solido_hfss.json'))
    setup = design.GetModule('AnalysisSetup')
    setup.EditSetup('Divisor', ['NAME:Divisor', 'Frequency:=', '5.17GHz', 'MaxDeltaS:=', .008,
        'MaximumPasses:=', 16, 'MinimumPasses:=', 3, 'MinimumConvergedPasses:=', 2,
        'PercentRefinement:=', 24, 'BasisOrder:=', 1])
    if 'Banda' not in setup.GetSweeps('Divisor'):
        setup.InsertFrequencySweep('Divisor', ['NAME:Banda', 'IsEnabled:=', True,
            'RangeType:=', 'LinearStep', 'RangeStart:=', '5090MHz', 'RangeEnd:=', '5250MHz',
            'RangeStep:=', '10MHz', 'Type:=', 'Discrete', 'SaveFields:=', False, 'SaveRadFields:=', False])
    assert design.ValidateDesign() == 1
    project.Save()
    log('MODELO_SOLIDO_OK')
    design.Analyze('Divisor')
    convergence_path = os.path.join(root, 'convergencia.txt')
    design.ExportConvergence('Divisor', '', convergence_path)
    convergence = open(convergence_path).read()
    assert 'Converged : Yes' in convergence
    assert int(re.search(r'Current Consecutive Passes\s*:\s*(\d+)', convergence).group(1)) >= 2
    design.GetModule('Solutions').ExportNetworkData('', ['Divisor : Banda'], 3,
        os.path.join(root, 'divisor.s%dp' % len(geometry['ports'])), ['All'], True, 50, 'S', -1, 1, 15, False, True, False)
    project.Save()
    oDesktop.CloseProject(project.GetName())
    log('DIVISOR_SOLIDO_OK')
except:
    log(traceback.format_exc())
