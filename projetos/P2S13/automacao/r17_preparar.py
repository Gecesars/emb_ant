"""Comparacao controlada: somente retirar dobras laterais, largura plana90mm."""
from pathlib import Path
import json,shutil,hashlib
ROOT=Path('D:/dev/EMBRAER/P2S13/R17_Flanges_Refletor');CASE=ROOT/'plano90';ROOT.mkdir(exist_ok=True)
SRC=Path('D:/dev/EMBRAER/P2S13/R16_Tubo_PVC');assert not CASE.exists()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
ANT=CASE/'antena';ANT.mkdir(parents=True)
native='PCB_Plano90.aedt';shutil.copy2(SRC/'dn100/antena/PCB_Tubo_DN100.aedt',ANT/native)
shutil.copy2(SRC/'dn100/antena/HFSS_14nucleos.acf',ANT/'HFSS_14nucleos.acf')
a=read(SRC/'dn100/antena/configuracao.json');a.update(native=native,revisao='R17_Plano90',angulo_dobra_graus=0.,inicio_dobra_y_mm=None)
save(ANT/'configuracao.json',a)
c=read(SRC/'dn100_c02/configuracao.json');c.update(revisao='R17_Plano90',antena_reutilizada=None,divisor_reutilizado=str(SRC/'dn100_c02/divisor'),
    escopo='Comparacao do refletor plano90 com dobrado, tubo aberto R16 preservado; flanges e novos fixadores nao incluidos nesta comparacao isolada.',
    fontes_divisor_sha256={n:hashlib.sha256((SRC/'dn100_c02/divisor'/n).read_bytes()).hexdigest() for n in ['Divisor_Duplo3.aedt','divisor.s8p','configuracao.json']})
c['modelos_RF_ativos']=dict(antena='antena/'+native,divisor=str(SRC/'dn100_c02/divisor/Divisor_Duplo3.aedt'),circuito='circuito/C09_PVC_Nexxim.aedt')
save(CASE/'configuracao.json',c)
print(CASE)
