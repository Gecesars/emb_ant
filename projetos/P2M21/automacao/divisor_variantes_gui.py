"""Criar/resolver variacoes em serie na instancia HFSS GUI explicitamente identificada."""
import argparse,json,sys,traceback,re
from pathlib import Path
import dois_verticais_sem_suportes as run

ROOT=Path('D:/dev/EMBRAER/P2M21/R09_Divisor_Simetria')

def write(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('etapa',choices=['preparar','resolver']);parser.add_argument('--pid',required=True,type=int)
    parser.add_argument('--variantes',nargs='+')
    args=parser.parse_args();desktop=run.attach(args.pid)
    variants=json.loads((ROOT/'estudo.json').read_text(encoding='utf-8'))['variantes']
    if args.variantes:
        assert set(args.variantes)<=set(variants)
        variants=args.variantes
    if args.etapa=='preparar':
        assert not any(list((ROOT/n).glob('*.aedt')) for n in variants),'Projetos ja criados; nao duplicar.'
        code=(ROOT/'criar_hfss.py').read_text(encoding='utf-8')
        code=re.sub(r'^for folder,filename in .*:$','for folder,filename in '+repr([(v,'Divisor_'+v) for v in variants])+':',code,flags=re.M)
        exec(compile(code,str(ROOT/'criar_hfss.py'),'exec'),{'oDesktop':desktop})
        for name in variants:
            folder=ROOT/name;cfg=json.loads((folder/'configuracao.json').read_text(encoding='utf-8'))
            text=(folder/cfg['native']).read_text(errors='replace')
            assert 'MaximumPasses=6' in text and 'MaxDeltaS=0.04' in text
            assert "Name='Apoio_POM" not in text
            write(folder/'qualificacao.json',dict(estado='PREPARADO_GUI_ABERTA',pid=args.pid))
        write(ROOT/'qualificacao.json',dict(estado='TRES_VARIANTES_PREPARADAS',pid=args.pid))
    else:
        sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'automacao/r06'))
        from auditar_malha import audit
        for name in variants:
            folder=ROOT/name;cfg=json.loads((folder/'configuracao.json').read_text(encoding='utf-8'))
            run.ROOT=folder;run.NATIVE=folder/cfg['native'];run.PROJECT=Path(cfg['native']).stem
            run.ACF=ROOT/'HFSS_14nucleos.acf'
            import shutil
            shutil.copy2(ROOT/'HFSS_14nucleos.acf',folder/'HFSS_14nucleos.acf')
            write(ROOT/'qualificacao.json',dict(estado='EM_CALCULO',variante=name,pid=args.pid))
            run.solve(desktop,args.pid)
            mesh=audit(folder);write(folder/'malha.json',mesh)
            assert mesh['reparos_major']==0,mesh
        write(ROOT/'qualificacao.json',dict(estado='VARIANTES_EXPORTADAS_AGUARDA_COMPARACAO',pid=args.pid))
        print('VARIANTES_CONCLUIDAS_GUI_ABERTA',flush=True)

if __name__=='__main__':
    try:main()
    except Exception:
        write(ROOT/'falha_pipeline.json',dict(erro=traceback.format_exc()))
        raise
