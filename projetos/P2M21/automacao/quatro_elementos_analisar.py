"""Audita e relata o unico ensaio de quatro elementos; nunca inicia solver."""
from pathlib import Path
import csv,hashlib,json,shutil,re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import divisor_variantes_comparar as compare

REPO=Path(__file__).resolve().parents[3]
ROOT=Path('D:/dev/EMBRAER/P2M21/R10_Quatro_Verticais')
DEST=REPO/'projetos/P2M21/quatro_elementos_hfss'


def main():
    state=json.loads((ROOT/'qualificacao.json').read_text(encoding='utf-8-sig'))
    assert state['estado'] in ['SOLVE_EXPORTADO_AGUARDA_AUDITORIA','ANALISE_CONCLUIDA'],state
    result,curves=compare.assess(ROOT)
    # O estudo R09 usava "validado" para a meta especifica de zero grau.
    # Nesta etapa separam-se resultado, convergencia e checagens fisicas.
    result.pop('validado',None)
    result.update(frequencia_GHz=5.17,entradas=['A','B'],potencia_incidente_total_W=1.,
        potencia_por_entrada_W=.5,fase_por_entrada_graus=0.,gui=False,
        radiadores=4,divisores_1x4=2,cabos_fisicos_com_perdas=True,comprimento_por_cabo_mm=50.,
        grade_angular_graus=.25,definicao_H='Phi=90 graus; plano YZ',definicao_V='Phi=0 graus; plano XZ',
        direcao_frontal='+Z; Theta=0 graus')
    consistency=[]
    for axis in 'HV':
        with (ROOT/('AB_'+axis+'.csv')).open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
        assert len(rows)==1441 and {float(r['Freq [GHz]']) for r in rows}=={5.17}
        assert {float(r['Phi [deg]']) for r in rows}=={90 if axis=='H' else 0}
        z=next(r for r in rows if abs(float(r['Theta [deg]']))<1e-12)
        gr,ga,di=[float(z[c]) for c in ['dB(RealizedGainTotal) []','dB(GainTotal) []','dB(DirTotal) []']]
        accepted=10**((gr-ga)/10)
        effrad=10**((ga-di)/10)
        efftotal=10**((gr-di)/10)
        consistency.append(dict(corte=axis,ganho_frontal_dBi=gr,diretividade_frontal_dBi=di,
            potencia_aceita_por_razao_ganhos_W=accepted,eficiencia_radiacao=effrad,
            eficiencia_total=efftotal,potencia_radiada_W=efftotal,
            erro_aceita_vs_S_W=abs(accepted-result['potencia_aceita_W'])))
        assert abs(gr-result['cortes'][axis]['ganho_frontal_dBi'])<1e-8
    warnings=[]
    if not result['passivo']:warnings.append('Matriz S excede limite de passividade.')
    if result['major']:warnings.append('Malha com reparos Major; resultado requer revisao.')
    if result['residuo_reciprocidade']>1e-3:warnings.append('Residuo de reciprocidade acima de 0,001.')
    if any(x['eficiencia_radiacao']>1.005 or x['erro_aceita_vs_S_W']>.005 for x in consistency):
        warnings.append('Balanço de potência requer revisão; não validar apenas por DeltaS.')
    result['balanco_potencia']=consistency
    result['ressalvas_fisicas']=warnings
    result['checagens_fisicas_aprovadas']=not warnings
    result['resultado_preliminar']=not result['convergiu'] or bool(warnings)
    result['nota_convergencia']='DeltaS entre passes; nao e limite rigoroso do erro fisico. S-convergencia nao comprova independencia de malha do diagrama.'
    (ROOT/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'comparacao_AB.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    conv=(ROOT/'convergencia.txt').read_text()
    passes=[]
    for line in conv.splitlines():
        m=re.match(r'\s*(\d+)\|\s*(\d+)\|\s*([^|]+)\|',line)
        if m:passes.append(dict(passe=int(m[1]),tetraedros=int(m[2]),delta_s=None if m[3].strip()=='N/A' else float(m[3])))
    assert len(passes)==result['passes']<=6
    (ROOT/'historico_passes.json').write_text(json.dumps(passes,indent=2)+'\n',encoding='utf-8')
    profile=next(ROOT.rglob('*.profile')).read_text(errors='replace')
    compact=[line.strip() for line in profile.splitlines() if "ProfileItem('Matrix Solve'" in line or "ProfileItem('Machine'" in line]
    (ROOT/'perfil_14_nucleos.txt').write_text('\n'.join(compact)+'\n',encoding='utf-8')

    h,v=result['cortes']['H'],result['cortes']['V']
    label='PRELIMINAR — não convergido' if not result['convergiu'] else 'Convergência ΔS atendida'
    if warnings:label+=' | ressalvas físicas'
    fig,axs=plt.subplots(1,2,figsize=(11,5.8),sharey=True)
    for ax,axis,color in zip(axs,'HV',['#176a9b','#d17b26']):
        theta,gain=curves[axis];c=result['cortes'][axis]
        ax.plot(theta,gain,color=color,lw=1.8)
        ax.axvline(0,c='#555555',lw=.7)
        ax.axvline(c['pico_graus'],c=color,ls=':',lw=1)
        ax.scatter([c['pico_graus']],[c['ganho_pico_dBi']],c=color,s=25)
        ax.set(xlim=(-90,90),ylim=(max(-30,min(h['ganho_pico_dBi'],v['ganho_pico_dBi'])-35),max(h['ganho_pico_dBi'],v['ganho_pico_dBi'])+2),
            xlabel='Ângulo (graus)',title=f"{axis}: máximo {c['pico_graus']:+.2f}° | abertura {c['abertura_graus']:.2f}°")
        ax.grid(alpha=.25)
    axs[0].set_ylabel('Ganho realizado total (dBi)')
    fig.suptitle('Quatro elementos + divisores 1:4 + cabos — 5,17 GHz\nA = B = 0,5 W / 0° | '+label,fontsize=13)
    fig.text(.5,.035,f"G frontal {h['ganho_frontal_dBi']:.3f} dBi | VSWR ativo A/B {result['VSWR_ativo'][0]:.3f}/{result['VSWR_ativo'][1]:.3f} | ΔS {result['delta_s']:.6f} | {result['passes']} passes",ha='center',fontsize=10)
    fig.tight_layout(rect=(0,.08,1,.88));fig.savefig(ROOT/'diagramas_HV.png',dpi=180);plt.close(fig)

    fig,axs=plt.subplots(1,2,figsize=(11,7),subplot_kw={'projection':'polar'})
    for ax,axis,color in zip(axs,'HV',['#176a9b','#d17b26']):
        theta,gain=curves[axis];c=result['cortes'][axis]
        ax.plot(np.deg2rad(theta),10**((gain-gain.max())/20),color=color,lw=1.8)
        ax.set_theta_zero_location('N');ax.set_theta_direction(-1)
        ax.set_ylim(0,1.05);ax.set_rticks([.25,.5,.75,1]);ax.set_rlabel_position(75);ax.tick_params(axis='y',labelsize=9)
        ax.set_thetagrids(np.arange(0,360,30),['0°','30°','60°','90°','120°','150°','180°','−150°','−120°','−90°','−60°','−30°'])
        ax.set_title(f"{axis}: máximo {c['pico_graus']:+.2f}° | abertura {c['abertura_graus']:.2f}°",pad=23,fontsize=11)
        ax.grid(alpha=.3)
    fig.suptitle('Quatro elementos — polar E/Emax — 5,17 GHz\nDuas entradas iguais e em fase | '+label,fontsize=13)
    fig.text(.5,.04,f"14 núcleos | {result['passes']} passes | ΔS final = {result['delta_s']:.6f}",ha='center',fontsize=11)
    fig.text(.5,.012,'Cada corte normalizado ao próprio máximo; cabos físicos de 50 mm incluídos.',ha='center',fontsize=9)
    fig.subplots_adjust(top=.75,bottom=.17,wspace=.30)
    fig.savefig(ROOT/'polar_HV.png',dpi=180);fig.savefig(ROOT/'polar_HV.pdf');plt.close(fig)

    fig,ax=plt.subplots(figsize=(7,3.8))
    ax.semilogy([p['passe'] for p in passes if p['delta_s'] is not None],[p['delta_s'] for p in passes if p['delta_s'] is not None],'o-',color='#176a9b')
    ax.axhline(.04,color='#b63b30',ls='--',label='Alvo ΔS = 0,04')
    ax.set(xlabel='Passe adaptativo',ylabel='Máximo |ΔS|',title='HFSS — histórico real de convergência')
    ax.set_xticks([p['passe'] for p in passes]);ax.grid(alpha=.25);ax.legend()
    fig.tight_layout();fig.savefig(ROOT/'convergencia.png',dpi=180);plt.close(fig)

    with (ROOT/'resumo.csv').open('w',encoding='utf-8',newline='') as f:
        fields=['frequencia_GHz','ganho_frontal_dBi','pico_H_graus','pico_V_graus','abertura_H_graus','abertura_V_graus','VSWR_ativo_A','VSWR_ativo_B','VSWR_casado_A','VSWR_casado_B','delta_s','passes','convergiu']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerow(dict(zip(fields,[5.17,h['ganho_frontal_dBi'],h['pico_graus'],v['pico_graus'],h['abertura_graus'],v['abertura_graus'],*result['VSWR_ativo'],*result['VSWR_casado'],result['delta_s'],result['passes'],result['convergiu']])))
    history='\n'.join(f"| {p['passe']} | {p['tetraedros']} | {p['delta_s'] if p['delta_s'] is not None else '—'} |" for p in passes)
    md=f'''# Quatro elementos — ensaio HFSS em 5,17 GHz

Ensaio de 9/11/2026: **{label}**. {result['passes']} passes, ΔS final **{result['delta_s']:.6f}** para alvo 0,04; {result['passes_consecutivos']} de {result['consecutivos_exigidos']} passes consecutivos exigidos. O limite de seis passes foi respeitado. Nenhum sweep foi executado.

| Resultado | A+B, entradas iguais e em fase |
|---|---:|
| Ganho realizado total frontal, θ = 0° | **{h['ganho_frontal_dBi']:.4f} dBi** |
| Máximo do corte horizontal | **{h['pico_graus']:+.2f}°**, {h['ganho_pico_dBi']:.4f} dBi |
| Máximo do corte vertical | **{v['pico_graus']:+.2f}°**, {v['ganho_pico_dBi']:.4f} dBi |
| Abertura horizontal a −3 dB | {h['abertura_graus']:.3f}° |
| Abertura vertical a −3 dB | {v['abertura_graus']:.3f}° |
| VSWR ativo A / B | **{result['VSWR_ativo'][0]:.4f} / {result['VSWR_ativo'][1]:.4f}** |
| VSWR A / B com a outra entrada casada em 50 Ω | {result['VSWR_casado'][0]:.4f} / {result['VSWR_casado'][1]:.4f} |

## Modelo e execução

Quatro radiadores verticais em X = −72, −24, +24 e +72 mm; passo 48 mm, PCB contínua 70 × 178,8 mm. Duas árvores impressas 1:4, uma por polarização, cada uma composta por uma raiz 1:2 e dois estágios locais 1:2. Os ajustes locais da v05 foram preservados. As quatro interfaces coaxiais intermediárias foram substituídas por junções impressas com retorno contínuo.

Dois cabos físicos de 50 mm, retos e perpendiculares à placa, conectados em X = +2,509 mm, Y = ±32 mm. Incluídos pinos, blindagens, PTFE e soldas; as portas ficam nas extremidades dos cabos, Z = −33,39 mm. Refletor de alumínio de 2 mm, face 194,8 × 90 mm. Face inferior do núcleo em Z = 16,61 mm. Sem apoios plásticos ou conectores N.

RO4350B de 0,76 mm, εr = 3,66 e tanδ = 0,0037; cobre físico de 35 µm e ENIG nominal da v05. Os cabos incluem as perdas nominais do condutor e do PTFE (εr = 2,03636, tanδ = 0,00027683). NiP de 4,5 µm com condutividade nominal de 1,5 MS/m e ouro de 0,0254 µm, aplicados às faces expostas por impedância em camadas, sem shell elements. Esses parâmetros são hipóteses do modelo.

AEDT 2024 R2 executado com `-ng`, sem GUI. **14 núcleos** confirmados nos {len(result['nucleos_por_passe'])} registros de solução de matriz. Classic com resolução automática 5, sem refinamentos locais, sem MeshLink e sem LambdaRefine inicial; adaptação de 20% durante o solve, base mista e solver iterativo com residual 1e−5. Somente o setup Centro em 5,17 GHz. A região aberta foi dimensionada com a referência conservadora de 5,09 GHz, o que não constitui solução nessa frequência.

Ambas as portas foram alimentadas com **0,5 W / 0°**, total de 1 W. Frente = +Z, θ = 0°. H: φ = 90°, plano YZ; V: φ = 0°, plano XZ. Grade angular de 0,25°. Os máximos reportados são amostras dos cortes no hemisfério frontal, não um máximo 3D otimizado.

## Auditorias

CAD: 42 sólidos válidos, 73 pares com sobreposição de caixas examinados, sem interseções volumétricas indevidas. Malha: {result['major']} corpos com reparo Major e {result['minor']} com Minor. Matriz S em 50 Ω: maior valor singular {result['max_singular']:.8f}; resíduo de reciprocidade |S−Sᵀ| máximo {result['residuo_reciprocidade']:.8g}. A recomposição complexa dos campos A/B reproduziu o caso conjunto com erro relativo máximo {max(result['erros_recomposicao'].values()):.3g}.

Potência aceita com ambas as entradas ativas: {result['potencia_aceita_W']:.6f} W. Eficiência de radiação derivada das grandezas HFSS: {100*consistency[0]['eficiencia_radiacao']:.3f}%; eficiência total: {100*consistency[0]['eficiencia_total']:.3f}%. Diferença máxima entre potência aceita por S e pela razão ganho realizado/ganho: {max(x['erro_aceita_vs_S_W'] for x in consistency):.3g} W.

Ressalvas físicas: {('; '.join(warnings)) if warnings else 'nenhuma falha identificada nos critérios numéricos acima.'}

| Passe | Tetraedros | Máximo ΔS |
|---:|---:|---:|
{history}

O critério ΔS compara soluções adaptativas; não é um limite rigoroso do erro físico do ganho ou do diagrama. Não foi executado um estudo independente de estabilidade de malha. Estes resultados não qualificam a banda completa nem o painel 16×2; o ganho é total com as duas entradas coerentes, não ganho MIMO por entrada.

![Cortes H/V](diagramas_HV.png)

![Polares E/Emax](polar_HV.png)

![Histórico adaptativo](convergencia.png)

## Arquivos

[Projeto HFSS](P2M21_4_elementos.aedt), [CAD FreeCAD](4_elementos.FCStd), [Touchstone](centro.s2p), [resumo CSV](resumo.csv), [auditoria completa](resultado.json) e [convergência HFSS](convergencia.txt). O nativo salvo mantém ambas as fontes em 0,5 W / 0°. As soluções FEM completas permanecem em `D:/dev/EMBRAER/P2M21/R10_Quatro_Verticais`; o repositório exclui malhas, resultados volumétricos, locks e temporários. Sem a pasta de resultados, o AEDT preserva o modelo, mas exige novo solve para restaurar os campos nativos.

Geometria de origem: [planejamento dos quatro elementos](../planejamento/4_elementos/README.md). Scripts em `../automacao/quatro_elementos_*.py`; os geradores específicos CAD/HFSS estão nesta pasta. Não houve novo ensaio de otimização, nova cotação ou envio de email.
'''
    (ROOT/'README.md').write_text(md,encoding='utf-8')
    state.update(estado='ANALISE_CONCLUIDA',convergiu=result['convergiu'],resultado_preliminar=result['resultado_preliminar'])
    (ROOT/'qualificacao.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    DEST.mkdir(parents=True,exist_ok=True)
    files=['P2M21_4_elementos.aedt','4_elementos.FCStd','README.md','configuracao.json','geometria.json','HFSS_14nucleos.acf',
        'qualificacao.json','hfss_validacao.json','execucao_headless.json','resultado.json','comparacao_AB.json','malha.json','historico_passes.json',
        'convergencia.txt','centro.s2p','mensagens.json','resumo.csv','perfil_14_nucleos.txt',
        'diagramas_HV.png','polar_HV.png','polar_HV.pdf','convergencia.png','criar_cad.py','criar_hfss.py',
        'cad/intersecoes.json','cad/portas.json','cad/folhas_solidas.json','cad/manifesto.json','cad/enig_hfss.json']
    files += [mode+'_'+axis+'.csv' for mode in ['AB','A','B'] for axis in 'HV']
    manifest=[]
    for name in files:
        src=ROOT/name;dst=DEST/name;dst.parent.mkdir(parents=True,exist_ok=True)
        data=src.read_bytes()
        if src.suffix in ('.py','.md'):data=data.replace(b'\r\n',b'\n')
        dst.write_bytes(data)
        manifest.append(dict(arquivo=name,sha256=hashlib.sha256(data).hexdigest(),origem_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),bytes=len(data)))
    (DEST/'manifesto.json').write_text(json.dumps(dict(arquivos=manifest,total_bytes=sum(x['bytes'] for x in manifest)),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['passes','delta_s','convergiu','VSWR_ativo','VSWR_casado','cortes','ressalvas_fisicas']},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
