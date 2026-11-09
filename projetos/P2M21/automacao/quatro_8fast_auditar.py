"""Audita continuidade dos seis passes e dados do Fast; nao executa solver."""
from pathlib import Path
import json,re,hashlib,sys,csv
import numpy as np
import skrf as rf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from quatro_ajustar_analisar import analyze

ROOT=Path('D:/dev/EMBRAER/P2M21/R12_Quatro_8Passes_Fast');F=ROOT/'antena';B=ROOT/'referencia6'
def write(n,x):(ROOT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def native(p):return p.read_text(errors='replace')
def block(t,n):return t.split("$begin '"+n+"'",1)[1].split("$end '"+n+"'",1)[0]
def geometry(t):return [b.split("$end 'GeometryPart'",1)[0] for b in t.split("$begin 'GeometryPart'")[1:]]
def history(p):
    return [[int(a),int(b),None if c=='N/A' else float(c)] for a,b,c in re.findall(r'^\s*(\d+)\|\s*(\d+)\|\s*([\d.eE+-]+|N/A)\|',p.read_text(),re.M)]
def unchanged():
    a=native(B/'P2M21_4_elementos.aedt');b=native(F/'P2M21_4_elementos.aedt')
    assert geometry(a)==geometry(b)
    assert len(geometry(a))>0
    for name in ['BoundarySetup','MaterialDef','MeshSetup']:
        if "$begin '"+name+"'" in a:assert block(a,name)==block(b,name),name
    sources=re.findall(r'SourceEntry\([^\n]+',b)
    assert len(sources)==2 and all("Magnitude='0.5W'" in s and "Phase='0deg'" in s for s in sources)
    return a,b

def prepare():
    a,b=unchanged()
    before=block(a,'AnalysisSetup');after=block(b,'AnalysisSetup')
    expected=before.replace('MaximumPasses=6','MaximumPasses=8').replace('MinimumPasses=2','MinimumPasses=8')
    normalized_target=False
    if expected!=after:
        # AEDT normaliza o default da base mista mesmo com lambda desativado.
        # Aceitar somente essa diferenca inativa, nunca alterar o criterio DeltaS.
        for t in [before,after]:
            assert all(s in t for s in ['DoLambdaRefine=false','SetLambdaTarget=false','BasisOrder=-1'])
        assert expected.replace('\n\t\t\t\t\tTarget=0.3333','\n\t\t\t\t\tTarget=0.6667')==after
        normalized_target=True
    origin=json.loads((ROOT/'origem.json').read_text());cache=[]
    for entry in origin['arquivos_resultados_copiados']:
        path=F/entry['arquivo']
        if path.name in ['native.adp','current.ngmesh','fields.evtrs_0','fields.evtrs_1','fields.evtrs_hyd']:
            assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'];cache.append(entry['arquivo'])
    assert len(cache)==5
    assert history(B/'convergencia.txt')==history(ROOT/'antes_convergencia.txt')
    write('preparacao_auditada.json',dict(aprovado=True,geometria_blocos=len(geometry(a)),geometria_materiais_fronteiras_malha_inalterados=True,alteracoes_ativas_setup=['MaximumPasses6->8','MinimumPasses2->8'],default_inativo_Target_normalizado=normalized_target,lambda_refinement=False,cache_malha_campos_byte_a_byte=cache,historico6_preservado=True,native_sha256=hashlib.sha256((F/'P2M21_4_elementos.aedt').read_bytes()).hexdigest()))
    print('PREPARACAO_AUDITADA_SEM_RESET')

def center():
    unchanged();old=history(B/'convergencia.txt');new=history(F/'convergencia.txt')
    assert len(old)==6 and len(new)==8 and new[:6]==old,(old,new)
    r=analyze(F);assert r['passes']==8 and r['fisica_ok']
    original=json.loads((B/'resultado.json').read_text())
    delta=dict(ganho_frontal_dB=r['cortes']['H']['ganho_frontal_dBi']-original['cortes']['H']['ganho_frontal_dBi'],
       maximo_H_graus=r['cortes']['H']['pico_graus']-original['cortes']['H']['pico_graus'],maximo_V_graus=r['cortes']['V']['pico_graus']-original['cortes']['V']['pico_graus'],
       abertura_H_graus=r['cortes']['H']['abertura_graus']-original['cortes']['H']['abertura_graus'],abertura_V_graus=r['cortes']['V']['abertura_graus']-original['cortes']['V']['abertura_graus'],
       VSWR_ativo=(np.array(r['VSWR_ativo'])-original['VSWR_ativo']).tolist(),VSWR_casado=(np.array(r['VSWR_casado'])-original['VSWR_casado']).tolist())
    write('continuidade_auditada.json',dict(aprovado=True,primeiros_seis_identicos=True,novos_passes=[7,8],historico=new,convergiu=r['convergiu'],delta_s=r['delta_s'],comparacao6_8=delta,escopo='Aprovado refere-se a continuidade e verificacoes fisicas; nao significa todas as metas de RF aprovadas.'))
    print('EXATAMENTE_DOIS_PASSES_ADICIONAIS',json.dumps(delta))

def fast():
    unchanged();assert history(ROOT/'apos_fast_convergencia.txt')==history(F/'convergencia.txt')
    n=rf.Network(str(F/'banda_fast.s2p'));center_n=rf.Network(str(F/'centro.s2p'))
    expected=np.arange(5090,5251)*1e6
    assert n.nports==2 and len(n.f)==161;np.testing.assert_allclose(n.f,expected,rtol=0,atol=.01)
    assert np.all(np.isfinite(n.s));np.testing.assert_allclose(n.z0,50)
    sv=np.linalg.svd(n.s,compute_uv=False)[:,0];rec=np.max(abs(n.s-n.s.transpose(0,2,1)),axis=(1,2))
    assert max(sv)<1.0001 and max(rec)<.001,(max(sv),max(rec))
    active=n.s@np.ones(2);matched=np.diagonal(n.s,axis1=1,axis2=2)
    assert np.all(abs(active)<1) and np.all(abs(matched)<1)
    va=(1+abs(active))/(1-abs(active));vc=(1+abs(matched))/(1-abs(matched))
    pa=1-.5*np.sum(abs(active)**2,axis=1);assert np.all(pa>=0) and np.all(pa<=1)
    ix=80;err=float(np.max(abs(n.s[ix]-center_n.s[0])))
    assert err<.01,('Fast e adaptativo divergentes no centro',err)
    rows=[dict(frequencia_GHz=float(f/1e9),VSWR_ativo_A=float(a[0]),VSWR_ativo_B=float(a[1]),VSWR_casado_A=float(c[0]),VSWR_casado_B=float(c[1]),potencia_aceita_AB_W=float(p)) for f,a,c,p in zip(n.f,va,vc,pa)]
    with (ROOT/'vswr_banda_fast.csv').open('w',newline='',encoding='utf-8') as stream:
        w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    extremes={}
    for group,arr in [('ativo',va),('casado',vc)]:
        extremes[group]=[dict(porta=pol,minimo=float(arr[:,k].min()),maximo=float(arr[:,k].max()),frequencia_max_GHz=float(n.f[np.argmax(arr[:,k])]/1e9),pontos_reprovados_1_3=[float(f/1e9) for f,v in zip(n.f,arr[:,k]) if v>=1.3]) for k,pol in enumerate('AB')]
    write('auditoria_fast.json',dict(aprovado_fisica=True,tipo='Fast',pontos=161,faixa_GHz=[5.09,5.25],passo_MHz=1,sem_adaptacao_adicional=True,diagramas_apenas_GHz=5.17,maior_singular=float(max(sv)),residuo_reciprocidade=float(max(rec)),diferenca_S_centro_fast_adaptativo=err,VSWR=extremes,todos_VSWR_menores_1_3=bool(max(va.max(),vc.max())<1.3),ganho_banda_verificado=False))
    fig,axs=plt.subplots(1,2,figsize=(11,5),sharey=True)
    for ax,values,title in zip(axs,[va,vc],['Duas entradas iguais em fase','Outra entrada casada em 50 Ω']):
        for k,pol in enumerate('AB'):ax.plot(n.f/1e9,values[:,k],label='Entrada '+pol,lw=1.7)
        ax.axhline(1.3,c='red',ls='--',lw=1,label='Meta <1,3');ax.axvline(5.17,c='gray',lw=.7)
        ax.set(xlabel='Frequência (GHz)',ylabel='VSWR',title=title);ax.grid(alpha=.25);ax.legend()
    r=json.loads((F/'resultado.json').read_text());fig.suptitle(f"Sweep Fast — 5,09 a 5,25 GHz — 14 núcleos\nMalha adaptada em 5,17 GHz; 8 passes; ΔS {100*r['delta_s']:.3f}%; convergiu: {r['convergiu']}")
    fig.tight_layout(rect=(0,0,1,.87));fig.savefig(ROOT/'vswr_banda_fast.png',dpi=170);plt.close(fig)
    write('qualificacao.json',dict(estado='CENTRO8_E_FAST_CONCLUIDOS_REVISAR',convergiu=r['convergiu'],ganho_frontal_dBi=r['cortes']['H']['ganho_frontal_dBi'],fast_pontos=161,ganho_apenas_GHz=5.17))
    print('FAST_AUDITADO',json.dumps(extremes))

if __name__=='__main__':{'preparar':prepare,'centro':center,'fast':fast}[sys.argv[1]]()
