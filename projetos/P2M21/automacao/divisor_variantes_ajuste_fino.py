"""Ajuste fino: duas fases em B e um retorno estreito, sem alterar fontes externas."""
import json
from pathlib import Path
ROOT=Path('D:/dev/EMBRAER/P2M21/R09_Divisor_Simetria')
SCRIPTS=Path(__file__).parent
variants=[('v06_B12_superior2',12.,2.,0.,1.8),
          ('v07_B10_superior3',10.,3.,0.,1.8),
          ('v08_B145_inferior05_terra33',17-2.50916841304063,0.,.5,1.65)]
original=(ROOT/'v01_central_layout.py').read_text(encoding='utf-8')
for name,extra_b,upper,lower,half in variants:
    assert not (ROOT/name).exists(),name
    text=original.replace("dest=root/'v01_central'",f'dest=root/{name!r}')
    old="            pts50=[pts70[-1],(cx+p,ty),(cx+p,-p if pol=='A' else p)]"
    assert old in text
    text=text.replace(old,f'''            depth=({extra_b!r}/2 if pol=='B' else 0.)+({upper!r}/2 if sign>0 else {lower!r}/2)
            if depth>0:
                ym=ty+(depth if pol=='B' else -depth)
                pts50=[pts70[-1],(tx+sign*(l70+1),ty),(tx+sign*(l70+1),ym),
                    (tx+sign*(l70+5),ym),(tx+sign*(l70+5),ty),(cx+p,ty),(cx+p,-p if pol=='A' else p)]
            else:pts50=[pts70[-1],(cx+p,ty),(cx+p,-p if pol=='A' else p)]''')
    text=text.replace('buffer(1.8,cap_style=',f'buffer({half!r},cap_style=')
    (ROOT/(name+'_layout.py')).write_text(text,encoding='utf-8')
    exec(compile(text,str(ROOT/(name+'_layout.py')),'exec'),{'__file__':str(SCRIPTS/'dois_verticais_layout.py')})
    cfg=json.loads((ROOT/'v01_central/configuracao.json').read_text(encoding='utf-8'))
    cfg.update(native='Divisor_'+name+'.aedt',variante=name,adicional_B_mm=extra_b,
        adicional_superior_AB_mm=upper,adicional_inferior_AB_mm=lower,largura_retorno_mm=2*half,
        descricao='Ajuste fino por comprimentos e largura nominal de retorno. Fontes externas .5W/0graus iguais.')
    (ROOT/name/'configuracao.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
cad=(ROOT/'criar_cad.py').read_text(encoding='utf-8')
old="for folder in [root/name for name in ['v00_terra6', 'v01_central', 'v02_central_terra6']]:"
assert old in cad
cad=cad.replace(old,'for folder in [root/name for name in '+repr([v[0] for v in variants])+']:')
(ROOT/'criar_cad_etapa3.py').write_text(cad,encoding='utf-8')
study=json.loads((ROOT/'estudo.json').read_text(encoding='utf-8'));study['variantes'] += [v[0] for v in variants]
(ROOT/'estudo.json').write_text(json.dumps(study,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
