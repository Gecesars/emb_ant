"""Relatorio e pacote compacto das variantes; nenhum novo solve."""
import csv,hashlib,json,shutil
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

import divisor_variantes_comparar as comparison

ROOT=comparison.ROOT
DEST=comparison.REPO/'projetos/P2M21/dois_verticais_divisor'

def main():
    names=json.loads((ROOT/'estudo.json').read_text(encoding='utf-8'))['variantes']
    records=[comparison.assess(comparison.BASE)[0]]
    curves={}
    for name in names:
        r,c=comparison.assess(ROOT/name);records.append(r);curves[name]=c
    candidates=[r for r in records[1:] if r['convergiu'] and r['passivo'] and r['major']==0 and max(r['VSWR_ativo'])<1.5]
    assert candidates,'Nenhuma variante convergida e casada; revisar antes de selecionar.'
    selected=min(candidates,key=lambda r:(r['desvio_maximo_graus'],sum(abs(r['cortes'][a]['pico_graus']) for a in 'HV'),-r['cortes']['H']['ganho_frontal_dBi']))
    pointing=min(records[1:],key=lambda r:(r['desvio_maximo_graus'],sum(abs(r['cortes'][a]['pico_graus']) for a in 'HV')))
    name=selected['variante'];folder=ROOT/name;cfg=json.loads((folder/'configuracao.json').read_text(encoding='utf-8'))
    (ROOT/'selecionada.json').write_text(json.dumps(dict(variante=name,criterio='Entre variantes convergidas, passivas, sem Major e VSWR ativo<1.5: menor maximo dos desvios H/V.',
        centrado_na_grade=selected['centrado_na_grade_025grau'],resultado=selected,
        melhor_apontamento_sem_exigir_convergencia=pointing),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    fig,axs=plt.subplots(1,2,figsize=(12,7.5),subplot_kw={'projection':'polar'})
    base_curves=comparison.assess(comparison.BASE)[1]
    for ax,axis in zip(axs,'HV'):
        th,g=curves[name][axis];tb,gb=base_curves[axis]
        ax.plot(np.deg2rad(tb),10**((gb-max(gb))/20),'--',lw=1.2,color='#929292',label='Original R08')
        ax.plot(np.deg2rad(th),10**((g-max(g))/20),lw=2,color='#196f98',label='Variante selecionada: v05')
        if pointing['variante']!=name:
            tp,gp=curves[pointing['variante']][axis]
            ax.plot(np.deg2rad(tp),10**((gp-max(gp))/20),lw=1.4,ls=':',color='#3b965c',label='Ajuste fino: não validado')
        ax.set_theta_zero_location('N');ax.set_theta_direction(-1);ax.set_ylim(0,1.05);ax.set_rticks([.25,.5,.75,1])
        ax.set_rlabel_position(75);ax.tick_params(axis='y',labelsize=9)
        ax.set_thetagrids(np.arange(0,360,30),['0°','30°','60°','90°','120°','150°','180°','−150°','−120°','−90°','−60°','−30°'])
        c=selected['cortes'][axis]
        ax.set_title(f"{axis}: máximo {c['pico_graus']:+.2f}° | abertura {c['abertura_graus']:.2f}°",pad=24)
        ax.grid(alpha=.3)
    fig.legend(*axs[1].get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.5,.105),ncol=3,fontsize=9)
    fig.suptitle('Comparação polar E/Emax — 5,17 GHz\nA = B = 0,5 W / 0° nas entradas dos dois cabos',fontsize=14,y=.98)
    fig.text(.5,.045,f"Ganho frontal: {selected['cortes']['H']['ganho_frontal_dBi']:.2f} dBi | ΔS = {selected['delta_s']:.5f} | {selected['passes']} passes",ha='center',fontsize=11)
    fig.text(.5,.01,'Cada corte normalizado ao próprio máximo; linhas não representam ganho absoluto.',ha='center',fontsize=9)
    fig.subplots_adjust(top=.76,bottom=.24,wspace=.27);fig.savefig(ROOT/'polar_selecionada.png',dpi=180);fig.savefig(ROOT/'polar_selecionada.pdf');plt.close(fig)

    h=selected['cortes']['H'];v=selected['cortes']['V']
    lines=['# Dois elementos: ensaios de divisores e retorno de terra','',
        f'Estudo HFSS de 9/11/2026. Foram comparadas {len(names)} alterações com a referência R08, usando a mesma instância GUI. ',
        'Dois elementos verticais separados por 48 mm, dois divisores impressos 1:2, dois cabos físicos de 50 mm, PCB RO4350B de 0,76 mm e refletor de alumínio de 2 mm. Sem apoios plásticos. ',
        'As duas entradas externas permaneceram em 0,5 W / 0°, total de 1 W. Frequência única de 5,17 GHz, sem sweep. Classic automático, sem operações locais de refinamento, máximo de 6 passes por geometria, alvo ΔS = 0,04 e dois passes consecutivos. 14 núcleos no perfil do solver.','',
        f"Variante selecionada: **{name}**. Ganho frontal **{h['ganho_frontal_dBi']:.3f} dBi**; máximos H **{h['pico_graus']:+.2f}°** e V **{v['pico_graus']:+.2f}°**. Aberturas H **{h['abertura_graus']:.2f}°**, V **{v['abertura_graus']:.2f}°**. VSWR ativo A/B **{selected['VSWR_ativo'][0]:.3f}/{selected['VSWR_ativo'][1]:.3f}**. ΔS **{selected['delta_s']:.6f}**, {selected['passes_consecutivos']} passes consecutivos aprovados.",'',
        f"Com a outra entrada casada, o VSWR da selecionada é A/B **{selected['VSWR_casado'][0]:.3f}/{selected['VSWR_casado'][1]:.3f}**; B ainda excede 1,5. O bom casamento ativo com ambas em fase não comprova o mesmo casamento em operação MIMO independente.",'',
        f"O ajuste de melhor apontamento foi **{pointing['variante']}**: H **{pointing['cortes']['H']['pico_graus']:+.2f}°**, V **{pointing['cortes']['V']['pico_graus']:+.2f}°**, ganho **{pointing['cortes']['H']['ganho_frontal_dBi']:.3f} dBi**, VSWR ativo **{pointing['VSWR_ativo'][0]:.3f}/{pointing['VSWR_ativo'][1]:.3f}**. ΔS final **{pointing['delta_s']:.6f}**, mas somente **{pointing['passes_consecutivos']} de {pointing['consecutivos_exigidos']} passes consecutivos**; fica preservado como candidato de ajuste, não como solução validada.",'',
        ('Os dois máximos coincidem com 0° na grade angular de 0,25°. Isso não é validação experimental nem comprovação da banda.' if selected['centrado_na_grade_025grau'] else '**A meta de máximo exatamente em 0° nos dois cortes ainda não foi atingida.** A variante escolhida é a melhor combinação testada de apontamento, convergência e casamento; não é uma declaração de otimização global.'),'',
        '| Variante | G frontal dBi | Pico H ° | Pico V ° | H ° | V ° | VSWR A/B ativo | ΔS | Convergência |',
        '|---|---:|---:|---:|---:|---:|---|---:|---|']
    for r in records:
        ch,cv=r['cortes']['H'],r['cortes']['V']
        lines.append(f"| {r['variante']} | {ch['ganho_frontal_dBi']:.3f} | {ch['pico_graus']:+.2f} | {cv['pico_graus']:+.2f} | {ch['abertura_graus']:.2f} | {cv['abertura_graus']:.2f} | {r['VSWR_ativo'][0]:.3f}/{r['VSWR_ativo'][1]:.3f} | {r['delta_s']:.6f} | {'Sim' if r['convergiu'] else 'Não'} |")
    lines += ['', 'As versões v01, v06 e v09 chegaram a ΔS < 0,04 no último passe, mas somente em um passe consecutivo. O indicador genérico do HFSS mostrou “Yes”; a auditoria mantém reprovação porque o setup exige dois consecutivos. Nenhuma execução excedeu seis passes.','',
        'As entradas originalmente estavam em X = 17 mm para A e X = 2,509 mm para B, com caminhos diferentes. Nos novos desenhos centrais, ambas ficam em X = 2,509 mm, Y = ±18 mm. O alargamento isolado do retorno nominal de 3,6 para 6 mm não melhorou os diagramas; reposicionar as conexões e equilibrar os caminhos trouxe a maior melhora inicial. Os ensaios de fase acrescentaram meandros nas trilhas mantendo as fases externas iguais.','',
        'Os resultados apoiam a hipótese de participação da alimentação/retorno na assimetria. Não provam que o terra é a causa única: mudar seu contorno também modifica impedância, acoplamento e fase elétrica, e algumas variantes não convergiram. Igual comprimento geométrico não garante igualdade elétrica.','',
        f"Na selecionada, o ganho em 0° está {h['ganho_pico_dBi']-h['ganho_frontal_dBi']:.5f} dB abaixo do pico horizontal e {v['ganho_pico_dBi']-v['ganho_frontal_dBi']:.5f} dB abaixo do pico vertical. Esses déficits pequenos não autorizam arredondar os ângulos para zero.",'',
        'Todos os CADs passaram nas verificações de sólidos/interseções e de curtos planares. A soma complexa dos campos individuais reproduziu o caso A+B; matrizes passivas e reparos de malha foram auditados. Os resultados são do módulo de dois elementos, não do painel 16×2 ou de ganho MIMO por entrada. Não houve nova cotação nem envio de email.','',
        '![Comparação dos cortes](comparacao_diagramas.png)','', '![Polar selecionada](polar_selecionada.png)','',
        f'![Layout selecionado](variantes/{name}/layout.png)','',
        'Os nativos HFSS, FreeCAD, geometria JSON, matrizes S e cortes exportados estão nas pastas de variantes. Foram excluídos resultados volumétricos, malhas, locks e temporários. O arquivo AEDT sem a pasta aedtresults preserva o modelo, mas não a solução FEM restaurável. O diretório local de trabalho mantém a solução completa.', '',
        'Trabalho local: `D:/dev/EMBRAER/P2M21/R09_Divisor_Simetria`. Os scripts geradores e de análise estão em `../automacao/divisor_variantes_*.py`; os scripts de criação CAD/HFSS derivados estão em `reproducao/`. A geometria e os parâmetros em JSON registram cada ensaio.']
    (ROOT/'README.md').write_text('\n'.join(line.rstrip() for line in lines)+'\n',encoding='utf-8')
    DEST.mkdir(parents=True,exist_ok=True)
    manifest=[]
    def copy(src,dst):
        dst.parent.mkdir(parents=True,exist_ok=True)
        data=src.read_bytes()
        if src.suffix in ('.py','.md'):data=data.replace(b'\r\n',b'\n')
        dst.write_bytes(data)
        assert dst.read_bytes()==data
        manifest.append(dict(arquivo=str(dst.relative_to(DEST)).replace('\\','/'),bytes=dst.stat().st_size,
            sha256=sha(dst),origem_sha256=sha(src),normalizacao_EOL=src.suffix in ('.py','.md')))
    for filename in ['README.md','estudo.json','qualificacao.json','selecionada.json','comparacao.json','comparacao.csv','comparacao_diagramas.png','polar_selecionada.png','polar_selecionada.pdf']:
        copy(ROOT/filename,DEST/filename)
    for source in ROOT.glob('*.py'):copy(source,DEST/'reproducao'/source.name)
    for source_folder,dest_name in [(comparison.BASE,'referencia_R08')]+[(ROOT/n,n) for n in names]:
        dest=DEST/'variantes'/dest_name
        files=['configuracao.json','convergencia.txt','mensagens.json','centro.s2p','comparacao_AB.json','malha.json']+[p+'_'+a+'.csv' for p in ['AB','A','B'] for a in 'HV']
        cfg2=json.loads((source_folder/'configuracao.json').read_text(encoding='utf-8'));files.append(cfg2['native'])
        for f in files:copy(source_folder/f,dest/f)
        if source_folder!=comparison.BASE:
            for f in ['geometria.json','layout.png','Dois_Verticais.FCStd','hfss_validacao.json','cad/intersecoes.json','cad/portas.json','cad/manifesto.json','cad/folhas_solidas.json']:
                copy(source_folder/f,dest/f)
    (DEST/'manifesto.json').write_text(json.dumps(dict(arquivos=manifest,total_bytes=sum(x['bytes'] for x in manifest)),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(selecionada=name,resultado=selected,arquivos=len(manifest),bytes=sum(x['bytes'] for x in manifest)),ensure_ascii=False,indent=2))

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

if __name__=='__main__':main()
