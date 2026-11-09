# -*- coding: utf-8 -*-
"""Diagnostico local Ez, com fontes AB. Nao cria geometria nem executa solver.
API nativa conforme export_field_file do PyAEDT local. Dados auxiliares;
as integrais aproximadas nao sao ondas de porta nem potencia por radiador.
"""
try:
    pts=os.path.join(root,'sondas.pts')
    with open(pts,'w') as f:
        f.write('Unit=mm\n')
        for cx in [-72.,-24.,24.,72.]:
            for y in [-2.50916841304063,2.50916841304063]:
                for iz in range(21):
                    z=16.61001+iz*(.75998/20.)
                    f.write('%.12g %.12g %.12g\n'%(cx+2.50916841304063,y,z))
    fr=d.GetModule('FieldsReporter')
    for op in ['Real','Imag']:
        fr.CalcStack('clear');fr.EnterQty('E');fr.CalcOp('ScalarZ');fr.CalcOp(op)
        fr.ExportToFile(os.path.join(root,'sondas_'+op+'.fld'),pts,'Centro : LastAdaptive',
            ['Freq:=','5.17GHz','Phase:=','0deg'],
            ['NAME:ExportOption','IncludePtInOutput:=',True,'RefCSName:=','Global','PtInSI:=',False,'FieldInRefCS:=',True])
    fr.CalcStack('clear')
    log('SONDAS_EZ_EXPORTADAS')
except:
    write('sondas_falha.json',dict(erro=traceback.format_exc()))
    log('SONDAS_AUXILIARES_FALHARAM '+traceback.format_exc())
