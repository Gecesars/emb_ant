"""Documenta valores medidos e limitacoes, sem escolher automaticamente uma geometria."""
from pathlib import Path
import json
import math

ROOT = Path('D:/dev/EMBRAER/P2S13/R00_Refletor_Dobrado')
REPO = Path(__file__).resolve().parents[3]
DEST = REPO / 'projetos/P2S13/estudo_refletor_R00'


def main():
    rows = json.loads((ROOT / 'comparacao.json').read_text())
    assert len(rows) >= 3
    DEST.mkdir(exist_ok=True, parents=True)
    text = [
        '# P2S13 — estudo preliminar do refletor dobrado', '',
        'Duas placas C12 de quatro elementos, empilhadas conforme confirmado pelo usuário, '
        'formam oito níveis em uma coluna. A comparação é em 5,17 GHz, com quatro portas '
        'de 0,25 W e 0°, totalizando 1 W. As perdas dos materiais das PCBs, dos divisores '
        'impressos e dos quatro cabos físicos de 50 mm estão incluídas. Não há rede externa '
        'nem conectores N neste modelo.', '',
        '**Metas:** ganho frontal realizado total ≥13 dBi; abertura horizontal a −3 dB '
        'de 99–121°; abertura vertical a −3 dB de 16,2–19,8°.', '',
        '| Caso | Malha | Dobra a partir do eixo | Ângulo para trás | Ganho frontal | H | V | VSWR ativo máximo | ΔS final | Passes | Convergiu |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|',
    ]
    for r in rows:
        text.append(f"| [{r['variante']}]({r['variante']}/resultado.json) | {r['metodo_malha']} | "
                    f"{r['inicio_dobra_mm']:.0f} mm | {r['angulo_graus']:.0f}° | "
                    f"{r['ganho_dBi']:.3f} dBi | {r['H_graus']:.2f}° | "
                    f"{r['V_graus']:.2f}° | {r['VSWR_ativo_max']:.3f} | "
                    f"{r['delta_s']:.6f} | {r['passes']} | "
                    f"{'Sim' if r['convergiu'] else 'Não'} |")
    approved = [r['variante'] for r in rows if r['aprovado']]
    text += ['', ('Casos que atenderam às metas e às verificações numéricas: ' +
                  ', '.join(approved) if approved else
                  '**Nenhuma geometria está aprovada para as três metas.** '
                  'Os casos que não convergiram são comparações preliminares, não uma validação RF.'), '',
             '![Diagramas normalizados e faixas desejadas](comparacao_normalizada.png)', '',
             '![Ganho realizado total dos casos](comparacao_HV.png)', '',
             '## Geometria e convenção das dobras', '',
             'O comprimento do refletor é 392 mm, a largura desenvolvida é 90 mm e a '
             'espessura é 2 mm. Usou-se raio interno nominal de 2 mm e fator K de 0,4. '
             'O parâmetro b mede a distância lateral entre o eixo e a tangência da parte '
             'plana frontal com a dobra. As duas abas são simétricas. O ângulo é o desvio '
             'para trás em relação à chapa plana: 0° é plano e 90° é aba orientada para −Z. '
             'Assim, o ensaio de 60° corresponde a ângulo interno de 120°.', '',
             'A largura desenvolvida foi mantida igual nos casos. Para a chapa plana, '
             'a linha nominal no meio do arco de dobra fica em b + BA/2, onde '
             'BA = α(rad) × (Ri + Kt). Isso é diferente da posição da tangência b. '
             'As posições são parâmetros de estudo; ainda não são cotas liberadas para fabricação.', '',
             '| Caso dobrado | Largura projetada | Profundidade total do refletor | Linha nominal no meio da dobra, na chapa plana |',
             '|---|---:|---:|---:|']
    for r in rows:
        if not r['angulo_graus']:
            continue
        case = ROOT / r['variante']
        cfg = json.loads((case / 'configuracao.json').read_text())
        cad = json.loads((case / 'cad/intersecoes.json').read_text())
        ba = math.radians(r['angulo_graus']) * (cfg['raio_interno_mm'] + cfg['K_dobra'] * cfg['espessura_mm'])
        text.append(f"| {r['variante']} | {cad['extensao_refletor_Y_mm']:.3f} mm | "
                    f"{cad['extensao_refletor_Z_mm']:.3f} mm | ±{r['inicio_dobra_mm'] + ba / 2:.3f} mm |")
    text += ['', '![Geometria de estudo](geometria_estudo.png)', '',
             'As PCBs têm 70 × 184 mm e seus centros ficam a 192 mm, deixando 8 mm '
             'entre elas. O passo dos radiadores permanece 48 mm; a face inferior do '
             'núcleo fica a 14,949 mm do plano frontal do refletor. O CAD contém 83 '
             'sólidos; os 82 corpos das duas células foram copiados da C12 com verificação '
             'de volume, área e número de faces. Não há interferências volumétricas '
             'nos pares de corpos verificados. Cada pasta inclui o FreeCAD e o HFSS nativos. '
             'Os parâmetros documentais do FreeCAD não recalculam o BREP: alterar o JSON '
             'e reconstruir com criar_cad.py.', '',
             '## Limitação da abertura vertical', '',
             'A estimativa com os campos complexos da C12 e fator de arranjo prevê '
             'aproximadamente 7,63° para duas placas em coluna, contra 15,18° para uma. '
             'Para centros separados por 192 mm, o fator de arranjo uniforme ideal '
             'tem seu primeiro zero em aproximadamente ±8,69°. Essa é uma estimativa '
             'sem o acoplamento entre placas ou o novo refletor; não substitui os resultados HFSS.', '',
             'As dobras laterais são estudadas para modificar a abertura horizontal. '
             'Não se deve interpretar o atendimento horizontal como atendimento vertical. '
             'Atingir 18° com oito níveis pode exigir modificar a distribuição de amplitude '
             'dentro das placas ou a geometria vertical, em estudo separado. Nenhuma dessas '
             'alterações foi aplicada aos casos desta comparação.', '',
             '## Método e rastreabilidade', '',
             'Materiais nominais preservados da célula C12: RO4350B com núcleo de '
             '0,76 mm, εr=3,66 e tanδ=0,0037; cobre físico de 35 µm com ENIG; '
             'alumínio AL5052 com condutividade de 2,0×10⁷ S/m; solda SAC305 com '
             '7,575758×10⁶ S/m. O dielétrico dos acessos coaxiais usa o modelo '
             'PTFE_terminal da célula de referência, εr=2,03636 e tanδ=0,000276831. '
             'Esses parâmetros são hipóteses do modelo e não medições do material deste protótipo.', '',
             'HFSS 2024 R2, sem GUI, 14 núcleos confirmados no perfil de todos os passes. '
             'Malha automática conforme a coluna da tabela (Classic ou TAU estrita), '
             'sem operações locais ou refinamento inicial imposto, '
             'sem MeshLink. Adaptação durante a solução, no máximo seis passes por geometria; '
             'alvo ΔS ≤0,05 por dois passes consecutivos. As nove sondas de campo são '
             'monitoramento adicional; a análise verifica variação ≤0,1 dB nos dois últimos '
             'passes para declarar estabilidade. Nenhum caso é aprovado por simplesmente '
             'chegar ao sexto passe. Não houve sweep de frequência.', '',
             'A tentativa b=20 mm/60° com Classic foi interrompida pela API após '
             '56,66 minutos na geração inicial, sem primeiro passe ou resultado RF. '
             'O processo continuava consumindo CPU, sem indicação de falta de memória; '
             'a causa exata da demora não foi determinada. O CAD foi conferido válido. '
             'As cópias TAU usam os mesmos arquivos CAD, verificados por SHA-256, com '
             'Flex e fallback desativados. A escolha de outro gerador de malha não '
             'relaxa as tolerâncias nem demonstra convergência. '
             '[Documentação Ansys sobre os geradores de malha](https://ansyshelp.ansys.com/public/views/secured/electronics/v251/en/subsystems/hfss/content/Mesh/SpecifyingInitialMeshSettings.htm).', '',
             'Foram verificadas as matrizes S4, passividade, reciprocidade, potência aceita '
             'e recomposição dos campos complexos das quatro fontes individuais. Cada caso '
             'contém o resultado das verificações e a auditoria dos reparos de malha. '
             'Os 14 CSVs por caso contêm cortes de campo distante, não campos volumétricos. '
             'O manifesto confere os arquivos copiados byte a byte. Malhas, .aedtresults, '
             'g3derr e locks permanecem fora do repositório.', '',
             'A P2M21 R18 e os documentos enviados anteriormente permanecem preservados. '
             'Este estudo não altera os Gerbers C12 nem constitui liberação de fabricação.', '']
    (DEST / 'README.md').write_text('\n'.join(text), encoding='utf-8')


if __name__ == '__main__':
    main()
