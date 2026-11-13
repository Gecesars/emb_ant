"""Auditoria adicional, comparacao 6/8 passes e pacote sem malhas da R05."""
from pathlib import Path
import json,hashlib,shutil,argparse,re,csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path('D:/dev/EMBRAER/P2M19/R05_72mm_ref146_8passes')
REPO=Path(__file__).resolve().parents[3]
OUT=REPO/'projetos/P2M19/continuacao_72mm_ref146_8passes'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main(pack=False):
    cfg=read(ROOT/'configuracao.json');source=Path(cfg['referencia_comparacao'])
    before=read(source/'resultado.json');after=read(ROOT/'resultado.json')
    h0=read(source/'historico_passes.json')['historico'];h=read(ROOT/'historico_passes.json')['historico']
    assert len(h0)==6 and len(h)==8 and h[:6]==h0,'Historico anterior modificado'
    assert after['passes']==8 and after['max_passes']==8 and after['nucleos']==14
    assert after['fisica_ok'] and after['balanco_potencia_valido'] and after['major']==0
    assert sha(source/cfg['native'])==cfg['continuacao']['nativo_referencia_sha256'],'Referencia foi alterada'
    old=(source/cfg['native']).read_text(errors='replace');new=(ROOT/cfg['native']).read_text(errors='replace')
    def block(raw,n): return raw.split("$begin '"+n+"'",1)[1].split("$end '"+n+"'",1)[0]
    names=['GeometryCore','Materials','BoundarySetup','MeshSetup']
    assert all(block(old,n)==block(new,n) for n in names)
    # Exportar campos com diferentes fontes incrementa VersionID/NextUniqueID
    # das esferas. Conferir todo o restante, incluindo grades e coordenadas.
    def rad_physics(text):return re.sub(r'(?m)^\s*(?:VersionID|NextUniqueID)=\d+\s*$', '',block(text,'RadField'))
    assert rad_physics(old)==rad_physics(new)
    expected=block(old,'AnalysisSetup').replace('MaximumPasses=6','MaximumPasses=8').replace('MinimumPasses=2','MinimumPasses=8')
    assert block(new,'AnalysisSetup')==expected
    oldtraces=re.findall(r'TraceID=(\d+)',block(old,'AnalysisSetup'))
    assert len(oldtraces)==9 and oldtraces==re.findall(r'TraceID=(\d+)',block(new,'AnalysisSetup'))
    ev=dict(passes_1_a_6_identicos=True,passes_adicionais=[7,8],historico_inicial_tetraedros=602282,
        referencia_nativa_sha256=sha(source/cfg['native']),nativo_final_sha256=sha(ROOT/cfg['native']),
        geometria_materiais_portas_malha_campos_iguais=True,somente_min_max_setup_alterados=True,
        trace_ids_preservados=oldtraces,sem_sweep=not cfg['sweep'],
        radfield_definicoes_iguais=True,radfield_metadados_atualizados=['VersionID','NextUniqueID'])
    save(ROOT/'evidencias/continuidade_final.json',ev)
    rows=[]
    for label,r in [('R04: seis passes',before),('R05: oito passes',after)]:
        rows.append(dict(versao=label,passes=r['passes'],delta_s=r['delta_s'],convergiu=r['convergiu'],
            ganho_dBi=r['cortes']['H']['ganho_frontal_dBi'],
            H_graus=r['cortes_finos']['H']['abertura_graus'],V_graus=r['cortes_finos']['V']['abertura_graus'],
            pico_H_graus=r['cortes_finos']['H']['pico_interpolado_graus'],pico_V_graus=r['cortes_finos']['V']['pico_interpolado_graus'],
            VSWR_ativo_min=min(r['VSWR_ativo']),VSWR_ativo_max=max(r['VSWR_ativo']),VSWR_casado_max=max(r['VSWR_casado']),
            SLL_H_dB=r['cortes']['H']['SLL']['nivel_dB'],SLL_V_dB=r['cortes']['V']['SLL']['nivel_dB']))
    delta={k:rows[1][k]-rows[0][k] for k in ['ganho_dBi','H_graus','V_graus','VSWR_ativo_max','SLL_H_dB','SLL_V_dB']}
    save(ROOT/'comparacao_6_8.json',dict(casos=rows,diferencas=delta))
    assert before['ordem_portas']==after['ordem_portas']
    with (ROOT/'vswr_por_porta.csv').open('w',encoding='utf-8',newline='') as file:
        writer=csv.writer(file);writer.writerow(['porta','ativo_6passes','ativo_8passes','casado_6passes','casado_8passes'])
        for i,name in enumerate(after['ordem_portas']):writer.writerow([name,before['VSWR_ativo'][i],after['VSWR_ativo'][i],before['VSWR_casado'][i],after['VSWR_casado'][i]])
    fig,axs=plt.subplots(1,2,figsize=(11,4.2))
    axs[0].plot([p['passe'] for p in h[1:]],[p['delta_s'] for p in h[1:]],'o-',color='#1668ad')
    axs[0].axhline(.05,color='#bd2c2c',ls='--',label='Alvo 0,05');axs[0].set(ylabel='Delta S',xlabel='Passe total',title='Convergencia da mesma malha');axs[0].legend()
    axs[1].plot([p['passe'] for p in h],[p['campos_dBi']['P2M19_Campo_00'] for p in h],'o-',color='#1668ad')
    axs[1].axhline(19,color='#bd2c2c',ls='--',label='Meta 19 dBi');axs[1].set(ylabel='Ganho frontal realizado total (dBi)',xlabel='Passe total',title='Fontes iguais e em fase');axs[1].legend()
    for ax in axs: ax.axvspan(6.5,8.2,color='#1b9e77',alpha=.12);ax.set_xticks(range(1,9));ax.grid(alpha=.25)
    fig.suptitle('P2M19: 72 mm / refletor 146 mm — 5,17 GHz — passes 7 e 8 adicionais')
    fig.tight_layout();fig.savefig(ROOT/'historico_convergencia.png',dpi=175);plt.close(fig)
    last=rows[1];status='Convergencia S atendida' if after['convergiu'] else 'PRELIMINAR — NAO CONVERGIDO'
    lines=['# P2M19 — continuação da malha: colunas 72 mm, refletor 146 mm','',f'**{status}.** Executados exatamente os passes **7 e 8**, preservando os seis anteriores. ΔS final **{after["delta_s"]:.8f}**, alvo **0,05**; passes consecutivos atendidos: {after["consecutivos"]}.',
      '', '5,17 GHz, 14 núcleos, sem sweep. Oito placas C12, 16 níveis × duas colunas, 32 radiadores, 16 entradas iguais de 0,0625 W / 0°, total 1 W. Mesma geometria, materiais, fronteiras, portas, definições de malha e nove monitores de campo; alterados somente os limites mínimo/máximo para oito passes.',
      '', '| Resultado | 6 passes | 8 passes |','|---|---:|---:|']
    labels=[('Ganho frontal realizado total (dBi)','ganho_dBi'),('Abertura horizontal (°)','H_graus'),('Abertura vertical (°)','V_graus'),('Máximo H (°)','pico_H_graus'),('Máximo V (°)','pico_V_graus'),('VSWR ativo mínimo','VSWR_ativo_min'),('VSWR ativo máximo','VSWR_ativo_max'),('VSWR máximo com demais entradas casadas','VSWR_casado_max'),('Maior lóbulo secundário H (dB)','SLL_H_dB'),('Maior lóbulo secundário V (dB)','SLL_V_dB'),('ΔS','delta_s')]
    lines.extend(f'| {label} | {rows[0][key]:.6f} | {rows[1][key]:.6f} |' for label,key in labels)
    power=after['balanco_potencia']
    lines+=['',f'Potências: incidente {power["incidente_W"]:.6f} W, refletida {power["refletida_W"]:.6f} W, aceita {power["aceita_W"]:.6f} W, radiada {power["radiada_W"]:.6f} W e dissipada {power["dissipada_W"]:.6f} W. [VSWR individual das 16 entradas](vswr_por_porta.csv).']
    lines+=['',f'A variação de ganho entre seis e oito passes foi {delta["ganho_dBi"]:+.6f} dB. A meta numérica de 19 dBi é {"atendida" if last["ganho_dBi"]>=19 else "não atendida"}. Convergência S: {after["convergiu"]}; estabilidade das nove sondas (0,1 dB em dois passes): {after["estavel_nove_sondas"]}; validação numérica conjunta: {after["validado_numericamente"]}. Resultado não convergido não é aprovação, mesmo quando supera 19 dBi.',
      '', 'As aberturas são de meia potência do lóbulo principal. Picos refinados em grade de 0,05° com interpolação parabólica local; lóbulos secundários avaliados no hemisfério frontal, em relação ao pico de cada corte. O zero corresponde à normal frontal do refletor.',
      '',f'Balanço de potência válido: {after["balanco_potencia_valido"]}; reparos Major/Minor: {after["major"]}/{after["minor"]}. Maior valor singular da matriz S: {after["maior_singular"]:.8f}; erro de reciprocidade {after["reciprocidade"]:.3e}; recomposição dos campos {max(after["recomposicao"].values()):.3e}.',
      '', 'Inclui acoplamento e perdas dos divisores impressos, RO4350B de núcleo 0,76 mm, cobre 35 µm e ENIG nominal. Refletor 146 × 776 × 2 mm, passo vertical 48 mm e altura de PCB 14,949 mm. Exclui rede externa de distribuição, cabos em 3D, conectores N, radome e apoios plásticos. É ganho total coerente, não qualificação por entrada MIMO. Nenhuma banda foi simulada nesta etapa.',
      '', '![Diagramas polares E/Emax](polar_HV.png)','', '![Comparação dos diagramas](comparacao_diagramas.png)','', '![Casamento das 16 entradas](acoplamento_vswr.png)','', '![Histórico de adaptação](historico_convergencia.png)',
      '', '## Histórico','', '| Passe | Tetraedros | ΔS | G frontal (dBi) |','|---:|---:|---:|---:|']
    for p in h:
        ds='—' if p['delta_s'] is None else f'{p["delta_s"]:.8f}'
        lines.append(f'| {p["passe"]} | {p["tetraedros"]} | {ds} | {p["campos_dBi"]["P2M19_Campo_00"]:.6f} |')
    lines+=['',f'[HFSS]({cfg["native"]}) · [FreeCAD EM]({cfg["cad_native"]}) · [S16](centro.s16p) · [Resultados detalhados](resultado.json) · [Prova da continuidade](evidencias/continuidade_final.json).',
      '', 'O basename e o design HFSS conservam o nome R04 para reconhecer a malha copiada; a pasta e a configuração identificam a continuação R05. O original R04 permanece intacto. Malhas e campos nativos restauráveis ficam apenas na pasta local de trabalho; o Git contém nativo, campos distantes e evidências, sem `.aedtresults`, malhas, campos volumétricos ou locks.',
      '', 'Acompanhamento desta execução encerrado após os oito passes e a revisão. Não há novos passes, sweep, otimização geométrica ou agendamento recorrente ativos.']
    (ROOT/'RELATORIO.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    if not pack:
        print(json.dumps(dict(casos=rows,diferencas=delta,continuidade=ev),indent=2));return
    review=read(ROOT/'revisao_visual.json');assert review['revisado']
    imgs=['polar_HV.png','comparacao_diagramas.png','acoplamento_vswr.png','historico_convergencia.png']
    for name in imgs: assert review['sha256'][name]==sha(ROOT/name)
    OUT.mkdir(parents=True,exist_ok=True);manifest=[]
    names=[cfg['native'],cfg['cad_native'],'configuracao.json','resultado.json','qualificacao.json','centro.s16p','convergencia.txt','mensagens.json','ordem_fontes.json','HFSS_14nucleos.acf','malha.json','historico_passes.json','recursos_matriz.json','solver_efetivo.json','potencia.json','hfss_validacao.json','geometria_importada.json','RELATORIO.md','pipeline.json','analise_exitcode.json','revisao_visual.json','comparacao_6_8.json']+imgs
    names += [p.relative_to(ROOT).as_posix() for p in ROOT.glob('*.csv')]
    names += [p.relative_to(ROOT).as_posix() for p in (ROOT/'scripts').iterdir() if p.suffix in ['.py','.ps1']]
    names += [p.relative_to(ROOT).as_posix() for p in (ROOT/'evidencias').iterdir() if p.suffix in ['.txt','.json'] and p.name!='copia_resultados_local.json']
    names += [p.relative_to(ROOT).as_posix() for p in (ROOT/'cad').glob('*.json')]
    for name in sorted(set(names)):
        assert not any(x in name.lower() for x in ['.aedtresults','.g3derr','.lock','.ngmesh','.profile','.fld'])
        target=OUT/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
        assert sha(target)==sha(ROOT/name)
        manifest.append(dict(arquivo=name,origem=str(ROOT/name),bytes=target.stat().st_size,sha256=sha(target)))
    shutil.copy2(ROOT/'RELATORIO.md',OUT/'README.md');manifest.append(dict(arquivo='README.md',origem=str(ROOT/'RELATORIO.md'),bytes=(OUT/'README.md').stat().st_size,sha256=sha(OUT/'README.md')))
    save(OUT/'manifesto.json',manifest)
    print(json.dumps(dict(arquivos=len(manifest),bytes=sum(x['bytes'] for x in manifest),pacote=str(OUT)),indent=2))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--empacotar',action='store_true');main(parser.parse_args().empacotar)
