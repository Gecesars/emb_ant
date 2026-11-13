"""Audita diferenças geométricas declaradas entre os candidatos, sem solve."""
from pathlib import Path
import json,hashlib
WORK=Path('D:/dev/EMBRAER/P2M19')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
base=WORK/'R01_16x2_88mm';base_cfg=read(base/'configuracao.json');base_geo=read(base/'cad/geometria_esperada.json')
rows=[]
for name in ['R02_16x2_72mm','R03_72mm_ref162','R04_72mm_ref146']:
    root=WORK/name;cfg=read(root/'configuracao.json');geo=read(root/'cad/geometria_esperada.json')
    assert set(geo)==set(base_geo) and len(geo)==329
    for key in ['fontes_sha256','frequencia_GHz','max_passes','min_passes','max_delta_s','passes_consecutivos','nucleos','sweep','basis_order','percent_refinement','potencia_por_porta_W','fase_graus','solver_type']:
        assert cfg[key]==base_cfg[key],(name,key)
    max_box=max_volume=0
    for label,g in geo.items():
        if label=='Refletor_Al2mm':continue
        dy=8 if label.startswith('C1') else -8
        expected=[x+(dy if i in [1,4] else 0) for i,x in enumerate(base_geo[label]['bbox_mm'])]
        max_box=max(max_box,max(abs(x-y) for x,y in zip(expected,g['bbox_mm'])))
        max_volume=max(max_volume,abs(g['volume_mm3']-base_geo[label]['volume_mm3']))
    assert max_box<1e-6 and max_volume<1e-6
    assert read(root/'cad/intersecoes.json')['aprovado'] and read(root/'cad/reabertura.json')['todos_validos']
    rows.append(dict(caso=name,objetos=329,corpos_PCB_e_terminais_preservados=328,
        deslocamentos_colunas_Y_mm=[8,-8],erro_bbox_mm=max_box,erro_volume_mm3=max_volume,
        refletor_mm=cfg['refletor_mm'],altura_pcb_mm=cfg['distancia_face_inferior_laminado_ao_refletor_mm'],
        folga_lateral_mm=cfg['folga_placas_horizontal_mm'],setup_configuracao_igual_R01=True,
        geometria_sha256=hashlib.sha256((root/'cad/geometria_esperada.json').read_bytes()).hexdigest()))
out=WORK/'Campanha_72mm_20261113/controle_geometria.json'
out.write_text(json.dumps(dict(aprovado=True,referencia=str(base),casos=rows),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(out)
