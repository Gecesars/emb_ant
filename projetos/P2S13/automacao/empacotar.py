"""Arquiva somente estudos encerrados, sem malhas ou campos volumetricos."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path('D:/dev/EMBRAER/P2S13/R00_Refletor_Dobrado')
REPO = Path(__file__).resolve().parents[3]
DEST = REPO / 'projetos/P2S13/estudo_refletor_R00'


def main():
    state = json.loads((ROOT / 'pipeline.json').read_text(encoding='utf-8-sig'))
    assert state['estado'] == 'CONCLUIDO_AGUARDA_COMPARACAO', state
    comparison = json.loads((ROOT / 'comparacao.json').read_text())
    assert len(comparison) >= 3
    files = []

    def copy(src):
        assert src.is_file(), src
        relative = src.relative_to(ROOT)
        assert not any(s.endswith('.aedtresults') for s in relative.parts)
        assert src.suffix.lower() not in {'.g3derr', '.lock', '.bak'}
        dst = DEST / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        digest = hashlib.sha256(src.read_bytes()).hexdigest()
        assert hashlib.sha256(dst.read_bytes()).hexdigest() == digest
        files.append(dict(arquivo=relative.as_posix(), bytes=src.stat().st_size,
                          sha256=digest))

    for name in ['requisitos.json', 'estimativa_arranjos.json',
                 'estimativa_arranjos.png', 'diagnostico_vertical.json',
                 'diagnostico_dobras_cad.json',
                 'geometria_estudo.png', 'comparacao.json', 'comparacao.csv',
                 'comparacao_HV.png', 'comparacao_normalizada.png']:
        copy(ROOT / name)
    for row in comparison:
        case = ROOT / row['variante']
        r = json.loads((case / 'resultado.json').read_text())
        assert r['fisica_ok'], case
        assert not list(case.glob('*.aedt.lock')), case
        assert r['passes'] <= 6 and r['nucleos'] == 14
        for name in ['P2S13.aedt', 'P2S13.FCStd', 'centro.s4p',
                     'configuracao.json', 'convergencia.txt',
                     'HFSS_14nucleos.acf', 'hfss_validacao.json',
                     'historico_passes.json', 'malha.json', 'mensagens.json',
                     'ordem_fontes.json', 'qualificacao.json',
                     'recursos_matriz.json', 'resultado.json',
                     'diagramas_HV.png', 'polar_HV.png']:
            copy(case / name)
        fields = sorted(case.glob('*_H.csv')) + sorted(case.glob('*_V.csv'))
        assert len(fields) == 14
        for path in fields:
            copy(path)
        for name in ['manifesto.json', 'folhas_solidas.json', 'portas.json',
                     'intersecoes.json', 'reabertura.json']:
            copy(case / 'cad' / name)
    for name in ['interrupcao.json', 'copias_tau.json', 'configuracao.json',
                 'hfss_validacao.json', 'centro.log', 'centro_aedt.log']:
        copy(ROOT / 'diagnostico_classic' / name)
    for path in (ROOT / 'diagnostico_classic').glob('*.profile'):
        copy(path)
    manifest = dict(estado='ESTUDO_PRELIMINAR_NAO_LIBERADO_PARA_FABRICACAO',
                    fonte=str(ROOT), arquivos=files,
                    observacao='Convergencia e atendimento das metas constam separadamente em cada resultado.json. Sem malhas, resultados volumetricos, locks ou cache do solver.')
    (DEST / 'manifesto.json').write_text(json.dumps(manifest, ensure_ascii=False,
                                                   indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(arquivos=len(files), bytes=sum(x['bytes'] for x in files),
                         destino=str(DEST)), indent=2))


if __name__ == '__main__':
    main()
