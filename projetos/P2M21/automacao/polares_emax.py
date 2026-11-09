"""Dois diagramas polares de amplitude E/Emax, sem alterar dados HFSS."""
import os,json,csv,argparse,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def generate(root,preview=False):
    audit=json.loads((root/'antena/auditoria_centro.json').read_text(encoding='utf-8-sig'))
    if not preview:assert audit['convergencia']['passes']==6,'A entrega exige os dois passes adicionais.'
    row=audit['pontos'][0];conv=audit['convergencia'];dest=root/('polares_preview' if preview else 'polares');dest.mkdir(exist_ok=True)
    label='PRELIMINAR / NÃO QUALIFICADO' if not audit['aprovado'] else 'CONVERGIDO / VERIFICAÇÕES ATENDIDAS'
    metadata=dict(frequencia_GHz=5.17,passes=conv['passes'],delta_s=conv['delta_s'],aprovado=audit['aprovado'],
      normalizacao='sqrt(|Etheta|^2+|Ephi|^2), dividido pelo maximo de cada corte completo; amplitude linear, nao potencia.',
      potencia_incidente_total_W=1,portas=64,fase_graus=0,amplitude_igual=True,curvas={})
    for axis,name,phi,zoom in [('H','Horizontal',90,30),('V','Vertical',0,6)]:
        source=root/'antena/centro/5170'/('Uniforme_'+axis+'.csv')
        with source.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
        cols=list(rows[0]);components=[k for k in cols if k.startswith(('re(','im('))];assert len(components)==4
        theta=np.array([float(r['Theta [deg]']) for r in rows])
        parts=np.array([[float(r[k]) for k in components] for r in rows])
        magnitude=np.sqrt(np.sum(parts**2,axis=1));normalized=magnitude/magnitude.max()
        gain=np.array([float(r['dB(RealizedGainTotal) []']) for r in rows])
        np.testing.assert_allclose(normalized,10**((gain-gain.max())/20),rtol=1e-8,atol=1e-12)
        assert abs(normalized.max()-1)<1e-12 and abs(normalized[0]-normalized[-1])<1e-8
        angle=np.deg2rad(theta);level=10**(-3/20)
        fig=plt.figure(figsize=(11.5,6.4));grid=fig.add_gridspec(1,2,width_ratios=[1.2,1],left=.04,right=.96,top=.80,bottom=.16,wspace=.20)
        full=fig.add_subplot(grid[0],projection='polar');front=fig.add_subplot(grid[1],projection='polar')
        for ax in [full,front]:
            ax.set_theta_zero_location('N');ax.set_theta_direction(-1)
            ax.plot(angle,normalized,color='#154f77',lw=1.8,label='E/Emax')
            ax.plot(angle,np.full_like(angle,level),color='#ad4b2d',ls=':',lw=1.2,label='−3 dB (0,708)')
            ax.set_ylim(0,1.05);ax.set_yticks([.2,.4,.6,.8,1]);ax.set_yticklabels(['0,2','0,4','0,6','0,8','1,0'],fontsize=9)
            ax.grid(alpha=.45)
        full.set_xticks(np.deg2rad(np.arange(0,360,30)));full.set_xticklabels(['0°','30°','60°','90°','120°','150°','180°','−150°','−120°','−90°','−60°','−30°'])
        full.set_rlabel_position(130);full.set_title('Corte completo • frente em 0°',pad=20,fontsize=11)
        front.set_thetalim(np.deg2rad(-zoom),np.deg2rad(zoom));ticks=np.linspace(-zoom,zoom,5 if axis=='V' else 7)
        front.set_xticks(np.deg2rad(ticks));front.set_xticklabels([f'{t:g}°' for t in ticks],fontsize=9)
        front.set_title('Ampliação frontal • mesma escala E/Emax',pad=22,fontsize=10)
        if axis=='V':
            front.set_ylim(.55,1.05);front.set_rorigin(0)
            front.set_yticks([.6,.8,1]);front.set_yticklabels(['0,6','0,8','1,0'],fontsize=9)
            front.set_title('Detalhe frontal • E/Emax de 0,55 a 1',pad=22,fontsize=10)
        for edge in [row['limite_'+axis+'_esquerdo_graus'],row['limite_'+axis+'_direito_graus']]:
            front.scatter([np.deg2rad(edge)],[level],s=20,color='#ad4b2d',zorder=5)
        width=row['abertura_'+axis+'_graus']
        fig.suptitle(f'P2M21 16 × 2 — {name} — E/Emax\n5,17 GHz | abertura −3 dB: {width:.2f}° | ganho frontal total: {row["ganho_frontal_total_realizado_dBi"]:.2f} dBi',fontsize=13,y=.98)
        fig.text(.5,.075,f'{conv["passes"]} passes | ΔS = {conv["delta_s"]:.6f} | {label}',ha='center',fontsize=10,color='#8b2f22' if not audit['aprovado'] else '#225c35')
        fig.text(.5,.035,f'64 portas iguais e em fase, 1 W total • φ={phi}° • escala de amplitude linear • normalização por corte',ha='center',fontsize=9)
        full.legend(loc='lower left',bbox_to_anchor=(-.07,-.20),ncol=2,frameon=False,fontsize=9)
        base=dest/('P2M21_'+name+'_polar_E_Emax')
        fig.savefig(str(base)+'.png',dpi=170,facecolor='white');fig.savefig(str(base)+'.svg');plt.close(fig)
        with (dest/('P2M21_'+name+'_E_Emax.csv')).open('w',encoding='utf-8',newline='') as f:
            w=csv.writer(f);w.writerow(['theta_graus','E_sobre_Emax']);w.writerows(zip(theta,normalized))
        metadata['curvas'][axis]=dict(abertura_graus=width,phi_graus=phi,amostras=len(theta),
          max_erro_equivalencia_amplitude=float(np.max(abs(normalized-10**((gain-gain.max())/20)))),
          csv_fonte_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),png=str(base)+'.png')
    (dest/'normalizacao.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(pasta=str(dest),passes=conv['passes'],preview=preview)))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(os.environ.get('P2M21_UNIFORME','D:/dev/EMBRAER/P2M21/R04_Centro_Classic')));parser.add_argument('--preview',action='store_true')
    args=parser.parse_args();generate(args.root,args.preview)
