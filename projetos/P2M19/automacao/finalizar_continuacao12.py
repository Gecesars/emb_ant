"""Auditoria adicional, comparacao 10/12 passes e pacote sem malhas da R07."""
from pathlib import Path
import json,hashlib,shutil,argparse,re,csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from estabilidade_continuacao12 import main as estabilidade
ROOT=Path('D:/dev/EMBRAER/P2M19/R07_72mm_ref146_12passes')
REPO=Path(__file__).resolve().parents[3]
OUT=REPO/'projetos/P2M19/continuacao_72mm_ref146_12passes'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main(pack=False):
    cfg=read(ROOT/'configuracao.json');source=Path(cfg['referencia_comparacao'])
    before=read(source/'resultado.json');after=read(ROOT/'resultado.json')
    h0=read(source/'historico_passes.json')['historico'];h=read(ROOT/'historico_passes.json')['historico']
    assert len(h0)==10 and len(h)==12 and h[:10]==h0,'Historico anterior modificado'
    assert after['passes']==12 and after['max_passes']==12 and after['nucleos']==14
    assert after['fisica_ok'] and after['balanco_potencia_valido'] and after['major']==0
    assert after['cache_confere_fontes_finais'],'Campos exportados devem coincidir com o passe 12'
    assert sha(source/cfg['native'])==cfg['continuacao']['nativo_referencia_sha256'],'Referencia foi alterada'
    old=(source/cfg['native']).read_text(encoding='latin1');new=(ROOT/cfg['native']).read_text(encoding='latin1')
    def block(raw,n): return raw.split("$begin '"+n+"'",1)[1].split("$end '"+n+"'",1)[0]
    names=['GeometryCore','Materials','BoundarySetup','MeshSetup']
    assert all(block(old,n)==block(new,n) for n in names)
    # Exportar campos com diferentes fontes incrementa VersionID/NextUniqueID
    # das esferas. Conferir todo o restante, incluindo grades e coordenadas.
    def rad_physics(text):return re.sub(r'(?m)^\s*(?:VersionID|NextUniqueID)=\d+\s*$', '',block(text,'RadField'))
    assert rad_physics(old)==rad_physics(new)
    expected=block(old,'AnalysisSetup').replace('MaximumPasses=10','MaximumPasses=12').replace('MinimumPasses=10','MinimumPasses=12')
    assert block(new,'AnalysisSetup')==expected
    oldtraces=re.findall(r'TraceID=(\d+)',block(old,'AnalysisSetup'))
    assert len(oldtraces)==9 and oldtraces==re.findall(r'TraceID=(\d+)',block(new,'AnalysisSetup'))
    ev=dict(passes_1_a_10_identicos=True,passes_adicionais=[11,12],historico_inicial_tetraedros=1163077,
        referencia_nativa_sha256=sha(source/cfg['native']),nativo_final_sha256=sha(ROOT/cfg['native']),
        geometria_materiais_portas_malha_campos_iguais=True,somente_min_max_setup_alterados=True,
        trace_ids_preservados=oldtraces,sem_sweep=not cfg['sweep'],
        radfield_definicoes_iguais=True,radfield_metadados_atualizados=['VersionID','NextUniqueID'])
    save(ROOT/'evidencias/continuidade_final.json',ev)
    stability=estabilidade()
    rows=[]
    for label,r in [('R06: dez passes',before),('R07: doze passes',after)]:
        rows.append(dict(versao=label,passes=r['passes'],delta_s=r['delta_s'],convergiu=r['convergiu'],
            ganho_dBi=r['cortes']['H']['ganho_frontal_dBi'],
            H_graus=r['cortes_finos']['H']['abertura_graus'],V_graus=r['cortes_finos']['V']['abertura_graus'],
            pico_H_graus=r['cortes_finos']['H']['pico_interpolado_graus'],pico_V_graus=r['cortes_finos']['V']['pico_interpolado_graus'],
            VSWR_ativo_min=min(r['VSWR_ativo']),VSWR_ativo_max=max(r['VSWR_ativo']),VSWR_casado_max=max(r['VSWR_casado']),
            SLL_H_dB=r['cortes']['H']['SLL']['nivel_dB'],SLL_V_dB=r['cortes']['V']['SLL']['nivel_dB']))
    delta={k:rows[1][k]-rows[0][k] for k in ['ganho_dBi','H_graus','V_graus','VSWR_ativo_max','SLL_H_dB','SLL_V_dB']}
    save(ROOT/'comparacao_10_12.json',dict(casos=rows,diferencas=delta))
    assert before['ordem_portas']==after['ordem_portas']
    with (ROOT/'vswr_por_porta.csv').open('w',encoding='utf-8',newline='') as file:
        writer=csv.writer(file);writer.writerow(['porta','ativo_10passes','ativo_12passes','casado_10passes','casado_12passes'])
        for i,name in enumerate(after['ordem_portas']):writer.writerow([name,before['VSWR_ativo'][i],after['VSWR_ativo'][i],before['VSWR_casado'][i],after['VSWR_casado'][i]])
    fig,axs=plt.subplots(1,2,figsize=(11,4.2))
    axs[0].plot([p['passe'] for p in h[1:]],[p['delta_s'] for p in h[1:]],'o-',color='#1668ad')
    axs[0].axhline(.05,color='#bd2c2c',ls='--',label='Alvo 0,05');axs[0].set(ylabel='Delta S',xlabel='Passe total',title='Convergencia da mesma malha');axs[0].legend()
    axs[1].plot([p['passe'] for p in h],[p['campos_dBi']['P2M19_Campo_00'] for p in h],'o-',color='#1668ad')
    axs[1].axhline(19,color='#bd2c2c',ls='--',label='Meta 19 dBi');axs[1].set(ylabel='Ganho frontal realizado total (dBi)',xlabel='Passe total',title='Fontes iguais e em fase');axs[1].legend()
    for ax in axs: ax.axvspan(10.5,12.2,color='#1b9e77',alpha=.12);ax.set_xticks(range(1,13));ax.grid(alpha=.25)
    fig.suptitle('P2M19: 72 mm / refletor 146 mm — 5,17 GHz — passes 11 e 12 adicionais')
    fig.tight_layout();fig.savefig(ROOT/'historico_convergencia.png',dpi=175);plt.close(fig)
    last=rows[1];status='Convergência S atendida' if after['convergiu'] else 'PRELIMINAR — NÃO CONVERGIDO'
    if after['convergiu'] and not after['estavel_nove_sondas']:
        status+=' — estabilidade dos campos ainda não confirmada'
    lines=['# P2M19 — continuação da malha: colunas 72 mm, refletor 146 mm','',f'**{status}.** Executados exatamente os passes **11 e 12**, preservando os dez anteriores. ΔS final **{after["delta_s"]:.8f}**, alvo **0,05**; passes consecutivos atendidos: {after["consecutivos"]}.',
      '', '5,17 GHz, 14 núcleos, sem sweep. Oito placas C12, 16 níveis × duas colunas, 32 radiadores, 16 entradas iguais de 0,0625 W / 0°, total 1 W. Mesma geometria, materiais, fronteiras, portas, definições de malha e nove monitores de campo; alterados somente os limites mínimo/máximo para onze e depois doze passes, com exportação intermediária.',
      '', '| Resultado | 10 passes | 12 passes |','|---|---:|---:|']
    labels=[('Ganho frontal realizado total (dBi)','ganho_dBi'),('Abertura horizontal (°)','H_graus'),('Abertura vertical (°)','V_graus'),('Máximo H (°)','pico_H_graus'),('Máximo V (°)','pico_V_graus'),('VSWR ativo mínimo','VSWR_ativo_min'),('VSWR ativo máximo','VSWR_ativo_max'),('VSWR máximo com demais entradas casadas','VSWR_casado_max'),('Maior lóbulo secundário H (dB)','SLL_H_dB'),('Maior lóbulo secundário V (dB)','SLL_V_dB'),('ΔS','delta_s')]
    lines.extend(f'| {label} | {rows[0][key]:.6f} | {rows[1][key]:.6f} |' for label,key in labels)
    power=after['balanco_potencia']
    lines+=['',f'Potências: incidente {power["incidente_W"]:.6f} W, refletida {power["refletida_W"]:.6f} W, aceita {power["aceita_W"]:.6f} W, radiada {power["radiada_W"]:.6f} W e dissipada {power["dissipada_W"]:.6f} W. [VSWR individual das 16 entradas](vswr_por_porta.csv).']
    yn=lambda value:'sim' if value else 'não'
    lines+=['',f'A variação de ganho entre dez e doze passes foi {delta["ganho_dBi"]:+.6f} dB. A meta numérica de 19 dBi é {"atendida" if last["ganho_dBi"]>=19 else "não atendida"}. Convergência S: {yn(after["convergiu"])}; estabilidade das nove sondas (0,1 dB em dois passes): {yn(after["estavel_nove_sondas"])}; validação numérica conjunta: {yn(after["validado_numericamente"])}. Convergência S e estabilidade do campo são verificações distintas. O monitoramento de campo não modifica a parada autorizada em doze passes.',
      '', 'As aberturas são de meia potência do lóbulo principal. Picos refinados em grade de 0,05° com interpolação parabólica local; lóbulos secundários avaliados no hemisfério frontal, em relação ao pico de cada corte. O zero corresponde à normal frontal do refletor.',
      '',f'Balanço de potência válido: {yn(after["balanco_potencia_valido"])}; reparos Major/Minor: {after["major"]}/{after["minor"]}. Maior valor singular da matriz S: {after["maior_singular"]:.8f}; erro de reciprocidade {after["reciprocidade"]:.3e}; recomposição dos campos {max(after["recomposicao"].values()):.3e}.',
      '', 'Inclui acoplamento e perdas dos divisores impressos, RO4350B de núcleo 0,76 mm, cobre 35 µm e ENIG nominal. Refletor 146 × 776 × 2 mm, passo vertical 48 mm e altura de PCB 14,949 mm. Exclui rede externa de distribuição, cabos em 3D, conectores N, radome e apoios plásticos. É ganho total coerente, não qualificação por entrada MIMO. Nenhuma banda foi simulada nesta etapa.',
      '', '![Diagramas polares E/Emax](polar_HV.png)','', '![Comparação dos diagramas](comparacao_diagramas.png)','', '![Casamento das 16 entradas](acoplamento_vswr.png)','', '![Histórico de adaptação](historico_convergencia.png)',
      '', '## Histórico','', '| Passe | Tetraedros | ΔS | G frontal (dBi) |','|---:|---:|---:|---:|']
    for p in h:
        ds='—' if p['delta_s'] is None else f'{p["delta_s"]:.8f}'
        lines.append(f'| {p["passe"]} | {p["tetraedros"]} | {ds} | {p["campos_dBi"]["P2M19_Campo_00"]:.6f} |')
    lines+=['','## Estabilidade entre passes consecutivos','',
      'O passe 11 teve seus campos completos exportados antes de continuar a mesma malha até o passe 12. Não houve interpolação entre passes.',
      '', '| Passe | G frontal (dBi) | H (°) | V (°) | Pico H / V (°) | VSWR ativo máximo |',
      '|---:|---:|---:|---:|---:|---:|']
    for row in stability['casos']:
        lines.append(f'| {row["passe"]} | {row["ganho_frontal_dBi"]:.6f} | {row["H_graus"]:.6f} | {row["V_graus"]:.6f} | {row["pico_H_graus"]:+.5f} / {row["pico_V_graus"]:+.5f} | {row["VSWR_ativo_max"]:.6f} |')
    lines+=['','| Comparação | ΔG (dB) | ΔH (°) | ΔV (°) | Maior diferença H / V em E/Emax |','|---|---:|---:|---:|---:|']
    for item in stability['comparacoes']:
        d=item['diferencas'];m=item['diagramas']
        lines.append(f'| {item["de"]} → {item["para"]} | {d["ganho_frontal_dBi"]:+.6f} | {d["H_graus"]:+.6f} | {d["V_graus"]:+.6f} | {m["H"]["max_diferenca_E_Emax"]:.6f} / {m["V"]["max_diferenca_E_Emax"]:.6f} |')
    last_change=stability['comparacoes'][1]
    probe=max(stability['sondas_monitoradas'],key=lambda item:abs(item['delta_11_12_dB']))
    relative=probe['ganho_dBi_10_11_12'][-1]-last['ganho_dBi']
    lines+=['',f'Do passe 11 para o 12, a maior diferença absoluta de amplitude normalizada E/Emax foi {last_change["diagramas"]["H"]["max_diferenca_E_Emax"]:.6f} em H e {last_change["diagramas"]["V"]["max_diferenca_E_Emax"]:.6f} em V. O maior lóbulo secundário mudou {last_change["diferencas"]["SLL_H_dB"]:+.6f} dB em H e {last_change["diferencas"]["SLL_V_dB"]:+.6f} dB em V.',
      '',f'O ganho e as aberturas do lóbulo principal apresentaram pequenas mudanças quantificadas na tabela. A estabilidade completa de 0,1 dB nas nove sondas por dois passes não foi atendida. A maior variação no último passe foi {abs(probe["delta_11_12_dB"]):.6f} dB em Theta={probe["theta_graus"]:+g}° / Phi={probe["phi_graus"]:g}°, direção {relative:.3f} dB abaixo do ganho frontal. Não foram autorizados nem executados passes além de 12.']
    lines+=['',stability['nota'],'','![Estabilidade H/V dos três passes](estabilidade_HV_10_11_12.png)',
      '', '[Dados completos de estabilidade](estabilidade_10_11_12.json) · [Tabela dos três passes](estabilidade_10_11_12.csv) · [Resultados intermediários do passe 11](passe11/resultado.json).',
      '',f'[HFSS]({cfg["native"]}) · [FreeCAD EM]({cfg["cad_native"]}) · [S16](centro.s16p) · [Resultados detalhados](resultado.json) · [Prova da continuidade](evidencias/continuidade_final.json).',
      '', 'O basename e o design HFSS conservam o nome R04 para reconhecer a malha copiada; a pasta e a configuração identificam a continuação R07. A referência de dez passes R06 permanece intacta. Malhas e campos nativos restauráveis ficam apenas na pasta local de trabalho; o Git contém nativo, campos distantes e evidências, sem `.aedtresults`, malhas, campos volumétricos ou locks.',
      '', 'Após exportar o passe 11, o controlador encontrou um erro de codificação ao gravar o JSON de configuração. O checkpoint RF ficou preservado; a recuperação gravou os metadados em Python 3 e conferiu o hash nativo usando bytes via .NET. O primeiro teste de recuperação parou nessa conferência, antes de qualquer cálculo. A retomada seguinte executou somente o passe 12. Nenhum passe RF foi repetido; a cadeia dos doze passes e seus tetraedros foi conferida. [Registro da recuperação](evidencias/recuperacao_codificacao.json).',
      '', 'Acompanhamento desta execução encerrado após os doze passes e a revisão. Não há novos passes, sweep, otimização geométrica ou agendamento recorrente ativos.']
    (ROOT/'RELATORIO.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    if not pack:
        print(json.dumps(dict(casos=rows,diferencas=delta,continuidade=ev),indent=2));return
    review=read(ROOT/'revisao_visual.json');assert review['revisado']
    imgs=['polar_HV.png','comparacao_diagramas.png','acoplamento_vswr.png','historico_convergencia.png','estabilidade_HV_10_11_12.png']
    for name in imgs: assert review['sha256'][name]==sha(ROOT/name)
    OUT.mkdir(parents=True,exist_ok=True);manifest=[]
    names=[cfg['native'],cfg['cad_native'],'configuracao.json','resultado.json','qualificacao.json','centro.s16p','convergencia.txt','mensagens.json','ordem_fontes.json','HFSS_14nucleos.acf','malha.json','historico_passes.json','recursos_matriz.json','solver_efetivo.json','potencia.json','hfss_validacao.json','geometria_importada.json','RELATORIO.md','pipeline.json','analise_exitcode.json','revisao_visual.json','comparacao_10_12.json']+imgs
    names += [p.relative_to(ROOT).as_posix() for p in ROOT.glob('*.csv')]
    names += ['estabilidade_10_11_12.json']
    names += [p.relative_to(ROOT).as_posix() for p in (ROOT/'passe11').iterdir() if p.is_file() and p.suffix in ['.csv','.json','.txt','.s16p']]
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
