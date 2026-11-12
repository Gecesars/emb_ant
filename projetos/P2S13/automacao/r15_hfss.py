# -*- coding: utf-8 -*-
"""Confirmar novo divisor, com importacao geometrica verificada antes do solve."""
import os
path='D:/dev/EMBRAER/emb_ant/projetos/P2S13/automacao/r14_divisor_hfss.py'
with open(path) as f:code=f.read()
needle="    apply(p,d,json.load(open(os.path.join(cad,'folhas_solidas.json'))),os.path.join(cad,'enig_hfss.json'))"
check="""    geometry=json.load(open(os.path.join(cad,'geometria_esperada.json')));verified={}
    for name,g in geometry.items():
        bbox=[float(v) for v in e.GetObjectBoundingBox(name)];volume=float(e.GetObjectVolume(name))
        err=max(abs(a-b) for a,b in zip(bbox,g['bbox_mm']));ev=abs(volume-g['volume_mm3'])/g['volume_mm3']
        verified[name]=dict(erro_bbox_mm=err,erro_volume_rel=ev,aprovado=err<.001 and ev<.001)
    save('geometria_importada.json',verified)
    assert all(v['aprovado'] for v in verified.values()),verified
"""
assert code.count(needle)==1
exec(compile(code.replace(needle,check+needle),path,'exec'))
