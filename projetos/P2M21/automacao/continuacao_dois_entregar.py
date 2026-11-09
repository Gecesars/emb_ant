"""Pacote e texto de email da continuacao6, sem enviar email nem executar solve."""
import os,json,csv,shutil,hashlib,html
from pathlib import Path
from datetime import datetime
from polares_emax import generate

root=Path(os.environ.get('P2M21_UNIFORME','D:/dev/EMBRAER/P2M21/R04_Centro_Classic'))
repo=Path(__file__).resolve().parents[3]
dest=repo/'projetos/P2M21/centro_sem_refinamento/continuacao_6_passes'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

if __name__=='__main__':
    now=read(root/'antena/auditoria_centro.json');old=read(root/'resultado_4_passes/auditoria_centro.json')
    assert now['convergencia']['passes']==now['convergencia']['max_passes']==6 and now['convergencia']['minimo']==6
    assert old['convergencia']['passes']==4 and now['n_pontos']==1
    history=read(root/'antena/historico_centro.json')['historico'];before=read(root/'resultado_4_passes/historico_centro.json')['historico']
    assert [(r['passe'],r['tetraedros'],r['delta_s']) for r in history[:4]]==[(r['passe'],r['tetraedros'],r['delta_s']) for r in before]
    row=now['pontos'][0];ref=old['pontos'][0];cfg=read(root/'configuracao.json')
    generate(root)
    comparison=dict(referencia_passes=4,passes_atual=6,ganho_diferenca_dB=row['ganho_frontal_total_realizado_dBi']-ref['ganho_frontal_total_realizado_dBi'],
      H_diferenca_graus=row['abertura_H_graus']-ref['abertura_H_graus'],V_diferenca_graus=row['abertura_V_graus']-ref['abertura_V_graus'],
      delta_s_antes=old['convergencia']['delta_s'],delta_s_depois=now['convergencia']['delta_s'],referencia_sha256=sha(root/'resultado_4_passes/auditoria_centro.json'),atual_sha256=sha(root/'antena/auditoria_centro.json'))
    write(root/'comparacao_4_6.json',comparison)
    dest.mkdir(exist_ok=True);(dest/'resultados').mkdir(exist_ok=True);(dest/'hfss').mkdir(exist_ok=True);(dest/'polares').mkdir(exist_ok=True);(dest/'evidencias').mkdir(exist_ok=True)
    for name in ['auditoria_centro.json','historico_centro.json','convergencia_centro.txt','malha_centro.json','centro.s64p','mensagens_centro.json']:
        shutil.copy2(root/'antena'/name,dest/'resultados'/name)
    for axis in 'HV':shutil.copy2(root/'antena/centro/5170'/('Uniforme_'+axis+'.csv'),dest/'resultados'/('Uniforme_'+axis+'.csv'))
    for p in (root/'polares').iterdir():
        if p.is_file():shutil.copy2(p,dest/'polares'/p.name)
    for name in ['configuracao.json','comparacao_4_6.json','resultados_centro.csv','verificacao_continuacao.json','HFSS_14nucleos.acf']:
        shutil.copy2(root/name,dest/name)
    shutil.copy2(root/'antena'/cfg['native'],dest/'hfss'/cfg['native'])
    shutil.copy2(root/'centro_6passes_aedt.log',dest/'evidencias/centro_6passes_aedt.txt')
    status='CONVERGIDO' if now['convergencia_aprovada'] else 'NÃO CONVERGIU'
    label='VERIFICAÇÕES NUMÉRICAS ATENDIDAS' if now['aprovado'] else 'PRELIMINAR / NÃO QUALIFICADO'
    metrics=[('Ganho frontal realizado total (dBi)','ganho_frontal_total_realizado_dBi'),('Abertura horizontal −3 dB (°)','abertura_H_graus'),('Abertura vertical −3 dB (°)','abertura_V_graus')]
    table='| Grandeza | Quatro passes | Seis passes |\n|---|---:|---:|\n'+''.join(f'| {label} | {ref[key]:.6f} | {row[key]:.6f} |\n' for label,key in metrics)+f'| ΔS | {old["convergencia"]["delta_s"]:.9f} | {now["convergencia"]["delta_s"]:.9f} |\n'
    issue_text='\n'.join('- '+i['verificacao']+': `'+json.dumps(i['detalhes'],ensure_ascii=False)+'`.' for i in now['falhas_qualidade']) or 'Nenhuma reprovação nos testes de qualidade implementados.'
    body=f'''# P2M21 — continuação de quatro para seis passes

**{label}. {status}; ΔS final {now['convergencia']['delta_s']:.9f}, referência 0,04.** Foram executados apenas os passes adicionais 5 e 6, preservando os quatro anteriores. 5,17 GHz, 14 núcleos nos passes 3–6, sem sweep. Nenhuma mudança de geometria, materiais, alimentação ou controles iniciais de malha; o setup mudou somente mínimo/máximo de passes para seis.

{table}
O ganho observado {'supera' if row['ganho_frontal_total_realizado_dBi']>=21 else 'não supera'} 21 dBi. O valor só constitui um resultado numericamente qualificado quando convergência e verificações forem aprovadas; a classificação acima é a deste cálculo. As 64 portas diretas recebem 0,015625 W/0°, total 1 W incidente. Não há rede externa no modelo; não se trata de ganho MIMO por entrada.

## Diagramas polares de amplitude

Normalização por corte completo: `E/Emax = sqrt(|Eθ|² + |Eφ|²) / máximo`. A escala é amplitude linear de 0 a 1. A curva foi conferida contra `10^((G−Gmax)/20)`. A referência de −3 dB corresponde a E/Emax = 0,707946. A frente está em 0°, a grade angular tem passo de 0,25° e o diagrama vertical inclui detalhe frontal radial de 0,55 a 1. Os dois arquivos PNG são os anexos previstos do email autorizado.

![Horizontal](polares/P2M21_Horizontal_polar_E_Emax.png)

![Vertical](polares/P2M21_Vertical_polar_E_Emax.png)

## Auditoria

Malha: {now['malha_major']} reparos Major e {now['malha_minor']} Minor. Eficiência calculada: {100*row['eficiencia_radiacao']:.6f}%. Maior valor singular S: {now['max_valor_singular']:.9f}. Erro máximo de reciprocidade: {now['erro_reciprocidade']:.9g}. As inconsistências permanecem registradas; não foram simetrizadas as matrizes nem truncadas eficiências para aprovar o resultado.

{issue_text}

[CSV dos resultados](resultados_centro.csv) · [Comparação com quatro passes](comparacao_4_6.json) · [Auditoria](resultados/auditoria_centro.json) · [Convergência nativa](resultados/convergencia_centro.txt) · [HFSS](hfss/{cfg['native']})

O nativo e os dados compactos são arquivados; a malha e os campos volumétricos permanecem locais, fora do Git. O `.aedt` sozinho não restaura a solução FEM. Envio solicitado para gecesars@gmail.com, somente depois da revisão visual e numérica dos anexos finais. O recibo do envio será registrado separadamente.
'''
    (dest/'README.md').write_text(body,encoding='utf-8')
    html_rows=''.join(f'<tr><td>{html.escape(title)}</td><td>{ref[key]:.4f}</td><td>{row[key]:.4f}</td></tr>' for title,key in metrics)
    html_rows+=f'<tr><td>ΔS</td><td>{old["convergencia"]["delta_s"]:.6f}</td><td>{now["convergencia"]["delta_s"]:.6f}</td></tr>'
    mail=f'''<p>Olá,</p><p>Concluí os dois passes adicionais da P2M21, totalizando seis em 5,17 GHz, com 14 núcleos nos passes finais e sem varredura de frequência.</p><p><strong>{label}. {status}.</strong> O ΔS final é {now['convergencia']['delta_s']:.6f}, para a referência de 0,04.</p><table border="1" cellpadding="6" cellspacing="0"><tr><th>Grandeza</th><th>4 passes</th><th>6 passes</th></tr>{html_rows}</table><p>Os dois diagramas polares anexos apresentam amplitude linear E/Emax, normalizada pelo máximo de cada corte. Horizontal: φ=90°; vertical: φ=0°. Excitação: 64 portas iguais/em fase, total de 1 W incidente. Este resultado não inclui os divisores/cabos nem comprova ganho MIMO por entrada.</p><p>Auditoria: {now['malha_major']} reparos graves de malha, eficiência calculada de {100*row['eficiencia_radiacao']:.4f}% e erro de reciprocidade {now['erro_reciprocidade']:.6g}. As limitações e o estado de convergência acompanham os resultados, sem declarar validação quando as verificações não são atendidas.</p><p>Arquivos e relatório: <a href="https://github.com/Gecesars/emb_ant/tree/main/projetos/P2M21/centro_sem_refinamento/continuacao_6_passes">repositório emb_ant</a>.</p>'''
    (root/'email_polares_6passes.html').write_text(mail,encoding='utf-8')
    state=dict(estado='SEIS_PASSES_REVISAR_ANEXOS_E_ENVIAR',instante=datetime.now().astimezone().isoformat(),passes=6,nucleos=14,frequencia_GHz=5.17,sweeps=0,aprovado=now['aprovado'],convergiu=now['convergencia_aprovada'],delta_s=now['convergencia']['delta_s'],email_destinatario='gecesars@gmail.com',email_enviado=False)
    write(root/'qualificacao.json',state);write(dest/'qualificacao.json',state)
    entries=[]
    for p in sorted(dest.rglob('*')):
        if p.is_file() and p.suffix!='.md' and p.name!='manifesto.json':entries.append(dict(arquivo=str(p.relative_to(repo)).replace('\\','/'),bytes=p.stat().st_size,sha256=sha(p)))
    write(dest/'manifesto.json',dict(arquivos=entries))
    print(json.dumps(dict(destino=str(dest),arquivos=len(entries),email_enviado=False)))
