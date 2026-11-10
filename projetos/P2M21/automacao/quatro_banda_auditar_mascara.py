"""Reproduz a correcao da mascara sem alterar resultados HFSS ou auditorias antigas."""
from pathlib import Path
import json,hashlib
import numpy as np
from quatro_banda_avaliar import main_lobe_mask
from divisor_variantes_comparar import read_pattern
from quatro_banda_estimar import ROOT,BASE

def run():
    ref=json.loads((BASE/'resultado.json').read_text());evidence=[]
    for old in sorted(ROOT.glob('c*/diagrama_comparado_antes_correcao_mascara.json')):
        folder=old.parent;c=json.loads((folder/'resultado.json').read_text());original=json.loads(old.read_text());metrics={}
        for axis in 'HV':
            t,e=read_pattern(BASE/('AB_'+axis+'.csv'));u,f=read_pattern(folder/('AB_'+axis+'.csv'))
            g=10*np.log10(np.sum(abs(e)**2,axis=1))-ref['cortes'][axis]['ganho_pico_dBi']
            h=10*np.log10(np.sum(abs(f)**2,axis=1))-c['cortes'][axis]['ganho_pico_dBi']
            d=abs(np.interp(t+c['cortes'][axis]['pico_graus']-ref['cortes'][axis]['pico_graus'],u,h)-g)
            before=(abs(t)<=90)&(g>=-10);mask,bounds=main_lobe_mask(t,g)
            i=np.flatnonzero(before)[np.argmax(d[before])]
            np.testing.assert_allclose(max(d[before]),original['metricas'][axis]['erro_forma_lobo_alinhado_dB'],atol=1e-12,rtol=0)
            metrics[axis]=dict(erro_anterior=float(max(d[before])),angulo_pior_anterior=float(t[i]),erro_lobo_principal=float(max(d[mask])),limites=bounds,angulos_excluidos=t[before&~mask].tolist())
        evidence.append(dict(candidato=folder.name,sha256_auditoria_anterior=hashlib.sha256(old.read_bytes()).hexdigest(),metricas=metrics))
    # Dois lobos separados por um minimo: apenas o lobo de zero pertence a mascara.
    t=np.arange(-90,91,dtype=float);g=np.maximum(-.08*t*t,-6-.1*(t-45)**2)
    mask,_=main_lobe_mask(t,g);assert mask[90] and not mask[135]
    assert evidence
    result=dict(motivo='Mascara >=-10dB incluia lobulo secundario da referencia a37..44.75graus; a reducao do secundario era contada como erro de forma principal.',criterios_numericos_inalterados=True,regressao_lobo_secundario_excluido=True,candidatos=evidence)
    (ROOT/'correcao_mascara_lobo_principal.json').write_text(json.dumps(result,indent=2)+'\n')
    print('MASCARA_CONFERIDA',len(evidence))

if __name__=='__main__':run()
