"""Registrar a mudanca de prioridade, sem modificar resultados RF historicos."""
import json,datetime,sys
from pathlib import Path
repo=Path(__file__).resolve().parents[3];old=Path('D:/dev/EMBRAER/P1H/R07_Banda17')
p=old/'qualificacao.json';previous=json.loads(p.read_text(encoding='utf-8-sig'))
if previous.get('estado','').startswith('SEMIPRONTA'):
    print('P1H_JA_CONGELADA');sys.exit(0)
state=dict(estado='SEMIPRONTA_CONGELADA_POR_SOLICITACAO_DO_USUARIO',data=datetime.datetime.now().isoformat(),
  motivo='Prioridade transferida para novo projeto P2M21, duas colunas, >=21dBi por entrada MIMO em5.09-5.25GHz.',
  preservado='R06 aprovada no centro. R07 com centro conferido, varredura interrompida voluntariamente; banda nao qualificada.',
  parada='Watcher12096 encerrado apos identidade conferida. StopSimulations aplicado somente a PCB_R07_SWEEP, AEDT172792; processos encerrados.',
  automacao_R07='Excluida nesta conversa; nenhum email R07 enviado.',estado_anterior=previous)
p.write_text(json.dumps(state,indent=2,ensure_ascii=False),encoding='utf8')
(repo/'resultados/r07/estado_semipronta.json').write_text(json.dumps(state,indent=2,ensure_ascii=False),encoding='utf8')
readme=repo/'README.md';s=readme.read_text(encoding='utf8');start=s.index('**R07 em calculo') if '**R07 em calculo' in s else s.index('**R07 em cálculo');end=s.index('\n\n',start)
s=s[:start]+'''**P1H semipronta — campanha R07 suspensa a pedido do usuário em 8/11.** A R06 permanece qualificada somente em 5,17 GHz. O centro R07 foi conferido; a varredura de 17 frequências foi interrompida voluntariamente para iniciar o novo projeto. Não há aprovação de banda R07. [Registro do congelamento](resultados/r07/estado_semipronta.json).

**Novo projeto P2M21:** duas colunas, 16 níveis e duas entradas MIMO independentes, com meta de **21 dBi por entrada em 5,09–5,25 GHz**, a outra entrada casada em 50 Ω. [Concepção, placas KiCad, montagem FreeCAD e HFSS separado](projetos/P2M21/README.md).'''+s[end:]
readme.write_text(s,encoding='utf8')
p=repo/'resultados/r07/README.md';s=p.read_text(encoding='utf8');p.write_text('> **Estado atual: SEMIPRONTA / CONGELADA em 8/11/2026 a pedido do usuário.** A fila e o acompanhamento R07 foram encerrados; o conteúdo abaixo registra o histórico anterior. Banda completa não qualificada. Novo projeto: [P2M21](../../projetos/P2M21/README.md).\n\n'+s,encoding='utf8')
print('P1H_CONGELADA')
