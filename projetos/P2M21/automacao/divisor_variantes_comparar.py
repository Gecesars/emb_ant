"""Comparar diagramas dos ensaios de retorno/divisores, sem executar solver."""
import argparse,csv,json,re,sys
from pathlib import Path
import numpy as np
import skrf as rf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

REPO=Path(__file__).resolve().parents[3]
ROOT=Path('D:/dev/EMBRAER/P2M21/R09_Divisor_Simetria')
BASE=Path('D:/dev/EMBRAER/P2M21/R08_Dois_Verticais_Sem_Suportes')
sys.path.insert(0,str(REPO/'automacao/r05'))
sys.path.insert(0,str(REPO/'automacao/r06'))
from rede_carregada import beam,read_pattern
from auditar_malha import audit

def profile_matrix_solves(text):
    """Distingue passes adaptativos das frequencias anexadas ao mesmo perfil."""
    stack=[];records=[]
    for raw in text.replace("\\'","'").splitlines():
        line=raw.strip()
        if line=="$begin 'ProfileGroup'":stack.append(None)
        elif line=="$end 'ProfileGroup'":
            assert stack,'Fim de grupo sem inicio';stack.pop()
        elif line.startswith("Name='") and stack:stack[-1]=line[6:-1]
        elif line.startswith("ProfileItem('Matrix Solve'"):
            match=re.search(r"'Cores', (\d+)",line);assert match,line
            passes=[int(m[1]) for name in stack if name for m in [re.fullmatch(r'Adaptive Pass (\d+)',name)] if m]
            assert len(passes)<=1,stack
            records.append(dict(passe_adaptativo=passes[0] if passes else None,nucleos=int(match[1]),grupos=[n for n in stack if n],linha=line))
    assert not stack,'Perfil incompleto'
    return records

def assess(folder):
    cfg=json.loads((folder/'configuracao.json').read_text(encoding='utf-8'))
    native=(folder/cfg['native']).read_text(errors='replace')
    entries=re.findall(r'SourceEntry\([^\n]+',native)
    assert len(entries)==2 and all("Magnitude='0.5W'" in x and "Phase='0deg'" in x for x in entries)
    conv=(folder/'convergencia.txt').read_text()
    passes=int(re.search(r'Completed\s*:\s*(\d+)',conv)[1]);maxpass=int(re.search(r'Maximum\s*:\s*(\d+)',conv)[1])
    assert passes<=maxpass==cfg['max_passes']
    delta=float(re.search(r'Current\s*:\s*([\d.eE+-]+)',conv)[1])
    consecutive=int(re.search(r'Current Consecutive Passes\s*:\s*(\d+)',conv)[1])
    required=int(re.search(r'Target Consecutive Passes\s*:\s*(\d+)',conv)[1])
    native_yes='Converged : Yes' in conv
    target=float(cfg.get('max_delta_s',.04))
    exported_target=float(re.search(r'^Target\s*:\s*([\d.eE+-]+)',conv,re.M)[1])
    assert abs(target-exported_target)<1e-12,(target,exported_target)
    converged=native_yes and delta<=target and consecutive>=required and passes>=cfg['min_passes']
    profiles=list(folder.rglob('*.profile'))
    if len(profiles)>1:
        # Continuacoes preservam o perfil antigo; selecionar pelos criterios
        # efetivos, sem aceitar um registro historico apenas por data/nome.
        selected=[]
        for profile_path in profiles:
            meta=profile_path.with_suffix('.EMConvData')
            if not meta.exists():continue
            t=meta.read_text()
            if ("MaxPasses='%d'"%cfg['max_passes']) in t and ("MinPasses='%d'"%cfg['min_passes']) in t:
                actual=float(re.search(r"ConvTarget='([^']+)'",t)[1])
                if abs(actual-target)<1e-12:selected.append(profile_path)
        profiles=selected
    assert len(profiles)==1,profiles
    profile=profiles[0].read_text(errors='replace').replace("\\'","'")
    matrix_records=profile_matrix_solves(profile)
    adaptive_records=[x for x in matrix_records if x['passe_adaptativo'] is not None]
    assert [x['passe_adaptativo'] for x in adaptive_records]==list(range(1,passes+1)),adaptive_records
    cores=[x['nucleos'] for x in adaptive_records]
    assert len(cores)==passes and set(cores)=={14},cores
    mesh=audit(folder)
    n=rf.Network(str(folder/'centro.s2p'));assert n.nports==2 and len(n.f)==1 and n.f[0]==5.17e9
    s=n.s[0];exc=np.ones(2)/np.sqrt(2);active=(s@exc)/exc;accepted=float(1-np.sum(abs(s@exc)**2))
    sv=float(np.linalg.svd(s,compute_uv=False).max());recip=float(abs(s-s.T).max())
    vswr=lambda z:((1+abs(z))/(1-abs(z))).tolist()
    result=dict(variante=folder.name,passes=passes,delta_s=delta,convergiu=converged,
        nucleos_por_passe=cores,recursos_matriz=matrix_records,
        hfss_indicou_convergencia=native_yes,passes_consecutivos=consecutive,consecutivos_exigidos=required,
        major=mesh['reparos_major'],minor=mesh['reparos_minor'],passivo=sv<=1.0001,
        max_singular=sv,residuo_reciprocidade=recip,VSWR_ativo=vswr(active),VSWR_casado=vswr(np.diag(s)),
        potencia_aceita_W=accepted,cortes={},erros_recomposicao={})
    curves={}
    for axis in 'HV':
        th,e=read_pattern(folder/('AB_'+axis+'.csv'));gain=10*np.log10(np.sum(abs(e)**2,axis=1))
        _,ea=read_pattern(folder/('A_'+axis+'.csv'));_,eb=read_pattern(folder/('B_'+axis+'.csv'))
        err=float(np.max(abs(e-(ea+eb)/np.sqrt(2)))/np.max(abs(e)))
        assert err<1e-7,err
        result['erros_recomposicao'][axis]=err
        ix=np.flatnonzero(abs(th)<=90);peak=ix[np.argmax(gain[ix])];center=np.argmin(abs(th));width,left,right=beam(th,gain)
        peaks={}
        for pol,f in [('A',ea),('B',eb)]:
            gp=10*np.log10(np.sum(abs(f)**2,axis=1));ip=ix[np.argmax(gp[ix])];peaks[pol]=float(th[ip])
        result['cortes'][axis]=dict(ganho_frontal_dBi=float(gain[center]),ganho_pico_dBi=float(gain[peak]),
            pico_graus=float(th[peak]),abertura_graus=float(width),limites_graus=[float(left),float(right)],
            picos_individuais_graus=peaks)
        curves[axis]=(th,gain)
    result['desvio_maximo_graus']=max(abs(result['cortes'][a]['pico_graus']) for a in 'HV')
    result['centrado_na_grade_025grau']=all(result['cortes'][a]['pico_graus']==0 for a in 'HV')
    result['validado']=bool(result['centrado_na_grade_025grau'] and converged and not mesh['reparos_major'] and result['passivo'])
    (folder/'comparacao_AB.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (folder/'malha.json').write_text(json.dumps(mesh,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result,curves

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--parcial',action='store_true');args=parser.parse_args()
    names=json.loads((ROOT/'estudo.json').read_text(encoding='utf-8'))['variantes']
    folders=[BASE]+[ROOT/n for n in names]
    assessed=[];curves=[]
    for folder in folders:
        if not (folder/'B_V.csv').exists():
            if args.parcial:continue
            raise AssertionError('Variante ainda nao exportada: '+str(folder))
        r,c=assess(folder);assessed.append(r);curves.append(c)
    out=[]
    for r in assessed:
        out.append(dict(variante=r['variante'],ganho_dBi=r['cortes']['H']['ganho_frontal_dBi'],
            picoH_graus=r['cortes']['H']['pico_graus'],picoV_graus=r['cortes']['V']['pico_graus'],
            aberturaH_graus=r['cortes']['H']['abertura_graus'],aberturaV_graus=r['cortes']['V']['abertura_graus'],
            VSWR_A=r['VSWR_ativo'][0],VSWR_B=r['VSWR_ativo'][1],delta_s=r['delta_s'],convergiu=r['convergiu']))
    (ROOT/'comparacao.json').write_text(json.dumps(assessed,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/'comparacao.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    fig,axs=plt.subplots(1,2,figsize=(12,7),sharey=True)
    labels={'R08_Dois_Verticais_Sem_Suportes':'Original R08','v00_terra6':'Retorno 6 mm',
            'v01_central':'Entradas simétricas','v02_central_terra6':'Simétricas + retorno 6 mm',
            'v03_B_longo':'B +14,49 mm','v04_superior_16':'Superior +1,6 mm',
            'v05_B_longo_inferior_15':'B +14,49 / inferior +1,5',
            'v06_B12_superior2':'B +12 / superior +2',
            'v07_B10_superior3':'B +10 / superior +3',
            'v08_B145_inferior05_terra33':'B +14,49 / terra 3,3 mm',
            'v09_B968_superior366':'B +9,68 / superior +3,66'}
    colors=plt.get_cmap('tab20').colors
    for i,(r,c) in enumerate(zip(assessed,curves)):
        for ax,axis in zip(axs,'HV'):
            th,g=c[axis];ax.plot(th,g,label=labels.get(r['variante'],r['variante']),lw=1.6,color=colors[i])
    for ax,axis in zip(axs,'HV'):
        ax.set(xlim=(-90,90),ylim=(-15,13),xlabel='Ângulo (graus)',title='Corte '+axis)
        ax.axvline(0,color='#555555',lw=.8);ax.grid(alpha=.3)
    axs[0].set_ylabel('Ganho realizado total (dBi)')
    fig.legend(*axs[1].get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.5,.055),ncol=3,fontsize=8)
    fig.suptitle('Divisores e retornos — 5,17 GHz | duas entradas iguais e em fase',fontsize=13)
    fig.text(.5,.015,'Limite de 6 passes por variante; interpretar cada curva junto ao ΔS e à convergência.',ha='center',fontsize=10)
    fig.tight_layout(rect=[0,.24,1,.94]);fig.savefig(ROOT/'comparacao_diagramas.png',dpi=180);plt.close(fig)
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
