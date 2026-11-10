"""Conferencia das 16 portas, campos complexos e comparacao com R04/C12."""
from pathlib import Path
import json,csv,re,sys,os
import numpy as np
import skrf as rf
from scipy.signal import find_peaks
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from divisor_variantes_comparar import profile_matrix_solves
from oito_celulas_monitorar import progress
REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'automacao/r05'));sys.path.insert(0,str(REPO/'automacao/r06'))
from rede_carregada import read_pattern,beam
from auditar_malha import audit
ROOT=Path(os.environ.get('P2M21_OITO_ROOT','D:/dev/EMBRAER/P2M21/R14_Oito_Celulas'))
def save(n,data):(ROOT/n).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sll(theta,gain):
    front=np.flatnonzero(abs(theta)<=90);peak=front[np.argmax(gain[front])]
    mins,_=find_peaks(-gain);lo=max((i for i in mins if i<peak),default=front[0]);hi=min((i for i in mins if i>peak),default=front[-1])
    ids,_=find_peaks(gain);ids=[i for i in ids if abs(theta[i])<=90 and (i<lo or i>hi)]
    return dict(nivel_dB=float(max((gain[i] for i in ids),default=-999)-gain[peak]),
                limites_lobo_principal_graus=[float(theta[lo]),float(theta[hi])],
                lobos=[dict(angulo_graus=float(theta[i]),nivel_dB=float(gain[i]-gain[peak])) for i in ids])
def metrics(theta,gain):
    front=np.flatnonzero(abs(theta)<=90);peak=front[np.argmax(gain[front])];bw,lo,hi=beam(theta,gain)
    return dict(ganho_frontal_dBi=float(gain[np.argmin(abs(theta))]),pico_graus=float(theta[peak]),ganho_pico_dBi=float(gain[peak]),abertura_graus=float(bw),cruzamentos_graus=[float(lo),float(hi)],SLL=sll(theta,gain))
def main():
    cfg=json.loads((ROOT/'configuracao.json').read_text());state=json.loads((ROOT/'qualificacao.json').read_text())
    assert state['estado'] in ['SOLVE_EXPORTADO_AGUARDA_AUDITORIA','ANALISE_CONCLUIDA']
    conv=(ROOT/'convergencia.txt').read_text();integer=lambda p:int(re.search(p,conv)[1])
    passes=integer(r'Completed\s*:\s*(\d+)');consec=integer(r'Current Consecutive Passes\s*:\s*(\d+)')
    assert integer(r'Maximum\s*:\s*(\d+)')==cfg['max_passes'] and passes<=cfg['max_passes']
    prog=progress(ROOT);history=prog['historico'];save('historico_passes.json',prog)
    assert len(history)==passes
    delta=history[-1]['delta_s'];converged='Converged : Yes' in conv and delta<=cfg['max_delta_s'] and consec>=cfg['passes_consecutivos'] and passes>=cfg['min_passes']
    count=len(cfg['portas']);cells=len(cfg['celulas']);label=cfg['revisao']
    native=(ROOT/cfg['native']).read_text(errors='replace');entries=re.findall(r'SourceEntry\([^\n]+',native)
    assert len(entries)==count and all(("Magnitude='%.12gW'"%(1/count)) in x and "Phase='0deg'" in x for x in entries)
    profiles=list((ROOT/cfg['native']).with_suffix('.aedtresults').rglob('*.profile'))
    profile_selection='unico_perfil'
    if len(profiles)>1:
        all_profiles=list(profiles)
        selected=[]
        for path in profiles:
            metadata=path.with_suffix('.EMConvData')
            if not metadata.exists():continue
            text=metadata.read_text()
            if ("MaxPasses='%d'"%cfg['max_passes']) in text and ("MinPasses='%d'"%cfg['min_passes']) in text and abs(float(re.search(r"ConvTarget='([^']+)'",text)[1])-cfg['max_delta_s'])<1e-12:selected.append(path)
        profile_selection='criterios_do_EMConvData_correspondente'
        if not selected:
            # Algumas releases numeram profile/EMConvData diferentemente.
            # O historico completo e inequívoco 1..N identifica a continuacao;
            # alvo/min/max foram conferidos separadamente no export e EMConvData.
            for path in all_profiles:
                records=profile_matrix_solves(path.read_text(errors='replace'))
                if [r['passe_adaptativo'] for r in records if r['passe_adaptativo'] is not None]==list(range(1,passes+1)):selected.append(path)
            profile_selection='historico_adaptativo_completo_1_a_N'
        profiles=selected
    assert len(profiles)==1,profiles
    profile_text=profiles[0].read_text(errors='replace')
    recs=profile_matrix_solves(profile_text)
    fallback_warning='Matrix solver warning: Slow convergence, switch from Iterative Solver to Direct Solver'
    solver_evidence=dict(configurado='Iterativo, residual 1e-5',perfil=str(profiles[0]),selecao_perfil=profile_selection,
        avisos_troca_automatica_direto=profile_text.count(fallback_warning),
        aviso=fallback_warning if fallback_warning in profile_text else None,
        registros_matriz=recs)
    save('solver_efetivo.json',solver_evidence)
    adap=[x for x in recs if x['passe_adaptativo'] is not None]
    assert [x['passe_adaptativo'] for x in adap]==list(range(1,passes+1)) and all(x['nucleos']==14 for x in adap)
    save('recursos_matriz.json',recs)
    mesh=audit(ROOT);save('malha.json',mesh)
    n=rf.Network(str(ROOT/('centro.s%dp'%count)));assert n.nports==count and len(n.f)==1 and n.f[0]==5.17e9
    np.testing.assert_allclose(n.z0,50)
    names=[x.strip().removesuffix(':1') for x in n.port_names]
    assert set(names)==set(p['name'] for p in cfg['portas'])
    s=n.s[0];inc=np.ones(count)/np.sqrt(count);ref=s@inc;gamma=ref/inc;accept=float(1-np.sum(abs(ref)**2))
    def vs(z):
        return [(float((1+abs(v))/(1-abs(v))) if abs(v)<1 else None) for v in z]
    sigma=float(np.linalg.svd(s,compute_uv=False)[0]);recip=float(abs(s-s.T).max())
    result=dict(frequencia_GHz=5.17,radiadores=cfg['radiadores'],celulas=cells,portas=count,potencia_total_W=1,potencia_por_porta_W=1/count,fase_graus=0,
        passes=passes,max_passes=cfg['max_passes'],delta_s=delta,alvo_delta_s=cfg['max_delta_s'],consecutivos=consec,convergiu=converged,nucleos=14,solver_efetivo=solver_evidence,
        ordem_portas=names,VSWR_ativo=vs(gamma),VSWR_casado=vs(np.diag(s)),potencia_aceita_W=accept,
        maior_singular=sigma,reciprocidade=recip,major=mesh['reparos_major'],minor=mesh['reparos_minor'],cortes={},grupos_polarizacao={},recomposicao={},potencia={},historico_cache=history[-2:])
    curves={};oldcurves={};old=REPO/cfg['referencia_historica']/'resultados'
    for axis in 'HV':
        t,e=read_pattern(ROOT/('ALL_'+axis+'.csv'));gain=10*np.log10(np.sum(abs(e)**2,axis=1));curves[axis]=(t,gain)
        fields=[]
        for name in names:
            ti,ei=read_pattern(ROOT/(name+'_'+axis+'.csv'));np.testing.assert_array_equal(t,ti);fields.append(ei)
        recomposed=np.sum(fields,axis=0)/np.sqrt(count);err=float(np.max(abs(recomposed-e))/np.max(abs(e)))
        result['recomposicao'][axis]=err;assert err<1e-7
        result['cortes'][axis]=metrics(t,gain)
        for pol in 'AB':
            tp,ep=read_pattern(ROOT/('POL_'+pol+'_'+axis+'.csv'));np.testing.assert_array_equal(t,tp)
            expected=sum(fields[i] for i,name in enumerate(names) if name.endswith('_'+pol))/np.sqrt(count/2)
            assert np.max(abs(expected-ep))/np.max(abs(ep))<1e-7
            gp=10*np.log10(np.sum(abs(ep)**2,axis=1));result['grupos_polarizacao'].setdefault(pol,{})[axis]=metrics(t,gp)
        with (ROOT/('ALL_'+axis+'.csv')).open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
        assert len(rows)==1441 and all(float(r['Freq [GHz]'])==5.17 for r in rows)
        row=min(rows,key=lambda r:abs(float(r['Theta [deg]'])))
        gr,ga,di=[float(row[k]) for k in ['dB(RealizedGainTotal) []','dB(GainTotal) []','dB(DirTotal) []']]
        result['potencia'][axis]=dict(eficiencia_radiacao=10**((ga-di)/10),eficiencia_total=10**((gr-di)/10),erro_aceita_W=abs(10**((gr-ga)/10)-accept))
        to,eo=read_pattern(old/('Uniforme_'+axis+'.csv'));go=10*np.log10(np.sum(abs(eo)**2,axis=1));oldcurves[axis]=(to,go)
    result['fisica_ok']=bool(sigma<=1.0001 and recip<=1e-5 and 0<=accept<=1 and mesh['reparos_major']==0 and
        all(v['eficiencia_radiacao']<=1.0001 and v['erro_aceita_W']<1e-4 for v in result['potencia'].values()))
    result['metas']=dict(ganho_total_21dBi=result['cortes']['H']['ganho_frontal_dBi']>=21,
        apontamento_H=abs(result['cortes']['H']['pico_graus'])<=.5,apontamento_V=abs(result['cortes']['V']['pico_graus'])<=.5)
    result['limite_monitoramento_campo_dB']=cfg['monitoramento_estabilidade_campo_dB']
    cached_center=history[-1]['campos_dBi'].get('R14_Campo_00')
    result['cache_confere_fontes_finais']=bool(cached_center is not None and abs(cached_center-result['cortes']['H']['ganho_frontal_dBi'])<1e-6)
    result['estavel_nove_sondas']=bool(result['cache_confere_fontes_finais'] and len(history)>=3 and all(p['delta_campo_max_dB'] is not None and p['delta_campo_max_dB']<=cfg['monitoramento_estabilidade_campo_dB'] for p in history[-2:]))
    result['validado_numericamente']=bool(converged and result['fisica_ok'] and result['estavel_nove_sondas'])
    result['qualificacao_mimo_por_entrada']=False
    save('resultado.json',result)
    fig,(ax,axv)=plt.subplots(1,2,figsize=(14,6.3),gridspec_kw={'width_ratios':[1.05,1]})
    im=ax.imshow(20*np.log10(np.maximum(abs(s),1e-12)),vmin=-60,vmax=0,cmap='viridis')
    ax.set_xticks(range(count),names,rotation=90,fontsize=7);ax.set_yticks(range(count),names,fontsize=7)
    ax.set_title('Matriz S: dB; referencia de 50 ohms')
    fig.colorbar(im,ax=ax,fraction=.046,pad=.04,label='dB')
    ix=np.arange(count)
    axv.bar(ix-.18,[x if x is not None else np.nan for x in result['VSWR_ativo']],width=.36,label=f'{count} entradas ativas')
    axv.bar(ix+.18,[x if x is not None else np.nan for x in result['VSWR_casado']],width=.36,label='Outras entradas casadas')
    axv.set_xticks(ix,names,rotation=90,fontsize=7);axv.set_ylabel('VSWR');axv.set_ylim(bottom=1)
    axv.legend(fontsize=8);axv.grid(axis='y',alpha=.25)
    fig.suptitle(f'{label} — 5,17 GHz — acoplamento e casamento das {count} conexoes\n'+('Convergencia DeltaS atendida' if converged else 'PRELIMINAR: NAO CONVERGIDO'))
    fig.tight_layout(rect=(0,0,1,.91));fig.savefig(ROOT/'acoplamento_vswr.png',dpi=175);plt.close(fig)
    status='Convergencia DeltaS atendida' if converged else 'PRELIMINAR: NAO CONVERGIDO'
    if not result['fisica_ok']:status+='; ressalva fisica'
    if not result['estavel_nove_sondas']:status+='; estabilidade de campo nao confirmada'
    fig,axs=plt.subplots(1,2,figsize=(12,5.6))
    for ax,axis in zip(axs,'HV'):
        t,g=curves[axis];to,go=oldcurves[axis]
        est=np.genfromtxt(ROOT/('estimativa_'+axis+'.csv'),delimiter=',',skip_header=1)
        ax.plot(t,g,label=f"{cells} celulas, 48 x {cfg['passo_horizontal_mm']} mm; {passes} passes",lw=1.7)
        ax.plot(to,go,ls='--',color='#999',label='R04: individuais, 52,6 x 40 mm; nao convergido')
        ax.plot(est[:,0],est[:,1],ls=':',color='#c0731d',label='C12 isolada + AF; sem acoplamento')
        ax.set(xlim=(-90,90),ylim=(-20,26),xlabel='Angulo (graus)',ylabel='Ganho realizado total (dBi)',title=axis)
        ax.grid(alpha=.25);ax.legend(fontsize=7,loc='lower left')
    fig.suptitle('5,17 GHz — 1 W total, todas as entradas iguais e em fase\n'+status)
    fig.text(.5,.015,'Geometrias, passos, refletores e redes diferentes: comparacao historica, sem isolar a causa das diferencas.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.05,1,.90));fig.savefig(ROOT/'comparacao_diagramas.png',dpi=175);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(11,7),subplot_kw={'projection':'polar'})
    for ax,axis in zip(axs,'HV'):
        t,g=curves[axis];c=result['cortes'][axis]
        ax.plot(np.deg2rad(t),10**((g-g.max())/20));ax.set_theta_zero_location('N');ax.set_theta_direction(-1)
        ax.set_ylim(0,1.05);ax.set_rticks([.25,.5,.75,1]);ax.set_rlabel_position(75)
        ax.set_title(f"{axis}: pico {c['pico_graus']:+.2f} graus; abertura {c['abertura_graus']:.2f} graus",pad=22,fontsize=10)
    fig.suptitle(f'{label} — polar E/Emax — 5,17 GHz\n'+status)
    fig.text(.5,.04,f"14 nucleos | {passes} passes | DeltaS {delta:.6f} | {count} portas de {1/count:.4g} W / 0 graus",ha='center')
    fig.subplots_adjust(top=.77,bottom=.16,wspace=.3);fig.savefig(ROOT/'polar_HV.png',dpi=175);plt.close(fig)
    table=[]
    for label,c in [(label,result['cortes']),('R04_individuais_nao_convergido',{a:metrics(*oldcurves[a]) for a in 'HV'})]:
        table.append(dict(versao=label,ganho_dBi=c['H']['ganho_frontal_dBi'],H_graus=c['H']['abertura_graus'],V_graus=c['V']['abertura_graus'],picoH_graus=c['H']['pico_graus'],picoV_graus=c['V']['pico_graus']))
    save('comparacao.json',table)
    with (ROOT/'comparacao.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
    state.update(estado='ANALISE_CONCLUIDA',convergiu=converged,validado_numericamente=result['validado_numericamente'],resultado='resultado.json');save('qualificacao.json',state)
    print(json.dumps({k:result[k] for k in ['passes','delta_s','convergiu','fisica_ok','metas','cortes','VSWR_ativo']},indent=2))
if __name__=='__main__':main()
