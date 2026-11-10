"""Audita cada candidato real contra a referencia convergida R12."""
from pathlib import Path
import argparse,json,csv
import numpy as np
import skrf as rf
from scipy.signal import find_peaks
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from quatro_ajustar_analisar import analyze
from divisor_variantes_comparar import read_pattern,profile_matrix_solves
from quatro_8fast_auditar import history
from quatro_banda_estimar import BASE,VSWR_TARGET

def main_lobe_mask(theta,normalized_gain):
    """Trecho entre os primeiros minimos, sem incorporar lobos secundarios."""
    front=np.flatnonzero(abs(theta)<=90)
    peak=front[np.argmax(normalized_gain[front])]
    minima,_=find_peaks(-normalized_gain)
    left=[i for i in minima if i<peak];right=[i for i in minima if i>peak]
    lo=max(left) if left else front[0];hi=min(right) if right else front[-1]
    mask=(abs(theta)<=90)&(normalized_gain>=-10)&(theta>=theta[lo])&(theta<=theta[hi])
    assert mask[peak] and np.count_nonzero(mask)>2
    return mask,[float(theta[lo]),float(theta[hi])]

def center(folder):
    r=analyze(folder);ref=json.loads((BASE/'resultado.json').read_text());checks={};metrics={}
    checks['fisica']=r['fisica_ok'];checks['convergencia']=r['convergiu'];checks['ganho_minimo12']=r['cortes']['H']['ganho_frontal_dBi']>=12
    checks['SLL_vertical']=r['SLL_V']['nivel_dB']<=ref['SLL_V']['nivel_dB']+.5
    fig,axs=plt.subplots(1,2,figsize=(11,5.5))
    for axis,ax in zip('HV',axs):
        b=ref['cortes'][axis];c=r['cortes'][axis]
        tb,eb=read_pattern(BASE/('AB_'+axis+'.csv'));tc,ec=read_pattern(folder/('AB_'+axis+'.csv'))
        gb=10*np.log10(np.sum(abs(eb)**2,axis=1));gc=10*np.log10(np.sum(abs(ec)**2,axis=1))
        nb=gb-b['ganho_pico_dBi'];nc=gc-c['ganho_pico_dBi']
        mask,bounds=main_lobe_mask(tb,nb)
        interp=np.interp(tb[mask]+c['pico_graus']-b['pico_graus'],tc,nc)
        diff=float(np.max(abs(interp-nb[mask])));dw=abs(c['abertura_graus']/b['abertura_graus']-1)
        metrics[axis]=dict(erro_forma_lobo_alinhado_dB=diff,variacao_abertura_relativa=dw,maximo_graus=c['pico_graus'],limites_lobo_principal_referencia_graus=bounds,pontos_forma=int(mask.sum()))
        checks['forma_'+axis]=diff<=.75;checks['abertura_'+axis]=dw<=.05
        checks['apontamento_'+axis]=abs(c['pico_graus'])<=(.5 if axis=='H' else max(1.5,abs(b['pico_graus'])))
        label=folder.name+(' — convergida' if r['convergiu'] else ' — NÃO convergida')
        ax.plot(tb,nb,label='R12 convergida');ax.plot(tc,nc,label=label);ax.set(xlim=(-90,90),ylim=(-30,1),xlabel='Ângulo (graus)',ylabel='Ganho normalizado (dB)',title=axis);ax.grid(alpha=.3);ax.legend(fontsize=8)
    fig.suptitle('Diagramas em 5,17 GHz — A=B=0,5 W / 0°\n'+f"{r['passes']} passes | ΔS={100*r['delta_s']:.3f}% | "+('Convergida' if r['convergiu'] else 'PRELIMINAR — não convergida'));fig.tight_layout(rect=(0,0,1,.89));fig.savefig(folder/'comparacao_diagramas.png',dpi=170);plt.close(fig)
    result=dict(referencia=str(BASE),metodo_forma='Lobo principal da referencia limitado pelos primeiros minimos, apenas pontos >=-10dB; alinhar maximos. Lobos secundarios avaliados separadamente, nunca incluidos nesta mascara.',criterios=dict(ganho_min_dBi=12,erro_forma_alinhada_max_dB=.75,variacao_abertura_max=.05,degradacao_SLL_V_max_dB=.5,maximo_H_abs_graus=.5,maximo_V_abs_graus=1.5),metricas=metrics,verificacoes=checks,permitir_fast=bool(all(checks.values())))
    (folder/'diagrama_comparado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('DIAGRAMA_COMPARADO',json.dumps(result,ensure_ascii=False))

def peak_check(folder):
    plan=json.loads((folder/'pico_planejado.json').read_text(encoding='utf-8'))
    assert history(folder/'antes_pico_convergencia.txt')==history(folder/'apos_pico_convergencia.txt')==history(folder/'convergencia.txt')
    n=rf.Network(str(folder/'pico_fast.s2p'));fast=rf.Network(str(folder/'banda_fast.s2p'))
    assert n.nports==2 and len(n.f)==1
    np.testing.assert_allclose(n.f,[plan['frequencia_GHz']*1e9],atol=.01,rtol=0)
    np.testing.assert_allclose(n.z0,50)
    indices=np.flatnonzero(abs(fast.f-n.f[0])<.01);assert len(indices)==1
    sf=fast.s[indices[0]];sd=n.s[0]
    sigma=float(np.linalg.svd(sd,compute_uv=False)[0]);rec=float(np.max(abs(sd-sd.T)))
    assert sigma<1.0001 and rec<.001
    gs=[np.r_[s@np.ones(2),np.diag(s)] for s in [sd,sf]]
    assert all(np.max(abs(g))<1 for g in gs)
    vs=[(1+abs(g))/(1-abs(g)) for g in gs]
    power=float(1-.5*np.sum(abs(gs[0][:2])**2));assert 0<=power<=1
    error=float(np.max(abs(sd-sf)));assert error<.01
    solves=[r for p in folder.rglob('*.profile') for r in profile_matrix_solves(p.read_text(errors='replace')) if 'Solution - Pico_Fast' in r['grupos']]
    assert solves and all(r['nucleos']==14 and r['passe_adaptativo'] is None for r in solves)
    result=dict(tipo='Discrete',pontos=1,frequencia_GHz=float(n.f[0]/1e9),sem_adaptacao_adicional=True,
        VSWR_ativo=vs[0][:2].tolist(),VSWR_casado=vs[0][2:].tolist(),VSWR_Fast=vs[1].tolist(),
        diferenca_S_max=error,diferenca_VSWR_max=float(np.max(abs(vs[0]-vs[1]))),maior_singular=sigma,reciprocidade=rec,potencia_aceita_W=power,
        nucleos=[r['nucleos'] for r in solves],meta_VSWR_inclusiva=VSWR_TARGET,
        ativos_ate_meta=bool(max(vs[0][:2])<=VSWR_TARGET),casados_ate_meta=bool(max(vs[0][2:])<=VSWR_TARGET))
    result['todos_VSWR_ate_meta']=result['ativos_ate_meta'] and result['casados_ate_meta']
    (folder/'pico_auditado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PICO_AUDITADO',json.dumps(result,ensure_ascii=False))

def band(folder):
    full=(folder/'banda_fast.s2p').exists();tag='fast' if full else 'triagem3';kind='Fast' if full else 'Discrete'
    assert history(folder/('antes_'+tag+'_convergencia.txt'))==history(folder/('apos_'+tag+'_convergencia.txt'))==history(folder/'convergencia.txt')
    n=rf.Network(str(folder/('banda_fast.s2p' if full else 'triagem3.s2p')));nc=rf.Network(str(folder/'centro.s2p'))
    expected=np.arange(5090,5251,1 if full else 80)*1e6
    assert n.nports==2 and len(n.f)==len(expected)
    np.testing.assert_allclose(n.f,expected,rtol=0,atol=.01);np.testing.assert_allclose(n.z0,50)
    sv=np.linalg.svd(n.s,compute_uv=False)[:,0];rec=float(np.max(abs(n.s-n.s.transpose(0,2,1))))
    err=float(np.max(abs(n.s[80 if full else 1]-nc.s[0])));assert max(sv)<1.0001 and rec<.001 and err<.01
    gamma=np.column_stack((n.s@np.ones(2),np.diagonal(n.s,axis1=1,axis2=2)));assert np.all(abs(gamma)<1)
    vs=(1+abs(gamma))/(1-abs(gamma));power=1-.5*np.sum(abs(gamma[:,:2])**2,axis=1);assert min(power)>=0 and max(power)<=1
    with (folder/('vswr_banda.csv' if full else 'vswr_triagem3.csv')).open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['GHz','VSWR_ativo_A','VSWR_ativo_B','VSWR_casado_A','VSWR_casado_B']);w.writerows(np.column_stack((n.f/1e9,vs)))
    result=dict(tipo=kind,pontos=len(n.f),banda_completa=full,sem_adaptacao_adicional=True,diagramas_apenas_GHz=5.17,maior_singular=float(max(sv)),reciprocidade=rec,diferenca_S_centro=err,
        pior_VSWR_ativo=float(vs[:,:2].max()),pior_VSWR_casado=float(vs[:,2:].max()),pior_VSWR_geral=float(vs.max()),
        extremos=[dict(condicao=x,minimo=float(vs[:,i].min()),maximo=float(vs[:,i].max()),frequencia_max_GHz=float(n.f[np.argmax(vs[:,i])]/1e9)) for i,x in enumerate(['ativo_A','ativo_B','casado_A','casado_B'])],meta_VSWR_inclusiva=VSWR_TARGET,ativos_ate_meta=bool(vs[:,:2].max()<=VSWR_TARGET),casados_ate_meta=bool(vs[:,2:].max()<=VSWR_TARGET),todos_VSWR_ate_meta=bool(vs.max()<=VSWR_TARGET))
    result['potencia_aceita_W_min_max']=[float(min(power)),float(max(power))]
    sweep_group='Solution - '+('Banda_Fast' if full else 'Triagem3')
    records=[record for path in folder.rglob('*.profile') for record in profile_matrix_solves(path.read_text(errors='replace'))]
    solves=[r for r in records if sweep_group in r['grupos']]
    if full and not solves:
        # HFSS 2024 R2 registra o Fast diretamente sob Frequency Sweep,
        # sem Solution/Frequency; as solucoes discretas ficam em subgrupos.
        solves=[r for r in records if r['grupos']==['Solution Process','Frequency Sweep']]
    assert solves and all(x['nucleos']==14 and x['passe_adaptativo'] is None for x in solves),solves
    result['nucleos_solucoes_banda']=[x['nucleos'] for x in solves]
    result['grupos_solucoes_banda']=[x['grupos'] for x in solves]
    if full and (folder/'triagem3.s2p').exists():
        discrete=rf.Network(str(folder/'triagem3.s2p'))
        np.testing.assert_allclose(discrete.f,n.f[[0,80,160]],rtol=0,atol=.01)
        ds=float(np.max(abs(discrete.s-n.s[[0,80,160]])))
        dg=np.column_stack((discrete.s@np.ones(2),np.diagonal(discrete.s,axis1=1,axis2=2)))
        dvs=(1+abs(dg))/(1-abs(dg))
        result['conferencia_discrete']=dict(frequencias_GHz=(discrete.f/1e9).tolist(),diferenca_S_max=ds,diferenca_VSWR_max=float(np.max(abs(dvs-vs[[0,80,160]]))),pior_VSWR_ativo=float(dvs[:,:2].max()),pior_VSWR_casado=float(dvs[:,2:].max()))
        assert ds<.01,('Fast difere da verificacao discreta',ds)
        result['ativos_ate_meta'] &= bool(dvs[:,:2].max()<=VSWR_TARGET)
        result['casados_ate_meta'] &= bool(dvs[:,2:].max()<=VSWR_TARGET)
        result['todos_VSWR_ate_meta'] &= bool(dvs.max()<=VSWR_TARGET)
    (folder/('banda_auditada.json' if full else 'triagem3_auditada.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    fig,axs=plt.subplots(1,2,figsize=(11,4.6),sharey=True)
    baseline=rf.Network(str(BASE/'banda_fast.s2p'))
    gb=np.column_stack((baseline.s@np.ones(2),np.diagonal(baseline.s,axis1=1,axis2=2)))
    vb=(1+abs(gb))/(1-abs(gb))
    for ax,idx,title in zip(axs,[0,2],['AB em fase','Outra entrada em 50 Ω']):
        for k,pol in enumerate('AB'):
            color=['tab:blue','tab:orange'][k]
            ax.plot(baseline.f/1e9,vb[:,idx+k],ls='--',c=color,alpha=.5,label='R12 '+pol)
            ax.plot(n.f/1e9,vs[:,idx+k],'-' if full else 'o-',c=color,label='Nova '+pol)
        ax.axhline(VSWR_TARGET,c='red',ls=':',label=str(VSWR_TARGET).replace('.',','));ax.set(xlabel='GHz',ylabel='VSWR',title=title);ax.grid(alpha=.3);ax.legend(fontsize=8)
    fig.suptitle(folder.name+' — '+kind+' — '+str(len(n.f))+' frequências'+('' if full else '\nTrês pontos calculados; segmentos são apenas guias visuais'))
    fig.tight_layout(rect=(0,0,1,.86 if not full else .92));fig.savefig(folder/('vswr_banda.png' if full else 'vswr_triagem3.png'),dpi=170);plt.close(fig)
    if full:
        fig,axs=plt.subplots(1,2,figsize=(11,4.7),sharey=True)
        for ax,idx,title in zip(axs,[0,2],['Duas entradas iguais, em fase','Outra entrada terminada em 50 ohms']):
            for k,pol in enumerate('AB'):
                j=idx+k;i=int(np.argmax(vs[:,j]))
                ax.plot(n.f/1e9,vs[:,j],label=f'{pol}: max. {vs[i,j]:.4f} em {n.f[i]/1e9:.3f} GHz')
                ax.plot(n.f[i]/1e9,vs[i,j],'o',color=['tab:blue','tab:orange'][k])
            ax.axhline(VSWR_TARGET,c='red',ls=':',label='Meta 1,25')
            ax.set(xlabel='Frequencia (GHz)',ylabel='VSWR',title=title,ylim=(1.,max(1.3,float(vs.max())+.03)))
            ax.grid(alpha=.3);ax.legend(fontsize=8)
        fig.suptitle(folder.name+' | HFSS Fast — 161 pontos de saida\nMalha adaptada somente em 5,17 GHz; inclui os dois cabos fisicos de 50 mm')
        fig.tight_layout(rect=(0,0,1,.86));fig.savefig(folder/'vswr_banda_detalhe.png',dpi=170);plt.close(fig)
    print('BANDA_AUDITADA',json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('etapa',choices=['centro','fast','pico']);p.add_argument('pasta');a=p.parse_args();{'centro':center,'fast':band,'pico':peak_check}[a.etapa](Path(a.pasta))
