"""FreeCAD headless: organiza a montagem RF R12 sem mudar suas geometrias."""
import FreeCAD as A
import Part
from pathlib import Path
import json, hashlib, csv

SOURCE=Path('D:/dev/EMBRAER/P2S13/R12_Curvilinear_Simplificado')
OUT=Path('D:/dev/EMBRAER/emb_ant/projetos/P2S13/mecanica_R12')
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'imagens').mkdir(exist_ok=True)
cfg=json.loads((SOURCE/'configuracao.json').read_text(encoding='utf-8-sig'))
manifest=json.loads((SOURCE/'cad/manifesto.json').read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source_path=SOURCE/cfg['cad_native']
d=A.openDocument(str(source_path))
assert len(d.Objects)==123 and set(manifest)==set(o.Name for o in d.Objects)
d.Label='R12 - montagem completa do modelo RF - PRELIMINAR'

def record(o):
    bb=o.Shape.optimalBoundingBox(False,False)
    return dict(nome=o.Name,material=manifest[o.Name],volume_mm3=o.Shape.Volume,
        area_mm2=o.Shape.Area,solidos=len(o.Shape.Solids),valido=o.Shape.isValid(),
        bbox_mm=[bb.XMin,bb.YMin,bb.ZMin,bb.XMax,bb.YMax,bb.ZMax])
original={o.Name:record(o) for o in d.Objects}
def same_geometry(a,b):
    return a['nome']==b['nome'] and a['solidos']==b['solidos'] and b['valido'] and a['material']==b['material'] and abs(a['volume_mm3']-b['volume_mm3'])<1e-8 and abs(a['area_mm2']-b['area_mm2'])<1e-8 and max(abs(x-y) for x,y in zip(a['bbox_mm'],b['bbox_mm']))<1e-8
groups={}
for name,label in [('Placa_R1','01 - Placa radiante R1 - 2 elementos'),
                   ('Placa_R2','02 - Placa radiante R2 - 2 elementos'),
                   ('Placa_R3','03 - Placa radiante R3 - 2 elementos'),
                   ('Divisor_C08','04 - Divisor duplo 1:3 C08'),
                   ('Chicote_6','05 - Seis cabos coaxiais de 50 mm'),
                   ('Refletor','06 - Refletor aluminio 2 mm - 28,5 mm / 150 graus'),
                   ('Radome','07 - Radome FR4 2 mm - ocultar para inspecao')]:
    g=d.addObject('App::DocumentObjectGroup',name);g.Label=label;groups[name]=g
for name in original:
    o=d.getObject(name)
    if name=='Radome_FR4_2mm':g=groups['Radome']
    elif name=='Refletor_Al2mm':g=groups['Refletor']
    elif name.startswith('D_'):g=groups['Divisor_C08']
    elif any('_'+v+'_' in name for v in ['Vivo','Blindagem','PTFE']):g=groups['Chicote_6']
    else:g=groups['Placa_'+name[:2]]
    g.addObject(o)
    o.addProperty('App::PropertyString','OrigemRF','Rastreabilidade')
    o.OrigemRF='P2S13 R12; geometria nominal preservada do HFSS'
    o.setEditorMode('OrigemRF',1)
meta=d.addObject('App::FeaturePython','Dados_Montagem')
meta.Label='00 - Dados e limites da montagem PRELIMINAR'
for name,value in dict(Estado='PRELIMINAR; RF em continuacao dos passes 7/8',
    Edicao='Solidos BREP posicionados; nao e montagem cinematica nem arvore parametrica das PCBs',
    Eixos='X vertical; Y horizontal; +Z frontal',
    InterfacesPendentes='Suportes/fixadores, conectores externos N, saidas vedadas e fixacao do radome nao caracterizados',
    Radome='FR4 Isola 370HR nominal, sem cobre; fechado conforme modelo HFSS',
    Fonte=str(source_path),SHA256Fonte=sha(source_path),
    ConectoresReferencia='Amphenol 082-6784: STEP existente em projetos/P2M21/mecanica_preliminar_R18/referencias; NAO incorporado nem posicionado neste modelo RF').items():
    meta.addProperty('App::PropertyString',name,'Rastreabilidade');setattr(meta,name,value)
for name,value in dict(PassoElementos=48,PassoPlacas=96,AlturaPCB=14.949,EspessuraRefletor=2,
        InicioDobra=28.5,EspessuraRadome=2,ComprimentoCoax=50,ComprimentoRadome=314,
        LarguraRadome=84,ProfundidadeRadome=84).items():
    meta.addProperty('App::PropertyLength',name,'Dimensoes de referencia');setattr(meta,name,value);meta.setEditorMode(name,1)
meta.addProperty('App::PropertyAngle','AnguloDobra','Dimensoes de referencia');meta.AnguloDobra=150;meta.setEditorMode('AnguloDobra',1)
d.recompute()
for name,before in original.items():
    after=record(d.getObject(name))
    assert same_geometry(before,after),(name,before,after)
path=OUT/'Antena_R12_PRELIMINAR.FCStd';d.saveAs(str(path));A.closeDocument(d.Name)
d=A.openDocument(str(path))
after={name:record(d.getObject(name)) for name in original}
assert all(same_geometry(original[n],after[n]) for n in original)
assert all(x['valido'] for x in after.values())
Part.export([d.getObject(n) for n in original],str(OUT/'Antena_R12_RF.step'))
audit=dict(aprovado_geometria=True,objetos_RF=len(original),solidos_BREP=sum(x['solidos'] for x in original.values()),
    grupos=len(groups),reabertura_aprovada=True,coordenadas_inalteradas=True,fonte=str(source_path),
    fonte_sha256=sha(source_path),referencia_intersecoes=json.loads((SOURCE/'cad/intersecoes.json').read_text()),
    notas='Organizacao e aparencia; nenhum corpo fisico adicionado/removido. Solidos posicionados, sem juntas cinematicas.',
    objetos=list(original.values()))
(OUT/'conferencia_geometria.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
with (OUT/'lista_materiais.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['Item','Quantidade','Unidade','Descricao','Dimensoes','Material','Estado'])
    w.writerows([
        ['PCB-RAD',3,'un','Placa simetrica de 2 elementos; mesma M00','88 x 50 mm; core0,76mm','RO4350B / Cu35um / ENIG nominal','Geometria RF preservada'],
        ['PCB-DIV',1,'un','Divisor duplo1:3 C08','220 x 64 mm; core1,52mm','ZYF300CA-C / Cu35um / ENIG nominal','Geometria RF preservada'],
        ['COAX',6,'un','Ramais coaxiais soldados iguais','50mm; vivoR0,45975; PTFE R1,515mm','Cobre/PTFE','Geometria RF nominal; cabo comercial a confirmar'],
        ['REFLETOR',1,'un','Refletor dobrado','296mm; desenvolvido90mm; t2; ri2; inicio28,5;150graus','Al5052 nominal','Sem suportes/fixadores caracterizados'],
        ['RADOME',1,'un','Caixa fechada RF','314 x 84 x 84 mm; parede2mm','FR4 Isola370HR nominal sem cobre','Referencia RF; juntas/fixacao/vedacao pendentes'],
        ['SOLDA',1,'conjunto','Terminais soldados e PTH','Conforme modelo de cada PCB','SAC305 e cobre','Sem massa de processo definida'],
        ['N-EXT',2,'un','Conectores N externos; referencia3D Amphenol082-6784','Posicao e transicao pendentes','Conforme fabricante','Referencia nao integrada ao RF ou montagem'],
        ['FIXACAO',1,'conjunto','Apoios/fixadores e fixacao do radome','Dimensionamento pendente','A definir','Nao modelado; nao fabricar como conjunto acabado'],
    ])
A.closeDocument(d.Name)
print(json.dumps(dict(arquivo=str(path),objetos=len(original),solidos=audit['solidos_BREP'],geometria_preservada=True,reaberto=True)))
