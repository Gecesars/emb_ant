"""Executar na GUI FreeCAD: vistas tecnicas reproduziveis sem editar a fonte."""
import math
from pathlib import Path
import FreeCAD as App,FreeCADGui as Gui

ROOT=Path('D:/dev/EMBRAER/P1H/R06_sem_cabos')
REPO=Path('D:/dev/EMBRAER/emb_ant')
OUTPUT=ROOT/'imagens';OUTPUT.mkdir(exist_ok=True)

def render(filename,target,angle,height,width=1800,pxheight=1200):
    view=Gui.activeDocument().activeView()
    rot=App.Rotation(App.Vector(1,0,0),angle)
    pos=App.Vector(*target)+rot.multVec(App.Vector(0,0,1000))
    view.setCamera('#Inventor V2.1 ascii\nOrthographicCamera { viewportMapping ADJUST_CAMERA '
      'position %g %g %g orientation 1 0 0 %g nearDistance 1 farDistance 2000 '
      'aspectRatio 1 focalDistance 1000 height %g }'%(pos.x,pos.y,pos.z,math.radians(angle),height))
    Gui.updateGui();view.saveImage(str(OUTPUT/filename),width,pxheight,'White')

def visible(doc,predicate):
    for obj in doc.Objects:obj.ViewObject.Visibility=predicate(obj.Name)
    Gui.updateGui()

doc=App.getDocument('R06_Imagens_Montagem')
if doc is None:doc=App.openDocument(str(OUTPUT/'Montagem_visual.FCStd'))
App.setActiveDocument(doc.Name)
visible(doc,lambda n:True)
render('montagem_frontal.png',(-15,0,-15),30,190,2400,800)
render('montagem_traseira.png',(-15,0,-15),150,235,2400,1000)
render('base_conectores.png',(-263,0,-20),50,115,1800,1400)
render('apoio_passagem.png',(-52.6,0,2),65,58)
render('suporte_pom_5mm.png',(-105.2,0,9),55,48,1500,1200)
render('fixacao_divisor.png',(134,0,-15),145,100,1500,1200)
visible(doc,lambda n:n.startswith(('Rogers','Ant','Via')))
render('pcb_continua_superior.png',(0,0,17.4),0,44,2600,220)
render('pcb_continua_inferior.png',(0,0,16.6),180,44,2600,220)
render('elemento_superior.png',(-26.3,0,17.4),0,32)
render('elemento_inferior.png',(-26.3,0,16.6),180,32)
for side in ['Inferior','Superior']:
    visible(doc,lambda n:side in n and n.startswith(('PCB_','Pad_','Massa_','Estrela_')))
    b=doc.getObject('PCB_'+side).Shape.BoundBox
    center=((b.XMin+b.XMax)/2,0,-10)
    w,h=(2200,900) if side=='Inferior' else (900,1400)
    render('divisor_'+side.lower()+'_superior.png',center,0,86,w,h)
    render('divisor_'+side.lower()+'_inferior.png',center,180,86,w,h)
visible(doc,lambda n:n=='Refletor_R05')
render('refletor_dobrado.png',(-9,0,-14),35,185,2500,850)
flat=App.openDocument(str(REPO/'freecad/mecanica_R05/02_Refletor_planificado.FCStd'))
App.setActiveDocument(flat.Name)
for item in flat.Objects:
    item.ViewObject.Visibility=item.Name=='Chapa_plana'
    if hasattr(item,'Shape'):
        item.ViewObject.ShapeColor=(.72,.75,.78)
        item.ViewObject.LineColor=(.12,.15,.18)
Gui.updateGui()
render('refletor_planificado.png',(-34.7,0,1),0,202,2500,850)
App.closeDocument(flat.Name);App.setActiveDocument(doc.Name)
coil=App.openDocument(str(ROOT.parent/'R05_Correcao/cupons/Bobina_r090/Bobina_r090.FCStd'))
visible(coil,lambda n:True)
coil.getObject('Linha_e_bobina').ViewObject.ShapeColor=(.82,.48,.13)
coil.getObject('Dieletrico').ViewObject.ShapeColor=(.9,.92,.9)
coil.getObject('Dieletrico').ViewObject.Transparency=65
App.setActiveDocument(coil.Name)
render('bobina_dc.png',(2.509168,-19.25,-10),65,16,1400,1400)
App.closeDocument(coil.Name);App.setActiveDocument(doc.Name)
visible(doc,lambda n:True)
Gui.activeDocument().activeView().viewAxonometric();Gui.activeDocument().activeView().fitAll()
print('IMAGENS_R06_OK')
