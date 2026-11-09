"""Preparacao e auditoria dos ensaios uniformes P2M21; nenhum solve neste script."""
import argparse,csv,hashlib,json,re,shutil,sys,os
from datetime import datetime
from pathlib import Path
import numpy as np
import skrf

repo=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(repo/'automacao/r05'))
sys.path.insert(0,str(repo/'automacao/r06'))
from auditar_malha import audit as mesh_audit
from rede_carregada import beam,read_pattern
root=Path(os.environ.get('P2M21_UNIFORME','D:/dev/EMBRAER/P2M21/R02_Malha_Uniforme17'))
folder=root/'antena'
source=Path('D:/dev/EMBRAER/P2M21/R00_Concepcao/antena/P2M21_Antena.aedt')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def geometry(text):
    return [b.split("$end 'GeometryPart'",1)[0] for b in text.split("$begin 'GeometryPart'")[1:]]
def conv_info(path):
    text=path.read_text()
    def value(expr,cast=float):return cast(re.search(expr,text).group(1))
    return dict(passes=value(r'Completed\s*:\s*(\d+)',int),max_passes=value(r'Maximum\s*:\s*(\d+)',int),
      minimo=value(r'Minimum\s*:\s*(\d+)',int),alvo=value(r'Target\s*:\s*([\d.eE+-]+)'),
      delta_s=value(r'Current\s*:\s*([\d.eE+-]+)'),
      consecutivos=value(r'Current Consecutive Passes\s*:\s*(\d+)',int),
      convergiu='Converged : Yes' in text,sha256=sha(path))
def progress():
    cfg=read(root/'configuracao.json');native=(folder/cfg['native']).read_text(errors='replace')
    results=(folder/cfg['native']).with_suffix('.aedtresults')
    candidates=[]
    for p in results.rglob('*.EMConvData'):
        text=p.read_text()
        target=re.search(r"ConvTarget='([^']+)'",text)
        if target and abs(float(target[1])-.04)<1e-12 and "MaxPasses='6'" in text:candidates.append((p,text))
    if not candidates:return dict(estado='sem_historico_adaptativo_ainda')
    assert len(candidates)==1,[str(p) for p,t in candidates]
    p,text=candidates[0];history={};traces={};fields={}
    for block in text.split("$begin 'QuantityValues'")[1:]:
        block=block.split("$end 'QuantityValues'",1)[0]
        number=int(re.search(r'PassNo=(\d+)',block)[1]);tet=int(float(re.search(r'SolvedElements\(([^,]+)',block)[1]))
        ds=re.search(r'MaxMagDeltaS\(([^,]+)',block)
        history[number]=dict(passe=number,tetraedros=tet,delta_s=float(ds[1]) if ds else None)
    for block in native.split("$begin 'CacheItem'")[1:]:
        block=block.split("$end 'CacheItem'",1)[0]
        title=re.search("Title='([^']+)'",block);trace=re.search(r'TraceID=(\d+)',block)
        if title and trace:traces[int(trace[1])]=title[1]
    caches=sorted(results.rglob('*.ExprCache'),key=lambda p:p.stat().st_mtime)
    if caches:
        for line in caches[-1].read_text().splitlines():
            match=re.match(r"(\d+)\s+Pass='(\d+)'\s+([^\s]+)",line)
            if match and int(match[1]) in traces:
                fields.setdefault(int(match[2]),{})[traces[int(match[1])]]=float(match[3])
    for number,row in history.items():
        row['campos_dBi']=fields.get(number,{})
        before=fields.get(number-1,{})
        row['delta_campo_max_dB']=(max(abs(row['campos_dBi'][k]-before[k]) for k in traces.values())
          if len(before)==len(row['campos_dBi'])==len(traces)==9 else None)
    return dict(fonte=str(p),nativo_convergiu='IsConverged=true' in text,
      cache_somente_monitoramento=True,historico=[history[k] for k in sorted(history)])
def initialize():
    assert not root.exists(),'Pasta ja existe; examinar estado antes de reutilizar.'
    folder.mkdir(parents=True)
    config=dict(revisao='R02_Malha_Uniforme17',inicio=datetime.now().astimezone().isoformat(),
      native='P2M21_Uniforme.aedt',fonte=str(source),fonte_sha256=sha(source),
      niveis=16,colunas=2,radiadores=32,portas=64,potencia_total_W=1.,potencia_por_porta_W=1/64,
      fase_todas_portas_graus=0,frequencias_MHz=list(range(5090,5251,10)),
      max_passes=6,delta_s=.04,passes_consecutivos=2,adaptacao_MHz=5170,
      metodo='PCB radiante/refletor/apoios em HFSS, 64 portas diretas iguais e em fase; sem rede externa ou cabos.',
      criterio_usuario='Ultima instrucao: Delta S de 4% suficiente; substitui 2%. Limite de seis passes mantido.',
      campos_cache='Nove direcoes apenas monitoradas por passe; nao sao criterio adicional.',
      correcoes_malha='TrueSurf .0005mm/5graus em64Cu0+64Cu1+128soldas; Length.06mm acrescentado aos64Cu0. Cu1 ja tinha.06mm. Nova malha, sem reutilizar reparos R00.')
    shutil.copy2(source,folder/config['native']);write(root/'configuracao.json',config)
    write(root/'qualificacao.json',dict(estado='COPIA_PREPARADA_AGUARDANDO_CORRECAO',configuracao=config))
    print('COPIA_INICIAL_OK',root)
def check_preparation():
    cfg=read(root/'configuracao.json');p=folder/cfg['native']
    text=p.read_text(errors='replace');original=source.read_text(errors='replace')
    assert sha(source)==cfg['fonte_sha256']
    assert geometry(text)==geometry(original),'A correcao deve preservar os blocos de geometria.'
    assert re.search(r'\bMaxDeltaS=0\.04\s',text)
    assert re.search(r'\bMaximumPasses=6\s',text)
    assert re.search(r'\bMinimumConvergedPasses=2\s',text)
    # AEDT omite IsConvergence quando False; itens de criterio conteriam MaxConvergenceDelta.
    cache=text.split("$begin 'ExpressionCache'",1)[1].split("$end 'ExpressionCache'",1)[0]
    assert cache.count("$begin 'CacheItem'")==9 and 'MaxConvergenceDelta=' not in cache
    assert 'IsConvergence=true' not in cache
    assert text.count("Magnitude='0.015625W'")==64
    assert 'Cobre_solda_superficie_R02' in text and 'Cu0_60um_R02' in text
    prep=read(folder/'preparacao.json');assert prep['validacao']==1 and not prep['erros']
    assert len(prep['portas'])==64 and abs(prep['potencia_por_porta_W']*64-1)<1e-12
    evidence=dict(geometria_preservada=True,blocos_geometria=len(geometry(text)),fonte_sha256=sha(source),
      novo_native_sha256=sha(p),portas=64,potencia_total_W=1,max_passes=6,delta_s=.04,
      superficie_refinada_corpos=256,novos_Cu0_com_limite_60um=64)
    write(folder/'verificacao_preparacao.json',evidence);print(json.dumps(evidence))
def check(stage):
    cfg=read(root/'configuracao.json');assert sha(Path(cfg['fonte']))==cfg['fonte_sha256']
    if cfg.get('apenas_centro'):assert stage=='centro','Sweep nao autorizado nesta etapa.'
    conv=conv_info(folder/('convergencia_'+stage+'.txt'))
    mesh=mesh_audit(folder);write(folder/('malha_'+stage+'.json'),mesh)
    converged=(conv['convergiu'] and 2<=conv['passes']<=6 and conv['max_passes']==6 and
      conv['consecutivos']>=2 and conv['alvo']==.04 and conv['delta_s']<=.04)
    monitor=progress();write(folder/('historico_'+stage+'.json'),monitor)
    recent=monitor.get('historico',[])[-2:]
    converged=bool(converged and len(recent)==2 and all(r['delta_s'] is not None and r['delta_s']<=.04 for r in recent))
    if stage=='banda':
        previous=read(folder/'auditoria_centro.json')
        assert previous['aprovado'] and conv['passes']==previous['convergencia']['passes']
    nw=skrf.Network(str(folder/(stage+'.s64p')))
    freqs=np.array([5170] if stage=='centro' else list(range(5090,5251,10)))*1e6
    np.testing.assert_allclose(nw.f,freqs,rtol=0,atol=1)
    assert nw.nports==64 and np.allclose(nw.z0,50)
    singular=float(np.linalg.svd(nw.s,compute_uv=False).max())
    reciprocity=float(np.abs(nw.s-nw.s.transpose(0,2,1)).max())
    assert singular<=1.0001 and reciprocity<1e-6,(singular,reciprocity)
    records=[];a=np.ones(64,dtype=complex)/8;hashes={}
    for f,s in zip(nw.f,nw.s):
        mhz=int(round(f/1e6));row=dict(frequencia_GHz=float(f/1e9),potencia_incidente_W=1.)
        reflected=float(np.linalg.norm(s@a)**2);accepted=1-reflected
        assert 0<accepted<=1.00001
        row.update(potencia_refletida_W=reflected,potencia_aceita_W=accepted)
        centers=[]
        for axis in 'HV':
            path=folder/stage/str(mhz)/('Uniforme_'+axis+'.csv');hashes[str(path.relative_to(root))]=sha(path)
            with path.open(encoding='utf-8-sig',newline='') as handle:data=list(csv.DictReader(handle))
            angles=np.array([float(r['Theta [deg]']) for r in data])
            gains=np.array([float(r['dB(RealizedGainTotal) []']) for r in data])
            np.testing.assert_allclose(angles,np.arange(-180,180.001,.25),atol=1e-9)
            assert np.isfinite(gains).all()
            center=int(np.argmin(abs(angles)));centers.append(gains[center])
            gain=float(data[center]['dB(GainTotal) []']);directivity=float(data[center]['dB(DirTotal) []'])
            frac=10**((gains[center]-gain)/10)
            assert abs(frac-accepted)<1e-5,(frac,accepted)
            eta=10**((gain-directivity)/10);assert 0<eta<=1.0001
            theta,field=read_pattern(path) # Confere potencia dos campos complexos contra o ganho nativo.
            width,left,right=beam(angles,gains);front=np.abs(angles)<=90
            peak=np.flatnonzero(front)[np.argmax(gains[front])]
            row['abertura_'+axis+'_graus']=float(width)
            row['limite_'+axis+'_esquerdo_graus']=float(left);row['limite_'+axis+'_direito_graus']=float(right)
            row['pico_'+axis+'_graus']=float(angles[peak]);row['ganho_pico_'+axis+'_dBi']=float(gains[peak])
            if axis=='H':
                row.update(ganho_frontal_total_realizado_dBi=float(gains[center]),ganho_frontal_total_dBi=gain,
                  diretividade_frontal_total_dBi=directivity,eficiencia_radiacao=eta,
                  potencia_radiada_W=float(accepted*eta),perda_interna_W=float(accepted*(1-eta)))
        assert abs(centers[0]-centers[1])<1e-8
        records.append(row)
    result=dict(aprovado=bool(converged and mesh['reparos_major']==0),convergencia=conv,
      malha_major=mesh['reparos_major'],malha_minor=mesh['reparos_minor'],max_valor_singular=singular,
      erro_reciprocidade=reciprocity,passivo=True,reciproco=True,normalizacao_incidente_W=1,
      max_erro_balanco_W=max(abs(r['potencia_refletida_W']+r['potencia_radiada_W']+r['perda_interna_W']-1) for r in records),
      pontos=records,n_pontos=len(records),matriz_sha256=sha(folder/(stage+'.s64p')),campos_sha256=hashes,
      ganho_min_dBi=min(r['ganho_frontal_total_realizado_dBi'] for r in records),
      ganho_max_dBi=max(r['ganho_frontal_total_realizado_dBi'] for r in records),
      H_min_graus=min(r['abertura_H_graus'] for r in records),H_max_graus=max(r['abertura_H_graus'] for r in records),
      V_min_graus=min(r['abertura_V_graus'] for r in records),V_max_graus=max(r['abertura_V_graus'] for r in records),
      meta_21dBi_todos_pontos=all(r['ganho_frontal_total_realizado_dBi']>=21 for r in records),
      nota='Ganho total com todas as portas A/B coerentes; nao e ganho MIMO por entrada nem inclui a rede externa. Malha adaptada no centro; pontos discretos reais.')
    write(folder/('auditoria_'+stage+'.json'),result)
    with (root/('resultados_'+stage+'.csv')).open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    print(json.dumps({k:v for k,v in result.items() if k not in ('pontos','campos_sha256')},indent=2))
    assert result['aprovado'],'Convergencia ou malha nao aprovada; interromper antes da banda.'
    if stage=='banda':plot(records)
def plot(records):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    x=[r['frequencia_GHz'] for r in records]
    fig,axs=plt.subplots(1,3,figsize=(14,4.4))
    for ax,key,ylabel in zip(axs,['ganho_frontal_total_realizado_dBi','abertura_H_graus','abertura_V_graus'],['Ganho frontal total realizado (dBi)','Abertura horizontal (graus)','Abertura vertical (graus)']):
        ax.plot(x,[r[key] for r in records],'o-',markersize=3);ax.set(xlabel='Frequencia (GHz)',ylabel=ylabel);ax.grid(alpha=.3)
    axs[0].axhline(21,color='#b64d2b',linestyle='--',label='Meta 21 dBi');axs[0].legend()
    fig.suptitle('P2M21 16 x 2 — 64 portas iguais/em fase; 1 W total; PCBs radiantes sem rede externa')
    fig.tight_layout();fig.savefig(root/'ganho_aberturas_17pontos.png',dpi=180);plt.close(fig)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('etapa',choices=['iniciar','preparacao','centro','banda','monitor'])
    stage=parser.parse_args().etapa
    if stage=='iniciar':initialize()
    elif stage=='preparacao':check_preparation()
    elif stage=='monitor':print(json.dumps(progress(),indent=2))
    else:check(stage)
