# -*- coding: utf-8 -*-
"""Criar divisor ajustado sem resolver antes de acrescentar PVC."""
import os
path='D:/dev/EMBRAER/emb_ant/projetos/P2S13/automacao/r14_divisor_hfss.py'
code=open(path).read()
needle="    apply(p,d,json.load(open(os.path.join(cad,'folhas_solidas.json'))),os.path.join(cad,'enig_hfss.json'))"
check="""    geometry=json.load(open(os.path.join(cad,'geometria_esperada.json')));verified={}
    for name,g in geometry.items():
        bbox=[float(v) for v in e.GetObjectBoundingBox(name)];volume=float(e.GetObjectVolume(name))
        err=max(abs(a-b) for a,b in zip(bbox,g['bbox_mm']));ev=abs(volume-g['volume_mm3'])/g['volume_mm3']
        verified[name]=dict(erro_bbox_mm=err,erro_volume_rel=ev,aprovado=err<.001 and ev<.001)
    save('geometria_importada.json',verified)
    assert all(v['aprovado'] for v in verified.values()),verified
"""
assert code.count(needle)==1;code=code.replace(needle,check+needle)
start=code.index('    oDesktop.SetRegistryFromFile(');end=code.index('\nexcept:',start)
code=code[:start]+"    oDesktop.CloseProject(p.GetName())\n    save('estado.json',dict(estado='CRIADO_SEM_SOLVE'))\n"+code[end:]
assert ".Analyze(" not in code
exec(compile(code,path,'exec'))
