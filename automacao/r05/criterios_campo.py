# -*- coding: utf-8 -*-
"""Convergencia de S e do campo frontal/proximo aos limites dos dois feixes."""
def configure(design, reset=False, max_delta_s=.008, field_delta=.05, maximum_passes=18, minimum_passes=3):
    cache = ['NAME:ExpressionCache']
    samples = [(0,90),(-60,90),(-50,90),(-40,90),(40,90),(50,90),(60,90),(-3,0),(3,0)]
    for theta,phi in samples:
        title='G_%s%d_P%d'%('M' if theta<0 else 'P',abs(theta),phi)
        cache.append(['NAME:CacheItem','Title:=',title,
            'Expression:=','dB(RealizedGainTotal)',
            'Intrinsics:=',"Phi='%sdeg' Theta='%sdeg'"%(phi,theta),
            'IsConvergence:=',True,'UseRelativeConvergence:=',0,
            'MaxConvergenceDelta:=',field_delta,'MaxConvergeValue:=',str(field_delta),
            'ReportType:=','Far Fields',['NAME:ExpressionContext','Context:=','HV']])
    setup=design.GetModule('AnalysisSetup')
    if reset and 'Banda' in setup.GetSetups():
        setup.DeleteSetups(['Banda'])
    data=['NAME:Banda','SolveType:=','Single','Frequency:=','5.17GHz',
         'MaxDeltaS:=',max_delta_s,'MaximumPasses:=',maximum_passes,'MinimumPasses:=',minimum_passes,
         'MinimumConvergedPasses:=',2,'PercentRefinement:=',15,'BasisOrder:=',0,
         'DrivenSolverType:=','Iterative Solver','IterativeResidual:=',.00001,
         'SaveAnyFields:=',True,'SaveRadFieldsOnly:=',False,'UseCacheFor:=',['Pass'],cache]
    if 'Banda' not in setup.GetSetups():
        setup.InsertSetup('HfssDriven',['NAME:Banda','Frequency:=','5.17GHz',
            'MaxDeltaS:=',.008,'MaximumPasses:=',18,'MinimumConvergedPasses:=',2])
    setup.EditSetup('Banda',data)
