"""Snapshot compacto, somente leitura, das tres simulacoes autorizadas."""
from pathlib import Path
import json,subprocess,sys
from oito_celulas_monitorar import progress
W=Path('D:/dev/EMBRAER/P2M21')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig')) if p.exists() else {}
def main():
    a=read(W/'R15_Oito_Celulas_8passes/pipeline.json');b=read(W/'comparacao_colunas_niveis/pipeline.json')
    rows=[]
    for n in ['R15_Oito_Celulas_8passes','R16_Oito_Celulas_78mm','R17_Dez_Celulas_78mm']:
        root=W/n;cfg=read(root/'configuracao.json');state=read(root/'qualificacao.json');row=dict(versao=n,estado=state.get('estado'))
        try:
            p=progress(root) if (root/cfg['native']).exists() else {};h=p.get('historico',[])
            if h:row.update(passe_completo=h[-1]['passe'],delta_s=h[-1]['delta_s'],ganho_cache_dBi=h[-1]['campos_dBi'].get('R14_Campo_00'),delta_campo_dB=h[-1]['delta_campo_max_dB'])
        except (AssertionError,ValueError,IndexError,KeyError) as e:row['metadados_em_atualizacao']=str(e)[:120]
        if (root/'resultado.json').exists():
            r=read(root/'resultado.json');row.update(convergiu=r['convergiu'],validado=r['validado_numericamente'],ganho=r['cortes']['H']['ganho_frontal_dBi'])
        rows.append(row)
    print(json.dumps(dict(continuacao=a,variantes=b,estudos=rows),ensure_ascii=False))
if __name__=='__main__':main()
