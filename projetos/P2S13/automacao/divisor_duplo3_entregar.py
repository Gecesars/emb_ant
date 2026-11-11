"""Documenta e arquiva somente o plano de circuito, sem resultados FEM ou malhas."""
from pathlib import Path
import json,hashlib,shutil,zipfile
REPO=Path(__file__).resolve().parents[3]
ROOT=Path('D:/dev/EMBRAER/P2S13/R07_Divisor_Duplo3')
OUT=REPO/'projetos/P2S13/divisor_duplo_1x3';OUT.mkdir(exist_ok=True)
p=json.loads((ROOT/'parametros.json').read_text());cases=json.loads((ROOT/'comparacao_circuitos.json').read_text())
r=cases['Wilkinson_ajustado'];v=json.loads((ROOT/'verificacao.json').read_text());nx=json.loads((ROOT/'circuito/verificacao_nexxim.json').read_text());sen=json.loads((ROOT/'sensibilidade_6_8.json').read_text())
assert nx['matriz_conferida'] and nx['erro_absoluto_max']<2e-6
tables=[]
for name,x in cases.items():
    tables.append('| %s | %.4f / %.4f | %.4f / %.4f | %.4f | %.3f / %.3f |'%(name.replace('_',' '),*x['VSWR_ativo'],*x['VSWR_outra_casada'],x['ganho_frontal_dBi'],x['H_graus'],x['V_graus']))
md=f'''# P2S13 — plano do divisor duplo 1:3

**Planejamento e circuito preliminares, 11/11/2026.** Duas redes Wilkinson 1:3 idênticas alimentam as polarizações A e B das três placas de dois elementos. O ajuste comum de entrada resultou em VSWR ativo **{r['VSWR_ativo'][0]:.4f}/{r['VSWR_ativo'][1]:.4f}** e, com a outra entrada casada em 50 Ω, **{r['VSWR_outra_casada'][0]:.4f}/{r['VSWR_outra_casada'][1]:.4f}**. Os quatro valores ficam abaixo de 1,25 **neste modelo de circuito e nesta frequência**. O divisor ainda não tem layout roteado ou validação EM.

O ganho frontal calculado é **{r['ganho_frontal_dBi']:.4f} dBi**, H **{r['H_graus']:.3f}°** e V **{r['V_graus']:.3f}°**, em 5,17 GHz, com duas entradas de 0,5 W / 0°. Não há sweep. São incorporados a matriz S6 e os campos complexos das três placas juntas, incluindo acoplamento, divisores 1:2 impressos e seis cabos físicos de 50 mm com perdas. Esses cabos **não foram acrescentados outra vez**. A alimentação anterior aos planos de referência e os conectores externos são ideais.

## Topologia e posição propostas

Reservar uma placa de distribuição traseira de aproximadamente **220 × 60 mm**, centralizada longitudinalmente no refletor de 296 mm. Colocar os dois divisores 1:3 na região central, com entradas simétricas e cada polarização ocupando uma metade da largura. Alinhar as três saídas de cada polarização com as conexões existentes, em X = −93,491 / +2,509 / +98,509 mm e Y = ±18 mm, nas coordenadas do HFSS. Isso permite conservar os seis cabos iguais já simulados.

Os três ramais de 50 Ω de cada rede têm **100 mm de comprimento de linha**, após os transformadores de quarto de onda. O ramal da placa central precisa de meandro para igualar os caminhos. São seis ramais nominalmente idênticos; não foram impostas correções de fase diferentes entre placas ou polarizações. A posição final em Z, transições coaxiais, folgas, fixação, separação entre meandros e interferência com as abas precisam de conferência no CAD e no modelo EM do divisor. O retângulo de 220 × 60 mm é uma reserva de espaço, não um desenho de fabricação.

O Wilkinson foi escolhido por manter a alimentação das três cargas mais uniforme na presença das reflexões do conjunto. A versão T sem resistores foi comparada com as mesmas linhas: dispersão de amplitude/fase nas seis portas **{cases['T_nao_isolado']['dispersao_amplitude_dB']:.4f} dB / {cases['T_nao_isolado']['dispersao_fase_graus']:.4f}°**, contra **{r['dispersao_amplitude_dB']:.4f} dB / {r['dispersao_fase_graus']:.4f}°** no Wilkinson ajustado. Sob cargas ideais iguais, ambas as polarizações têm potência e fase exatamente iguais em suas três saídas no modelo. Com a antena real, o acoplamento gera os pequenos desequilíbrios registrados; as duas fontes externas continuam iguais/em fase.

![Plano elétrico](plano_divisor.png)

## Valores iniciais para o futuro layout

| Trecho, por polarização | Impedância | Largura nominal | Comprimento |
|---|---:|---:|---:|
| Ajuste de entrada, idêntico em A/B | {p['Z_ajuste_entrada_ohm']:.3f} Ω | {p['largura_ajuste_entrada_mm']:.3f} mm | {p['comprimento_ajuste_entrada_mm']:.2f} mm |
| Três transformadores de quarto de onda | {p['Z_quarto_onda_ohm']:.3f} Ω | {p['largura_quarto_onda_mm']:.3f} mm | {p['comprimento_quarto_onda_mm']:.3f} mm |
| Três ramais de saída iguais | 50 Ω | {p['largura_saida_mm']:.3f} mm | 100 mm |

Três resistores ideais de **150 Ω em triângulo** interligam as extremidades dos transformadores de cada Wilkinson: seis resistores no total. Encapsulamento, potência e modelo RF dos resistores ainda precisam ser escolhidos antes do layout. O valor não constitui especificação de componente aprovado para 5,17 GHz.

Material nominal do plano: **ZYF300CA-C, núcleo de 1,52 mm**, εr=2,94, tanδ=0,0016, cobre de 35 µm, σ=58 MS/m. A família e os parâmetros dielétricos constam no [serviço oficial de alta frequência da JLCPCB](https://jlcpcb.com/pcb-fabrication/high-frequency-pcb); 1,52 mm vem da cotação histórica do projeto em 7/11, não de uma nova cotação desta placa. Rugosidade RMS de 0,5 µm é hipótese de cálculo.

As linhas usam [MLine do scikit-rf](https://scikit-rf.readthedocs.io/en/latest/api/media/generated/skrf.media.mline.MLine.html), modelos Hammerstad–Jensen e dispersão Kirschning–Jansen. **Não foram modelados ENIG do divisor, descontinuidades das junções, curvas, acoplamento entre trilhas, parasitas dos resistores e soldas.** As perdas das placas radiantes e seus cabos já estão nos dados HFSS, conforme os materiais do R06. Não há aprovação para fabricação.

## Casamento visto nas duas entradas

| Rede carregada pelo mesmo S6 | VSWR ativo A/B | VSWR outra casada A/B | G frontal (dBi) | H / V (°) |
|---|---:|---:|---:|---:|
{chr(10).join(tables)}

A otimização variou somente a impedância e o comprimento do trecho comum de entrada, mantendo valores idênticos nas duas polarizações. Objetivo: minimizar o maior módulo de reflexão entre os dois casos ativos e os dois casos com a outra entrada casada. Busca limitada a 35–80 Ω e 1–20 mm, somente em 5,17 GHz. A largura final foi arredondada a 0,001 mm e o comprimento a 0,01 mm; o circuito foi recalculado após arredondar. Isso é precisão de parametrização, não tolerância de fabricação prometida.

No modelo nominal com saídas em 50 Ω, a perda excedente de transmissão do divisor ajustado é **{p['perda_excedente_nominal_dB'][0]:.4f} dB**, além da divisão ideal de 4,7712 dB. Esse valor inclui o descasamento do ajuste projetado para a carga real; não é apenas dissipação. Com o painel conectado e 1 W incidente: reflexão **{r['potencia_refletida_W']:.6f} W**, dissipação na rede distribuidora **{r['dissipacao_divisor_W']:.6f} W**, potência líquida aceita no modelo da antena **{r['potencia_aceita_antena_W']:.6f} W**. A soma confere. O ganho já incorpora esse carregamento e as perdas nominais do divisor do circuito.

Os máximos continuam H **{r['pico_H_graus']:+.2f}°**, V **{r['pico_V_graus']:+.2f}°**. O corte H tem topo quase plano com dois máximos próximos; o plano do divisor não corrige esse formato. O maior lóbulo vertical frontal é **{r['SLL_V_dB']:.3f} dB** em relação ao máximo. A largura H permanece próxima de 100°, mas não chegou a 100° exatos; V continua perto de 10°, não 18°.

![Diagramas normalizados](polar_conjunto.png)

## Verificações e limites de confiança

O Wilkinson ideal de três vias foi conferido por montagem independente: entrada e saídas casadas, saídas isoladas, transmissão −j/√3. Erro máximo **{v['benchmark_3vias_ideal_erro']:.3g}**. O circuito de linhas com perdas foi resolvido por redução nodal e também por interconexão de ondas no scikit-rf; erro **{r['erro_validacao_nodal_circuit']:.3g}**. A interconexão completa com S6 foi conferida por dois algoritmos e, depois, pelo **Ansys Circuit/Nexxim**, com erro máximo **{nx['erro_absoluto_max']:.3g}** na matriz S2. Isso verifica o cálculo e a ligação; não valida a física ainda ausente no modelo do divisor.

O S6 original não foi simetrizado ou modificado. SHA-256: `{v['S6_sha256']}`. A rede distribuidora é passiva e recíproca, mas a matriz carregada herda o erro numérico da antena: |S−Sᵀ| máximo **{r['reciprocidade_conjunto']:.8g}**, ainda acima do limite de auditoria de 1×10⁻⁵. A [continuação da antena](../continuacao_tres_placas2/README.md) convergiu em ΔS=0,01760, porém não passou na estabilidade das nove sondas nem na reciprocidade estrita. **Assim, o VSWR abaixo de 1,25 é uma indicação preliminar; o conjunto não está qualificado.**

Como verificação de sensibilidade, a mesma rede aplicada aos dados anteriores de seis passes dá VSWR máximo **{max(sen['passes6_VSWR_ativo']+sen['passes6_VSWR_casado']):.4f}**; com oito passes, **{max(sen['passes8_VSWR_ativo']+sen['passes8_VSWR_casado']):.4f}**. O caso de seis passes ultrapassa 1,25, reforçando que não se deve liberar a PCB com base apenas no casamento do modelo atual. Não houve novo solve FEM, varredura de frequência ou adaptação além dos passes 7 e 8 solicitados.

## Arquivos e próximo desenvolvimento

[Parâmetros](parametros.json) · [Resultados dos três circuitos](comparacao_circuitos.json) · [Sensibilidade](sensibilidade_6_8.json) · [Conferência Nexxim](circuito/verificacao_nexxim.json) · [S2 final](Wilkinson_ajustado_conjunto.s2p) · [S8 do divisor duplo](Wilkinson_ajustado_duplo.s8p).

[Circuito nativo](circuito/P2S13_Divisor_Duplo3.aedt) · [Arquivo AEDTZ portátil com Touchstones, sem malhas](circuito/P2S13_Divisor_Duplo3_sem_malhas.aedtz). Preferir restaurar o AEDTZ para trazer os arquivos externos; o `.aedt` conserva os caminhos locais originais. O projeto contém dois blocos S4 idênticos e o S6 da antena, com duas portas externas de 50 Ω. A potência/fase operacional é aplicada na recomposição de ondas documentada pelo script.

A próxima implementação é rotear as duas redes simétricas, selecionar resistores RF e transições, conferir o encaixe traseiro e simular a PCB distribuidora completa separadamente em HFSS. Depois substituir o S8 analítico pelo S8 EM e repetir a ligação ao painel. O casamento, ganho e forma do diagrama deverão ser revistos com a malha da antena qualificada. Não foi iniciada essa etapa automaticamente.

Reprodução: `divisor_duplo3_planejar.py`, seguido de `divisor_duplo3_nexxim.py` e `divisor_duplo3_entregar.py`, em `../automacao`. Trabalho local: `{ROOT.as_posix()}`. O script Nexxim recusa sobrescrever um projeto existente. [Manifesto](manifesto.json) rastreia os arquivos; nenhum `.aedtresults`, malha, lock ou campo volumétrico é enviado ao Git.
'''
(OUT/'README.md').write_text(md,encoding='utf-8')
records=[]
allowed={'.json','.png','.csv','.aedt','.aedtz','.s2p','.s4p','.s6p','.s8p'}
for p in sorted(ROOT.rglob('*')):
    if not p.is_file() or p.suffix not in allowed or any(s.endswith(('.aedtresults','.aedb')) for s in p.parts):continue
    if p.suffix=='.aedtz' and zipfile.is_zipfile(p):
        with zipfile.ZipFile(p) as z:
            assert not any('.aedtresults' in n or n.endswith(('.ngmesh','.g3derr','.lock')) for n in z.namelist())
    dest=OUT/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    h=hashlib.sha256(p.read_bytes()).hexdigest();assert hashlib.sha256(dest.read_bytes()).hexdigest()==h
    records.append(dict(arquivo=dest.relative_to(REPO).as_posix(),fonte=str(p),sha256=h,bytes=p.stat().st_size))
(OUT/'manifesto.json').write_text(json.dumps(dict(artefatos=records,total_bytes=sum(x['bytes'] for x in records)),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('PLANO_ARQUIVADO',len(records),'arquivos')
