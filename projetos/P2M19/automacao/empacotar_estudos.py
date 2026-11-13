"""Publica nativos e evidências compactas do lote concluído, sem malhas."""
from pathlib import Path
import hashlib,json,shutil

REPO=Path(__file__).resolve().parents[3];WORK=Path('D:/dev/EMBRAER/P2M19')
CAMPAIGN=WORK/'Campanha_72mm_20261113';OUT=REPO/'projetos/P2M19/estudo_72mm'
NAMES=['R02_16x2_72mm','R03_72mm_ref162','R04_72mm_ref146']

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    state=read(CAMPAIGN/'estado.json')
    assert state['estado'] in ['LOTE_CONCLUIDO_REVISAR','LOTE_CONCLUIDO_REVISADO'],state
    assert len(read(CAMPAIGN/'comparacao.json'))==4
    review=read(CAMPAIGN/'revisao_visual.json')
    assert review['revisado']
    for item in review['imagens']:assert digest(Path(item['origem']))==item['sha256']
    expected_images={(WORK/name/image).resolve() for name in NAMES for image in ['polar_HV.png','comparacao_diagramas.png','acoplamento_vswr.png','montagem_frontal.png','montagem_duas_faces.png']}
    expected_images.update((CAMPAIGN/name).resolve() for name in ['comparacao_HV.png','comparacao_polar_HV.png'])
    assert expected_images.issubset({Path(item['origem']).resolve() for item in review['imagens']})
    OUT.mkdir(parents=True,exist_ok=True);manifest=[]
    def copy(source,relative):
        source=Path(source);target=OUT/relative;target.parent.mkdir(parents=True,exist_ok=True)
        assert source.is_file(),source
        assert not any(s in str(relative).lower() for s in ['.aedtresults','.g3derr','.lock','.ngmesh','.fld','.profile'])
        shutil.copy2(source,target);assert source.read_bytes()==target.read_bytes()
        manifest.append(dict(arquivo=str(relative).replace('\\','/'),origem=str(source),bytes=target.stat().st_size,sha256=digest(target)))
    for name in NAMES:
        root=WORK/name;cfg=read(root/'configuracao.json');r=read(root/'resultado.json')
        assert r['passes']<=6 and r['nucleos']==14 and r['fisica_ok']
        c=r['cortes'];f=r['cortes_finos'];status='Convergência S atendida' if r['convergiu'] else 'PRELIMINAR — NÃO CONVERGIDO'
        lines=[f"# {name}",'',f"**{status}.** 5,17 GHz, {r['passes']} passes, ΔS {r['delta_s']:.8f}; alvo 0,05. Perfil auditado: 14 núcleos, sem sweep.",
            '',f"Ganho frontal realizado total **{c['H']['ganho_frontal_dBi']:.4f} dBi**; aberturas do lóbulo principal H **{f['H']['abertura_graus']:.4f}°** e V **{f['V']['abertura_graus']:.4f}°**.",
            '',f"Máximos H/V: {f['H']['pico_interpolado_graus']:+.4f}° / {f['V']['pico_interpolado_graus']:+.4f}°. Maiores lóbulos secundários frontais H/V: {c['H']['SLL']['nivel_dB']:.3f} / {c['V']['SLL']['nivel_dB']:.3f} dB relativos ao pico de cada corte.",
            '',f"VSWR ativo nas 16 portas: {min(r['VSWR_ativo']):.4f} a {max(r['VSWR_ativo']):.4f}. VSWR máximo com demais portas casadas: {max(r['VSWR_casado']):.4f}.",
            '',f"16 níveis × duas colunas a {cfg['passo_horizontal_mm']:g} mm; oito placas C12 de quatro radiadores. Refletor {cfg['refletor_mm'][0]:g} × 776 × 2 mm; altura da PCB 14,949 mm. Cada entrada recebe 0,0625 W a 0°, total 1 W.",
            '', 'Inclui acoplamento, divisores impressos e perdas de RO4350B, cobre e ENIG nominal. Sem rede externa, cabos em 3D, conectores N, radome ou suportes plásticos. O ganho é total coerente, não qualificação por entrada MIMO.',
            '',f"Balanço de potência consistente: {r['balanco_potencia_valido']}. Reparos Major/Minor: {r['major']}/{r['minor']}. Reciprocidade: {r['reciprocidade']:.3e}. Recomposição das fontes: erro relativo máximo {max(r['recomposicao'].values()):.3e}.",
            '',f"Estabilidade das nove sondas: {r['estavel_nove_sondas']}. Validação numérica completa: {r['validado_numericamente']}. Atingir o limite de seis passes não representa convergência; resultados sem estabilidade permanecem preliminares.",
            '', '![Diagramas polares](polar_HV.png)','', '![Comparação com R01 de 88 mm](comparacao_diagramas.png)','', '![Acoplamento e VSWR](acoplamento_vswr.png)',
            '',f"[HFSS]({cfg['native']}) · [CAD EM]({cfg['cad_native']}) · [S16](centro.s16p) · [Resultado completo](resultado.json) · [Configuração](configuracao.json).",
            '', '## Adaptação','', '| Passe | Tetraedros | ΔS | G frontal monitorado (dBi) |','|---:|---:|---:|---:|']
        for p in read(root/'historico_passes.json')['historico']:
            ds='—' if p['delta_s'] is None else f"{p['delta_s']:.8f}"
            lines.append(f"| {p['passe']} | {p['tetraedros']} | {ds} | {p['campos_dBi']['P2M19_Campo_00']:.6f} |")
        lines+=['','Nativos e campos distantes estão preservados; malhas e campos volumétricos ficam somente na pasta local de trabalho. Materiais nominais e uma única frequência não qualificam fabricação ou banda completa.']
        if (root/'evidencias/curvilinear_inicial.txt').exists():
            lines+=['','O registro original da projeção curvilínea da malha inicial está em [curvilinear_inicial.txt](evidencias/curvilinear_inicial.txt). Eventuais faces rebaixadas para representação linear constam desse diagnóstico; isso é distinto da contagem de reparos Major/Minor.']
        (root/'RELATORIO.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        mandatory=[cfg['native'],cfg['cad_native'],'configuracao.json','resultado.json','qualificacao.json','centro.s16p','convergencia.txt','mensagens.json','ordem_fontes.json','HFSS_14nucleos.acf','malha.json','historico_passes.json','recursos_matriz.json','solver_efetivo.json','potencia.json','hfss_validacao.json','geometria_importada.json','polar_HV.png','comparacao_diagramas.png','acoplamento_vswr.png','montagem_frontal.png','montagem_duas_faces.png','scripts_sha256.json','RELATORIO.md']
        mandatory+=[p.relative_to(root).as_posix() for p in root.glob('*.csv')]
        mandatory+=[p.relative_to(root).as_posix() for p in (root/'cad').glob('*.json')]
        mandatory+=[p.relative_to(root).as_posix() for p in (root/'scripts').glob('*.py')]
        mandatory+=['pipeline.json']
        mandatory+=[p.relative_to(root).as_posix() for p in (root/'evidencias').iterdir() if p.is_file() and p.suffix in ['.txt','.json','.ps1']] if (root/'evidencias').exists() else []
        mandatory+=[n for n in ['revisao_visual.json','analise_exitcode.json'] if (root/n).exists()]
        for filename in sorted(set(mandatory)):copy(root/filename,Path('casos')/name/filename)
        copy(root/'RELATORIO.md',Path('casos')/name/'README.md')
    for name in ['RELATORIO.md','comparacao.json','comparacao.csv','comparacao_HV.png','comparacao_polar_HV.png','plano.json','estado.json','controle_geometria.json','revisao_visual.json','resultados_parciais.json']:
        copy(CAMPAIGN/name,name)
    copy(CAMPAIGN/'RELATORIO.md','README.md')
    (OUT/'manifesto.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(arquivos=len(manifest),bytes=sum(x['bytes'] for x in manifest),pasta=str(OUT)),indent=2))
if __name__=='__main__':main()
