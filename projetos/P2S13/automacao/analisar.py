"""Mede resultados HFSS reais; separa metas RF, convergencia e verificacao fisica."""
from pathlib import Path
import os,sys,json,re,csv,textwrap
import numpy as np
import skrf as rf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
REPO=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(REPO/'projetos/P2M21/automacao'),str(REPO/'automacao/r05'),str(REPO/'automacao/r06')]
from oito_celulas_analisar import metrics as metrics_original
from oito_celulas_monitorar import progress
from divisor_variantes_comparar import profile_matrix_solves
from auditar_malha import audit
from rede_carregada import read_pattern
ROOT=Path(os.environ['P2S13_ROOT'])
def save(n,v):(ROOT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def metrics(t,g):
    r=metrics_original(t,g)
    if not r['SLL']['lobos']:
        r['SLL']['nivel_dB']=None
        r['SLL']['observacao']='Nenhum maximo secundario identificado no hemisferio frontal; nao atribuir um nivel numerico ficticio.'
    return r
def main():
    cfg=json.loads((ROOT/'configuracao.json').read_text());state=json.loads((ROOT/'qualificacao.json').read_text())
    assert state['estado'] in ['SOLVE_EXPORTADO_AGUARDA_AUDITORIA','ANALISE_CONCLUIDA']
    conv=(ROOT/'convergencia.txt').read_text();value=lambda p:int(re.search(p,conv)[1])
    passes=value(r'Completed\s*:\s*(\d+)');consec=value(r'Current Consecutive Passes\s*:\s*(\d+)')
    maximum=int(cfg['max_passes']);minimum=int(cfg['min_passes'])
    assert value(r'Maximum\s*:\s*(\d+)')==maximum and passes<=maximum
    assert value(r'Minimum\s*:\s*(\d+)')==minimum
    if maximum!=6:
        assert maximum==minimum==8 and cfg['passes_iniciais']==6 and cfg['passes_adicionais_autorizados']==2
        assert json.loads((ROOT/'continuidade_auditada.json').read_text())['aprovado']
    history=progress(ROOT);save('historico_passes.json',history);hist=history['historico'];assert len(hist)==passes
    delta=hist[-1]['delta_s'];converged='Converged : Yes' in conv and delta<=.05 and consec>=2 and passes>=minimum
    native=(ROOT/cfg['native']).read_text(errors='replace');entries=re.findall(r'SourceEntry\([^\n]+',native)
    method=cfg.get('mesh_method','AnsoftClassic')
    assert "MeshMethod='%s'"%method in native
    assert 'UseFlexMeshingForTAUvolumeMesh='+str(cfg.get('tau_flex',False)).lower() in native
    assert 'UseAlternativeMeshMethodsAsFallBack=false' in native
    assert len(entries)==4 and all("Magnitude='0.25W'" in x and "Phase='0deg'" in x for x in entries)
    # O monitor seleciona EMConvData pelos criterios atuais; nao usar perfil
    # historico de outro limite de passes apenas por ser o primeiro arquivo.
    profiles=[Path(history['fonte']).with_suffix('.profile')]
    assert profiles[0].is_file(),profiles
    profiles_with_solves=[(p,profile_matrix_solves(p.read_text(errors='replace'))) for p in profiles]
    profiles_with_solves=[(p,r) for p,r in profiles_with_solves if r]
    assert len(profiles_with_solves)==1,[(str(p),len(r)) for p,r in profiles_with_solves]
    recs=profiles_with_solves[0][1];adap=[x for x in recs if x['passe_adaptativo'] is not None]
    if cfg.get('passes_iniciais') and [x['passe_adaptativo'] for x in adap]==[7,8]:
        previous=json.loads((ROOT/'referencia6/recursos_matriz.json').read_text())
        assert [x['passe_adaptativo'] for x in previous if x['passe_adaptativo'] is not None]==list(range(1,7))
        recs=previous+recs;adap=[x for x in recs if x['passe_adaptativo'] is not None]
    assert [x['passe_adaptativo'] for x in adap]==list(range(1,passes+1)) and all(x['nucleos']==14 for x in adap)
    save('recursos_matriz.json',recs)
    if list(ROOT.rglob('nominalmesh.g3derr')):
        mesh=audit(ROOT)
    else:
        initial=json.loads((ROOT/'malha_inicial.json').read_text())
        messages=json.loads((ROOT/'mensagens.json').read_text())
        assert method=='AnsoftClassic' and not cfg.get('tau_flex',False)
        assert initial['reparos_major']==initial['reparos_minor']==0
        assert not any(re.search(r'mesh repair|mesh leak|outlines.*preserv|non-planar mesh',m,re.I) for m in messages)
        mesh=dict(reparos_major=0,reparos_minor=0,arquivo_avisos_presente=False,
          origem='Classic estrito: malha inicial auditada sem reparos e solve RF sem mensagens de reparo, vazamento, contorno ou planaridade; nenhum g3derr gerado.')
    save('malha.json',mesh)
    n=rf.Network(str(ROOT/'centro.s4p'));assert n.nports==4 and len(n.f)==1 and n.f[0]==5.17e9;np.testing.assert_allclose(n.z0,50)
    names=[s.strip().removesuffix(':1') for s in n.port_names];assert set(names)==set(p['name'] for p in cfg['portas'])
    s=n.s[0];inc=np.ones(4)/2;ref=s@inc;gamma=ref/inc;accept=float(1-np.sum(abs(ref)**2))
    vs=lambda x:[float((1+abs(z))/(1-abs(z))) if abs(z)<1 else None for z in x]
    r=dict(variante=cfg['revisao'],frequencia_GHz=5.17,passes=passes,delta_s=delta,convergiu=converged,nucleos=14,mesh_method=method,tau_flex=cfg.get('tau_flex',False),
        potencia_total_W=1,potencia_por_porta_W=.25,fase_graus=0,ordem_portas=names,VSWR_ativo=vs(gamma),VSWR_casado=vs(np.diag(s)),
        maior_singular=float(np.linalg.svd(s,compute_uv=False)[0]),reciprocidade=float(abs(s-s.T).max()),potencia_aceita_W=accept,
        major=mesh['reparos_major'],minor=mesh['reparos_minor'],cortes={},recomposicao={},potencia={})
    curves={}
    for axis in 'HV':
        t,e=read_pattern(ROOT/('ALL_'+axis+'.csv'));gain=10*np.log10(np.sum(abs(e)**2,axis=1));curves[axis]=(t,gain)
        fields=[]
        for name in names:
            ti,ei=read_pattern(ROOT/(name+'_'+axis+'.csv'));np.testing.assert_array_equal(t,ti);fields.append(ei)
        err=float(np.max(abs(sum(fields)/2-e))/np.max(abs(e)));assert err<1e-7;r['recomposicao'][axis]=err
        r['cortes'][axis]=metrics(t,gain)
        with (ROOT/('ALL_'+axis+'.csv')).open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
        assert len(rows)==1441 and all(float(row['Freq [GHz]'])==5.17 for row in rows)
        row=min(rows,key=lambda row:abs(float(row['Theta [deg]'])))
        gr,ga,di=[float(row[k]) for k in ['dB(RealizedGainTotal) []','dB(GainTotal) []','dB(DirTotal) []']]
        r['potencia'][axis]=dict(eficiencia_radiacao=10**((ga-di)/10),eficiencia_total=10**((gr-di)/10),erro_aceita_W=abs(10**((gr-ga)/10)-accept))
    r['fisica_ok']=bool(r['maior_singular']<=1.0001 and r['reciprocidade']<=1e-5 and 0<=accept<=1 and r['major']==0 and all(v['eficiencia_radiacao']<=1.0001 and v['erro_aceita_W']<1e-4 for v in r['potencia'].values()))
    r['verificacoes']=dict(passividade=bool(r['maior_singular']<=1.0001),
      reciprocidade=bool(r['reciprocidade']<=1e-5),limite_reciprocidade=1e-5,
      potencia_aceita=bool(0<=accept<=1),malha_sem_major=r['major']==0,
      eficiencia_e_balanco=bool(all(v['eficiencia_radiacao']<=1.0001 and v['erro_aceita_W']<1e-4 for v in r['potencia'].values())))
    cached=hist[-1]['campos_dBi'].get('P2S13_Campo_00');r['cache_confere']=bool(cached is not None and abs(cached-r['cortes']['H']['ganho_frontal_dBi'])<1e-6)
    r['estavel_nove_sondas']=bool(r['cache_confere'] and len(hist)>=3 and all(p['delta_campo_max_dB'] is not None and p['delta_campo_max_dB']<=.1 for p in hist[-2:]))
    h,v=r['cortes']['H'],r['cortes']['V'];r['metas_numericas']=dict(ganho_13dBi=h['ganho_frontal_dBi']>=13,horizontal_99_121=99<=h['abertura_graus']<=121,vertical_16p2_19p8=16.2<=v['abertura_graus']<=19.8)
    r['validado_numericamente']=bool(converged and r['fisica_ok'] and r['estavel_nove_sondas'])
    r['aprovado']=bool(r['validado_numericamente'] and all(r['metas_numericas'].values()))
    save('resultado.json',r)
    status='Convergencia DeltaS atendida' if converged else 'PRELIMINAR — nao convergido'
    if converged and not r['estavel_nove_sondas']:status+='; estabilidade de campo pendente'
    if not r['fisica_ok']:
        failed=[k for k,v in r['verificacoes'].items() if v is False]
        status+='; auditoria numerica reprovada: '+', '.join(failed)
    fig,axs=plt.subplots(1,2,figsize=(12,5))
    for ax,axis in zip(axs,'HV'):
        t,g=curves[axis];ax.plot(t,g,label=cfg['revisao']);ax.set(xlim=(-90,90),ylim=(-25,20),title=axis,xlabel='Angulo (graus)',ylabel='Ganho realizado total (dBi)');ax.grid(alpha=.25)
        ax.axhline(13,c='#999',ls='--',lw=.8)
    wrapped_status='\n'.join(textwrap.wrap(status,width=95))
    fig.suptitle(f"P2S13 — 5,17 GHz — quatro portas iguais/em fase, 1 W total\n{wrapped_status}\n{passes} passes | DeltaS={delta:.6f}",fontsize=11)
    fig.tight_layout(rect=(0,0,1,.86));fig.savefig(ROOT/'diagramas_HV.png',dpi=170);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(11,6.6),subplot_kw={'projection':'polar'})
    for ax,axis in zip(axs,'HV'):
        t,g=curves[axis];c=r['cortes'][axis];ax.plot(np.deg2rad(t),10**((g-g.max())/20));ax.set_theta_zero_location('N');ax.set_theta_direction(-1);ax.set_ylim(0,1.05);ax.set_rticks([.25,.5,.75,1]);ax.set_rlabel_position(75)
        ax.set_title(f"{axis}: largura {c['abertura_graus']:.2f} graus; pico {c['pico_graus']:+.2f} graus",fontsize=10,pad=22)
    fig.suptitle(f"{cfg['revisao']} — E/Emax — 5,17 GHz\n{wrapped_status}",fontsize=11)
    fig.text(.5,.025,f"G frontal {h['ganho_frontal_dBi']:.3f} dBi | DeltaS {delta:.6f} | 14 nucleos | {passes} passes",ha='center');fig.subplots_adjust(top=.77,bottom=.14,wspace=.25);fig.savefig(ROOT/'polar_HV.png',dpi=170);plt.close(fig)
    state.update(estado='ANALISE_CONCLUIDA',convergiu=converged,aprovado=r['aprovado']);save('qualificacao.json',state)
    print(json.dumps({k:r[k] for k in ['variante','passes','delta_s','convergiu','fisica_ok','metas_numericas','cortes','VSWR_ativo']},indent=2))
if __name__=='__main__':main()
