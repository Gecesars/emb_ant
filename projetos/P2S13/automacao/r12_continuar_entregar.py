"""Comparacao 6/8 e pacote compacto de resultados; nunca inicia solver."""
from pathlib import Path
import json,hashlib,shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path('D:/dev/EMBRAER/P2S13/R12_Continuacao8')
REPO=Path(__file__).resolve().parents[3]
OUT=REPO/'projetos/P2S13/curvilinear_simplificado/continuacao8'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
cfg=read(ROOT/'configuracao.json');r=read(ROOT/'resultado.json');old=read(ROOT/'referencia6/resultado.json')
assert r['passes']==8 and read(ROOT/'continuidade_auditada.json')['primeiros_seis_identicos']
assert not list(ROOT.glob('*.aedt.lock'))
assert sha(ROOT/cfg['native'])==r['fontes_sha256'][cfg['native']]
delta=dict(ganho_frontal_dB=r['cortes']['H']['ganho_frontal_dBi']-old['cortes']['H']['ganho_frontal_dBi'],
    H_graus=r['cortes']['H']['abertura_graus']-old['cortes']['H']['abertura_graus'],
    V_graus=r['cortes']['V']['abertura_graus']-old['cortes']['V']['abertura_graus'],
    VSWR_ativo=(np.array(r['VSWR_ativo'])-old['VSWR_ativo']).tolist())
write(ROOT/'comparacao6_8.json',dict(referencia='R12_Curvilinear_Simplificado',passes_adicionados=[7,8],
    antes=old,depois=r,diferencas=delta))
state=read(ROOT/'pipeline.json');state.update(estado='CONCLUIDO_COMPARADO',convergiu_delta_s=r['convergiu'],validacao_nominal=r['validacao_nominal'])
write(ROOT/'pipeline.json',state)
fig,axs=plt.subplots(1,2,figsize=(12,5))
source=Path(read(ROOT/'origem.json')['fonte'])
for ax,axis in zip(axs,'HV'):
    for folder,label in [(source,'6 passes'),(ROOT,'8 passes')]:
        a=np.loadtxt(folder/('diagrama_'+axis+'.csv'),delimiter=',',skiprows=1)
        ax.plot(a[:,0],a[:,1],label=label)
    ax.set(xlim=(-90,90),ylim=(-15,15),xlabel='Ângulo (°)',ylabel='Ganho realizado total (dBi)',title=axis)
    ax.grid(alpha=.3);ax.legend()
fig.suptitle('R12 — comparação da mesma malha: passes 6 e 8\n5,17 GHz | duas entradas de 0,5 W / 0° | sem sweep')
fig.tight_layout();fig.savefig(ROOT/'comparacao6_8.png',dpi=160);plt.close(fig)
rows=[]
for label,a,b in [('ΔS',old['delta_s'],r['delta_s']),('G frontal (dBi)',old['cortes']['H']['ganho_frontal_dBi'],r['cortes']['H']['ganho_frontal_dBi']),
    ('VSWR ativo A',old['VSWR_ativo'][0],r['VSWR_ativo'][0]),('VSWR ativo B',old['VSWR_ativo'][1],r['VSWR_ativo'][1]),
    ('H (graus)',old['cortes']['H']['abertura_graus'],r['cortes']['H']['abertura_graus']),('V (graus)',old['cortes']['V']['abertura_graus'],r['cortes']['V']['abertura_graus']),
    ('Máximo V (graus)',old['vertical_fino']['pico_interpolado_graus'],r['vertical_fino']['pico_interpolado_graus']),
    ('Assimetria principal V (dB)',old['vertical_fino']['assimetria_max_dB'],r['vertical_fino']['assimetria_max_dB'])]:
    rows.append(f'| {label} | {a:.6f} | {b:.6f} |')
p=read(ROOT/'potencia_conferida.json')['balanco_S']
text=f'''# R12 — dois passes adicionais, oito no total

Solicitação de 12/11/2026. Executados somente os passes 7 e 8, a 5,17 GHz, sem sweep e com 14 núcleos em cada solução matricial. Duas entradas externas de 0,5 W a 0°, total 1 W. Mesmos três módulos radiantes M00, divisor duplo C08, seis cabos físicos com perdas, refletor e radome FR-4 de 2 mm.

## Resultado

| Grandeza | Seis passes | Oito passes |
| --- | ---: | ---: |
{chr(10).join(rows)}

Convergência HFSS: **{'sim' if r['convergiu'] else 'não'}**, {r['consecutivos']} passes consecutivos no alvo ΔS≤0,05; são exigidos dois. Balanço de potência consistente: **{r['potencia_balanco_aprovado']}**. Validação nominal completa: **{r['validacao_nominal']}**. As comparações numéricas não qualificam resultados sem convergência ou com falha física. Estabilidade de nove amostras de campo nos dois últimos passes: {r['estabilidade_campos_ultimos_dB']} dB (monitoramento de 0,1 dB).

VSWR com a outra entrada casada: {r['VSWR_outra_casada'][0]:.6f} / {r['VSWR_outra_casada'][1]:.6f}. Máximo horizontal em {r['cortes']['H']['pico_graus']:+.2f}°, com {r['cortes']['H']['ganho_pico_dBi']:.6f} dBi; distinguir esse pico do ganho frontal. A assimetria V se refere apenas ao lóbulo principal no intervalo {r['vertical_fino']['intervalo_simetria_graus']}, com critério de 0,2 dB; tolerância angular anterior de ±0,5°. Lóbulos secundários estão registrados em `resultado.json`.

## Potência e integridade

Potência incidente 1 W; refletida {p['refletida_W']:.9f} W; aceita {p['aceita_W']:.9f} W; radiada {p['radiada_W']:.9f} W. Dissipação inferida por diferença aceita−radiada: {p['dissipada_W']:.9f} W, sem decomposição por material. Conferir `potencia_conferida.json` e o perfil matricial em `auditoria_solver_matricial.json`.

A cópia de 65 arquivos de resultados preservou a malha nativa, os campos e o cache por SHA256. Antes de resolver, a auditoria confirmou que somente MaximumPasses 6→8 e MinimumPasses 2→8 mudaram; geometria, materiais, fronteiras e malha foram preservados. A auditoria final confirmou os mesmos seis passes iniciais, inclusive tetraedros, ΔS e nove campos, e verificou que a origem não foi alterada. Não houve reinício da adaptação. Os oito passes são o total histórico, não oito novos.

![Diagramas polares H/V](polar_HV.png)

![Simetria vertical](simetria_vertical.png)

![Comparação seis e oito passes](comparacao6_8.png)

## Arquivos

`P2S13_Curvilinear.aedt`: projeto fechado, com a geometria e o setup atualizados. `centro.s2p`, cortes complexos e diagramas CSV são exportações do campo distante. `resultado.json`, histórico e auditorias rastreiam o resultado. Malhas, resultados volumétricos, locks e temporários ficam somente na pasta de trabalho local, fora do Git; o nativo isolado exige novo solve para restaurar os campos no HFSS. A referência de seis passes está preservada no diretório superior e na pasta local `referencia6`.

As geometrias KiCad e FreeCAD desta entrega são idênticas às PCBs simuladas; sua organização não implica aprovação RF. FR-4 nominal Isola370HR εr3,92/tanδ0,025, sem caracterização do lote, adesivos ou conectores externos. Simulação de frequência única.
'''
(ROOT/'README.md').write_bytes(text.encode('utf-8'))
OUT.mkdir(parents=True,exist_ok=True);items=[]
names=[cfg['native'],'configuracao.json','resultado.json','centro.s2p','convergencia.txt','historico_passes.json','convergencia_campos.json',
    'conferencia_perfil.json','recursos_matriz.json','auditoria_solver_matricial.json','malha.json','mensagens.json','potencia.json','potencia_conferida.json',
    'polar_HV.png','simetria_vertical.png','comparacao6_8.json','comparacao6_8.png','pipeline.json','qualificacao.json','ordem_fontes.json',
    'origem.json','antes_convergencia.txt','preparacao_auditada.json','continuidade_auditada.json','README.md']
names+=sorted({p.name for pat in ['ALL_*.csv','POL_*.csv','IN_*.csv','diagrama_*.csv'] for p in ROOT.glob(pat)})
for name in names:
    s=ROOT/name;d=OUT/name;assert s.is_file(),s
    shutil.copy2(s,d);assert sha(s)==sha(d)
    items.append(dict(arquivo=d.relative_to(REPO).as_posix(),sha256=sha(d),bytes=d.stat().st_size))
write(OUT/'manifesto.json',dict(arquivos=items,excluidos=['aedtresults','malhas','campos_volumetricos','locks']))
print(json.dumps(dict(arquivos=len(items),delta=delta,convergiu=r['convergiu'],validacao_nominal=r['validacao_nominal']),indent=2))
