"""Gerar ensaios controlados de retorno e posicionamento das entradas; nao resolve HFSS."""
import hashlib
import json
import shutil
from pathlib import Path

REPO=Path(__file__).resolve().parents[3]
SCRIPTS=Path(__file__).parent
ROOT=Path('D:/dev/EMBRAER/P2M21/R09_Divisor_Simetria')
VARIANTS=[('v00_terra6',False,3.),('v01_central',True,1.8),('v02_central_terra6',True,3.)]

def replace(text,old,new):
    assert old in text,old
    return text.replace(old,new)

assert not ROOT.exists() or not any(ROOT.rglob('*.aedt')) and not any(ROOT.rglob('*.FCStd')), 'Nao sobrescrever CAD/HFSS existente.'
ROOT.mkdir(exist_ok=True)
layout=(SCRIPTS/'dois_verticais_layout.py').read_text(encoding='utf-8')
for name,central,half_ground in VARIANTS:
    text=replace(layout,"root=Path('D:/dev/EMBRAER/P2M21/R07_Dois_Verticais_GUI');root.mkdir(exist_ok=True)",f"root=Path({str(ROOT)!r})")
    text=replace(text,'for pitch in [48.,52.6,56.]:','for pitch in [48.]:')
    text=replace(text,"dest=root/('d'+str(pitch).replace('.','p'));dest.mkdir(exist_ok=True)",f"dest=root/{name!r};dest.mkdir(exist_ok=True)")
    text=replace(text,'buffer(1.8,cap_style=',f'buffer({half_ground!r},cap_style=')
    text=replace(text,"ground=ground.difference(obstacles.buffer(.2,join_style='mitre'))",
        "ground=ground.difference(obstacles.buffer(.2,join_style='mitre'))\n"+
        "        ground=ground.intersection(Polygon([[-pitch/2-14.8,-21],[pitch/2+20,-21],[pitch/2+20,28],[-pitch/2-14.8,28]]).buffer(-.2))")
    if central:
        text=replace(text,"tx,ty=(17.,-18.) if pol=='A' else (p,18.)","tx,ty=(p,-18.) if pol=='A' else (p,18.)")
        start=text.index("            if pol=='A':pts50=")
        end=text.index('            pts=pts70+pts50[1:]',start)
        text=text[:start]+"            pts50=[pts70[-1],(cx+p,ty),(cx+p,-p if pol=='A' else p)]\n"+text[end:]
    code=ROOT/(name+'_layout.py');code.write_text(text,encoding='utf-8')
    exec(compile(text,str(code),'exec'),{'__file__':str(SCRIPTS/'dois_verticais_layout.py')})
    cfg=dict(native='Divisor_'+name+'.aedt',variante=name,conexoes_centrais=central,
        largura_retorno_mm=2*half_ground,espacamento_vertical_mm=48,radiadores=2,
        borda_retorno='Retorno novo limitado a0.2mm da borda daPCB; largura nominal pode ser recortada junto ao meandroB.',
        cabos_fisicos_com_perdas=True,comprimento_cabo_mm=50,apoios_plasticos=False,
        frequencia_GHz=5.17,max_passes=6,max_delta_s=.04,nucleos=14,gui=True,sweep=False,
        potencia_por_porta_W=.5,fase_graus=0,
        descricao=('Entradas x=2.509mm, y=+/-18mm; quatro ramos espelhados sem meandros.' if central else 'Roteamento R08 preservado; apenas largura nominal do retorno3.6->6mm.'),
        referencia='D:/dev/EMBRAER/P2M21/R08_Dois_Verticais_Sem_Suportes')
    (ROOT/name/'configuracao.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

cad=(SCRIPTS/'dois_verticais_cad.py').read_text(encoding='utf-8')
cad=replace(cad,"root=Path('D:/dev/EMBRAER/P2M21/R07_Dois_Verticais_GUI')",f"root=Path({str(ROOT)!r})")
cad=replace(cad,"for folder in [root/'d48p0',root/'d52p6',root/'d56p0']:",f"for folder in [root/name for name in {[x[0] for x in VARIANTS]!r}]:")
start=cad.index('    # Suportes de poliacetal')
end=cad.index('    d.recompute();',start)
cad=cad[:start]+cad[end:]
(ROOT/'criar_cad.py').write_text(cad,encoding='utf-8')

base=Path('D:/dev/EMBRAER/P2M21/R07_Dois_Verticais_GUI/criar_resolver_gui.py').read_text(encoding='utf-8')
base=base.split('# Resolver serialmente, na mesma GUI.')[0]
base=replace(base,"import ScriptEnv\nScriptEnv.Initialize('Ansoft.ElectronicsDesktop')",'')
base=replace(base,"root='D:/dev/EMBRAER/P2M21/R07_Dois_Verticais_GUI'",f'root={str(ROOT)!r}')
base=replace(base,"for folder,filename in [('d52p6','Dois_Verticais_d52p6'),('d48p0','Dois_Verticais_d48p0'),('d56p0','Dois_Verticais_d56p0')]:",
             'for folder,filename in '+repr([(v[0],'Divisor_'+v[0]) for v in VARIANTS])+':')
base=replace(base,"'MaximumPasses:=',4","'MaximumPasses:=',6")
base=replace(base,'max_passes=4','max_passes=6')
(ROOT/'criar_hfss.py').write_text(base.rstrip()+'\n',encoding='utf-8')
shutil.copy2('D:/dev/EMBRAER/P2M21/R08_Dois_Verticais_Sem_Suportes/HFSS_14nucleos.acf',ROOT/'HFSS_14nucleos.acf')
(ROOT/'estudo.json').write_text(json.dumps(dict(variantes=[x[0] for x in VARIANTS],
    objetivo='Reduzir deslocamento dos maximos H/V em relacao a0graus com A=B=.5W/0graus.',
    limite='Seis passes por geometria; relatar DeltaS real, nao validar resultado nao convergido.',
    referencia='R08: H+15.25graus,V-6.25graus,8.1283dBi,DeltaS.0893184.',
    fontes_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [SCRIPTS/'dois_verticais_layout.py',SCRIPTS/'dois_verticais_cad.py']}
    ),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('VARIANTES_PREPARADAS',ROOT)
