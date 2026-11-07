"""Guardar somente fontes nativas e dados concluídos da correção R05."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

repo=Path(__file__).resolve().parents[2]

def main(work):
    records=[]
    def copy(source,dest):
        source=work/source
        dest=repo/dest
        assert source.is_file(),source
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,dest)
        records.append(dict(arquivo=dest.relative_to(repo).as_posix(),origem=source.relative_to(work).as_posix(),
            bytes=dest.stat().st_size,sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
    for case in ['Bobina_r090','Bobina_esmalte20','Conector_N']:
        source=Path('cupons')/case
        assert 'Converged : Yes' in (work/source/'convergencia.txt').read_text()
        copy(source/(case+'.aedt'),Path('hfss/alimentacao/r05')/(case+'.aedt'))
        for name in ['cupom.s2p','convergencia.txt']:
            copy(source/name,Path('resultados/r05/diagnostico/entrada')/case/name)
    for name in ['hipotese.json','resultado.json','comparacao.csv']:
        copy(Path('cupons/Bobina_esmalte20')/name,Path('resultados/r05/diagnostico/entrada/Bobina_esmalte20')/name)
    for stage in ['1x2','1x5']:
        copy(Path('enig')/stage/('ENIG_'+stage+'.aedt'),Path('hfss/alimentacao/r05')/('ENIG_shell_'+stage+'.aedt'))
    for name in ['divisor.s6p','convergencia.txt','comparacao.json','enig_solido_hfss.json']:
        copy(Path('enig_solido/1x2')/name,Path('resultados/r05/rede/cobre_solido_1x2')/name)
    copy(Path('enig_solido/1x2/Divisor_solido.aedt'),Path('hfss/alimentacao/r05/ENIG_solido_1x2.aedt'))
    copy(Path('face40/antena_direta/Antena_direta.aedt'),Path('hfss/antenas/R05_Diagnostico_face40.aedt'))
    patterns=list((work/'face40/antena_direta/padroes').glob('*.csv'))
    assert len(patterns)==40
    for path in patterns:
        copy(path.relative_to(work),Path('resultados/r05/diagnostico/face40/padroes')/path.name)
    target=repo/'resultados/r05/manifesto_diagnosticos.json'
    target.write_text(json.dumps(dict(arquivos=records,
        nota='Nativos sem resultados volumétricos e malhas; S e cortes exportados são evidência dos estudos concluídos. O painel integral não integra este pacote de diagnóstico.'),indent=2),encoding='utf8')
    print(len(records),'arquivos',sum(row['bytes'] for row in records),'bytes')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('diretorio',type=Path)
    main(p.parse_args().diretorio)
