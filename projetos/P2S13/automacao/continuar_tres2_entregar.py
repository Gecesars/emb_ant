"""Compara passes6/8 do painel3xPCB2 e arquiva evidencias sem malhas."""
from pathlib import Path
import json,re,csv,sys,hashlib,shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
REPO=Path(__file__).resolve().parents[3];ROOT=Path('D:/dev/EMBRAER/P2S13/R06_Continuacao_Tres2');OUT=REPO/'projetos/P2S13/continuacao_tres_placas2';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(REPO/'automacao/r05'));from rede_carregada import read_pattern
assert json.loads((ROOT/'continuidade_auditada.json').read_text())['aprovado']
folders=[ROOT/'referencia6',ROOT];rows=[]
for folder in folders:
    r=json.loads((folder/'resultado.json').read_text());h,v=r['cortes']['H'],r['cortes']['V'];hist=json.loads((folder/'historico_passes.json').read_text())['historico']
    rows.append(dict(passes=r['passes'],DeltaS=r['delta_s'],consecutivos=int(re.search(r'Current Consecutive Passes\s*:\s*(\d+)',(folder/'convergencia.txt').read_text())[1]),convergiu_S=r['convergiu'],G_dBi=h['ganho_frontal_dBi'],H_graus=h['abertura_graus'],V_graus=v['abertura_graus'],pico_H_graus=h['pico_graus'],pico_V_graus=v['pico_graus'],SLL_V_dB=v['SLL']['nivel_dB'],VSWR_ativo_max=max(r['VSWR_ativo']),VSWR_casado_max=max(r['VSWR_casado']),campo_ultimo_delta_dB=hist[-1]['delta_campo_max_dB'],campos_estaveis=r['estavel_nove_sondas'],auditoria=r['fisica_ok'],reciprocidade=r['reciprocidade']))
a,b=rows;assert a['passes']==6 and b['passes']==8
delta={k:b[k]-a[k] for k in ['G_dBi','H_graus','V_graus','VSWR_ativo_max','VSWR_casado_max']}
(ROOT/'comparacao.json').write_text(json.dumps(dict(resultados=rows,delta_8_menos_6=delta,condicoes='3PCBs2, b28.5/150, seis entradas1/6W/0graus, cabos fisicos50mm com perdas, 5.17GHz,14nucleos,sem sweep; somente passes7/8 novos'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (ROOT/'comparacao.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(a));w.writeheader();w.writerows(rows)
fig,axs=plt.subplots(1,2,figsize=(12,6))
for folder,row in zip(folders,rows):
    for ax,axis in zip(axs,'HV'):
        t,e=read_pattern(folder/('ALL_'+axis+'.csv'));g=10*np.log10(np.sum(abs(e)**2,axis=1));ax.plot(t,g,label='%d passes | G%.3f dBi'%(row['passes'],row['G_dBi']))
for ax,axis in zip(axs,'HV'):
    ax.set(xlim=(-90,90),ylim=(-22,16),title=axis,xlabel='Ângulo (graus)',ylabel='Ganho realizado total (dBi)');ax.grid(alpha=.2);ax.legend(loc='lower center')
fig.suptitle('Três placas de dois elementos — continuação da mesma malha\n5,17 GHz | seis entradas iguais/em fase | 14 núcleos | somente passes 7 e 8 novos\nConvergência de S e estabilidade dos campos avaliadas separadamente')
fig.tight_layout(rect=(0,.02,1,.85));fig.savefig(ROOT/'comparacao_HV.png',dpi=170);plt.close(fig)
cfg=json.loads((ROOT/'configuracao.json').read_text());r=json.loads((ROOT/'resultado.json').read_text());hist=json.loads((ROOT/'historico_passes.json').read_text())['historico'];cont=json.loads((ROOT/'continuidade_auditada.json').read_text())
table=[]
for label,key,fmt in [('ΔS','DeltaS','.6f'),('Passes consecutivos','consecutivos','d'),('Ganho frontal realizado (dBi)','G_dBi','.4f'),('Abertura H (°)','H_graus','.3f'),('Abertura V (°)','V_graus','.3f'),('Máximo H (°)','pico_H_graus','+.2f'),('Máximo V (°)','pico_V_graus','+.2f'),('SLL vertical (dB)','SLL_V_dB','.3f'),('VSWR ativo máximo','VSWR_ativo_max','.5f'),('VSWR demais portas casadas, máximo','VSWR_casado_max','.5f')]:table.append('| %s | %s | %s |'%(label,format(a[key],fmt),format(b[key],fmt)))
ports=['| %s | %.5f | %.5f |'%(n,x,y) for n,x,y in zip(r['ordem_portas'],r['VSWR_ativo'],r['VSWR_casado'])]
yes=lambda v:'sim' if v else 'não'
md=f'''# P2S13 — continuação das três placas de dois elementos

Executados **somente os passes 7 e 8**, preservando a malha e os seis anteriores da versão b=28,5 mm / 150°. **Convergência ΔS≤0,05 por dois passes consecutivos: {yes(b['convergiu_S'])}**. Último ΔS **{b['DeltaS']:.8f}**, contador consecutivo **{b['consecutivos']}**. Estabilidade das nove sondas de campo: **{yes(b['campos_estaveis'])}**. Auditoria numérica completa: **{yes(b['auditoria'])}**.

## Condições e continuidade

Três PCBs idênticas de dois elementos, seis níveis a 48 mm, placas a 96 mm e vão de 8 mm. Refletor Al2mm, comprimento296mm, largura desenvolvida90mm, início das dobras28,5mm e ângulo150° para trás. Altura da PCB14,949mm. Seis cabos físicos de50mm e redes1:2 impressas com perdas, sem divisores externos ou N. **Seis entradas1/6W a0°, total1W, 5,17GHz,14núcleos,sem sweep.** Ganho realizado total, não ganho MIMO por entrada isolada.

A cópia preservou os76arquivos de resultados por SHA-256. O HFSS reconheceu os seis passes; a retomada iniciou no passe7. O setup mudou somente máximo6→8 e mínimo2→8. Geometria, materiais, fronteiras, malha, nove caches e fontes foram mantidos. Os seis registros completos iniciais permaneceram idênticos; a fonte R05 e seus resultados não foram alterados. [Auditoria antes da retomada](preparacao_auditada.json) · [Auditoria final](continuidade_auditada.json) · [Origem e hashes](origem.json).

## Resultados

| Grandeza | 6 passes | 8 passes |
|---|---:|---:|
{chr(10).join(table)}

Variações6→8: ganho **{delta['G_dBi']:+.4f}dB**, H **{delta['H_graus']:+.3f}°**, V **{delta['V_graus']:+.3f}°**. A última malha tem **{hist[-1]['tetraedros']} tetraedros**. Maior variação de campo no último passe **{b['campo_ultimo_delta_dB']:.6f}dB** (monitor0,1dB por dois passes). Reciprocidade máxima |S−Sᵀ| **{r['reciprocidade']:.8g}**, limite1×10⁻⁵. Passividade: **{yes(r['verificacoes']['passividade'])}**; balanço de potência: **{yes(r['verificacoes']['eficiencia_e_balanco'])}**; reparos Major/Minor: **{r['major']}/{r['minor']}**. Não confundir convergência de S com aprovação de todos os campos ou medição experimental.

| Entrada | VSWR ativo | VSWR demais casadas |
|---|---:|---:|
{chr(10).join(ports)}

As metas anteriores de H próximo100°, ganho≥13dBi e VSWR≤1,25 são verificadas separadamente no [resultado](resultado.json). Não há qualificação de banda. O próximo estudo solicitado é o divisor duplo1:3 carregado pela matriz S6, com casamento visto nas duas entradas externas; os resultados desta página ainda são das seis entradas diretas.

![Comparação de6e8passes](comparacao_HV.png)

![Diagramas polares finais](polar_HV.png)

[HFSS atualizado]({cfg['native']}) · [Montagem FreeCAD]({cfg['cad_native']}) · [Tabela CSV](comparacao.csv) · [S6](centro.s6p) · [Histórico de seis passes](../tres_placas2/README.md) · [Manifesto](manifesto.json).

Trabalho local: `{ROOT.as_posix()}`. Nativos, Touchstone, campos distantes e evidências compactas arquivados; sem `.aedtresults`, malhas, locks ou campos volumétricos. A solução FEM completa permanece local. Nenhum passe além do8 foi programado.
'''
for x,y in [('Al2mm','Al 2 mm'),('comprimento296mm','comprimento 296 mm'),('desenvolvida90mm','desenvolvida 90 mm'),('dobras28,5mm','dobras 28,5 mm'),('ângulo150°','ângulo 150°'),('PCB14,949mm','PCB 14,949 mm'),('de50mm','de 50 mm'),('redes1:2','redes 1:2'),('entradas1/6W a0°','entradas de 1/6 W a 0°'),('total1W','total 1 W'),('5,17GHz,14núcleos,sem','5,17 GHz, 14 núcleos, sem'),('os76arquivos','os 76 arquivos'),('passe7','passe 7'),('máximo6→8','máximo 6→8'),('mínimo2→8','mínimo 2→8'),('Variações6→8','Variações 6→8'),('monitor0,1dB','monitor 0,1 dB'),('limite1×','limite 1×'),('próximo100°','próximo de 100°'),('divisor duplo1:3','divisor duplo 1:3'),('além do8','além do 8')]:md=md.replace(x,y)
(OUT/'README.md').write_text(md,encoding='utf-8')
(ROOT/'entrega.json').write_text(json.dumps(dict(estado='CONCLUIDO',novos_passes=[7,8],malha_preservada=True,convergiu_S=b['convergiu_S'],campos_estaveis=b['campos_estaveis'],auditoria=b['auditoria'],proximo_solve_automatico=False),indent=2)+'\n')
records=[]
def cp(p):
    assert p.is_file() and not any(x.endswith('.aedtresults') for x in p.parts) and p.suffix.lower() not in ['.g3derr','.fld','.ngmesh','.lock','.log','.profile']
    dest=OUT/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);h=hashlib.sha256(p.read_bytes()).hexdigest();assert hashlib.sha256(dest.read_bytes()).hexdigest()==h
    records.append(dict(arquivo=dest.relative_to(REPO).as_posix(),fonte=str(p),sha256=h,bytes=p.stat().st_size))
assert not (ROOT/(cfg['native']+'.lock')).exists()
for name in [cfg['native'],cfg['cad_native'],'HFSS_14nucleos.acf','configuracao.json','origem.json','antes_convergencia.txt','preparacao_auditada.json','continuidade_auditada.json','qualificacao.json','entrega.json','resultado.json','comparacao.json','comparacao.csv','comparacao_HV.png','convergencia.txt','historico_passes.json','recursos_matriz.json','ordem_fontes.json','mensagens.json','malha.json','malha_inicial.json','diagramas_HV.png','polar_HV.png','centro.s6p']:cp(ROOT/name)
for p in ROOT.glob('*.csv'):
    if p.stem.startswith(('ALL_','POL_','R1_','R2_','R3_')):cp(p)
for p in (ROOT/'cad').glob('*.json'):cp(p)
(OUT/'manifesto.json').write_text(json.dumps(dict(artefatos=records,total_bytes=sum(x['bytes'] for x in records),excluidos='Malhas,aedtresults,locks,campos volumetricos. Referencia6 arquivada na R05.'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(resultados=rows,artefatos=len(records)),indent=2))
