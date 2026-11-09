"""Segunda etapa: comprimentos de ramos a partir da variante de conexoes centrais."""
import json
from pathlib import Path
ROOT=Path('D:/dev/EMBRAER/P2M21/R09_Divisor_Simetria')
SCRIPTS=Path(__file__).parent
variants=[('v03_B_longo',True,0.,0.),('v04_superior_16',False,.8,0.),('v05_B_longo_inferior_15',True,0.,.75)]
original=(ROOT/'v01_central_layout.py').read_text(encoding='utf-8')
for name,long_b,upper,lower in variants:
    assert not (ROOT/name).exists(),name
    text=original.replace("dest=root/'v01_central'",f'dest=root/{name!r}')
    old="            pts50=[pts70[-1],(cx+p,ty),(cx+p,-p if pol=='A' else p)]"
    assert old in text
    new=f'''            depth=((17-p)/2 if pol=='B' and {long_b!r} else 0.)+({upper!r} if sign>0 else {lower!r})
            if depth>0:
                ym=ty+(depth if pol=='B' else -depth)
                pts50=[pts70[-1],(tx+sign*(l70+1),ty),(tx+sign*(l70+1),ym),
                    (tx+sign*(l70+5),ym),(tx+sign*(l70+5),ty),(cx+p,ty),(cx+p,-p if pol=='A' else p)]
            else:pts50=[pts70[-1],(cx+p,ty),(cx+p,-p if pol=='A' else p)]'''
    text=text.replace(old,new)
    (ROOT/(name+'_layout.py')).write_text(text,encoding='utf-8')
    exec(compile(text,str(ROOT/(name+'_layout.py')),'exec'),{'__file__':str(SCRIPTS/'dois_verticais_layout.py')})
    cfg=json.loads((ROOT/'v01_central/configuracao.json').read_text(encoding='utf-8'))
    cfg.update(native='Divisor_'+name+'.aedt',variante=name,
        adicional_B_mm=17-2.50916841304063 if long_b else 0,
        adicional_superior_AB_mm=2*upper,adicional_inferior_AB_mm=2*lower,
        descricao='Meandros nos ramos impressos; fontes externas permanecem .5W/0graus iguais. Comprimento nominal nao garante fase eletrica.')
    (ROOT/name/'configuracao.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
cad=(ROOT/'criar_cad.py').read_text(encoding='utf-8')
old="for folder in [root/name for name in ['v00_terra6', 'v01_central', 'v02_central_terra6']]:"
assert old in cad
cad=cad.replace(old,'for folder in [root/name for name in '+repr([v[0] for v in variants])+']:')
(ROOT/'criar_cad_etapa2.py').write_text(cad,encoding='utf-8')
study=json.loads((ROOT/'estudo.json').read_text(encoding='utf-8'));study['variantes'] += [v[0] for v in variants]
(ROOT/'estudo.json').write_text(json.dumps(study,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
