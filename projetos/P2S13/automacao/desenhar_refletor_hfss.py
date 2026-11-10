# -*- coding: utf-8 -*-
"""Refletor identico ao CAD, criado com primitivas nativas do HFSS."""
import math

def mm(x):return '%.15gmm'%x

def criar(editor,cfg):
    e=editor
    assert 0<cfg['angulo_dobra_graus']<180,'Usar a caixa plana original quando angulo=0.'
    b=cfg['inicio_dobra_y_mm'];a=math.radians(cfg['angulo_dobra_graus']);ri=cfg['raio_interno_mm'];t=cfg['espessura_mm'];ro=ri+t;L=cfg['refletor_comprimento_mm']
    tail=cfg['refletor_desenvolvido_largura_mm']/2-b-a*(ri+cfg['K_dobra']*t)
    O=lambda v:(b+ro*math.sin(v),-ro+ro*math.cos(v))
    I=lambda v:(b+ri*math.sin(v),-ro+ri*math.cos(v))
    extend=lambda yz:(yz[0]+tail*math.cos(a),yz[1]-tail*math.sin(a))
    mirror=lambda yz:(-yz[0],yz[1])
    o0,om,o1=O(0),O(a/2),O(a);i0,im,i1=I(0),I(a/2),I(a);ot,it=extend(o1),extend(i1)
    yz=[mirror(ot),mirror(o1),mirror(om),mirror(o0),o0,om,o1,ot,it,i1,im,i0,mirror(i0),mirror(im),mirror(i1),mirror(it),mirror(ot)]
    pts=['NAME:PolylinePoints']+[['NAME:PLPoint','X:=',mm(-L/2),'Y:=',mm(y),'Z:=',mm(z)] for y,z in yz]
    segments=['NAME:PolylineSegments']
    for start,typ,count in [(0,'Line',2),(1,'Arc',3),(3,'Line',2),(4,'Arc',3),(6,'Line',2),(7,'Line',2),(8,'Line',2),(9,'Arc',3),(11,'Line',2),(12,'Arc',3),(14,'Line',2),(15,'Line',2)]:
        segments.append(['NAME:PLSegment','SegmentType:=',typ,'StartIndex:=',start,'NoOfPoints:=',count,'NoOfSegments:=',0])
    e.CreatePolyline(['NAME:PolylineParameters','IsPolylineCovered:=',True,'IsPolylineClosed:=',True,pts,segments,
      ['NAME:PolylineXSection','XSectionType:=','None','XSectionOrient:=','Auto','XSectionWidth:=','0mm','XSectionTopWidth:=','0mm','XSectionHeight:=','0mm','XSectionNumSegments:=','0','XSectionBendType:=','Corner']],
      ['NAME:Attributes','Name:=','Refletor_Al2mm','MaterialValue:=','"AL5052"','SolveInside:=',False])
    e.SweepAlongVector(['NAME:Selections','Selections:=','Refletor_Al2mm','NewPartsModelFlag:=','Model'],
      ['NAME:VectorSweepParameters','DraftAngle:=','0deg','DraftType:=','Round','CheckFaceFaceIntersection:=',False,'SweepVectorX:=',mm(L),'SweepVectorY:=','0mm','SweepVectorZ:=','0mm'])
    for k,pt in enumerate(cfg['portas']):
        n='Furo_Cabo_'+str(k)
        e.CreateCylinder(['NAME:CylinderParameters','XCenter:=',mm(pt['x']),'YCenter:=',mm(pt['y']),'ZCenter:=','-100mm','Radius:=','2.1mm','Height:=','120mm','WhichAxis:=','Z','NumSides:=','0'],
          ['NAME:Attributes','Name:=',n,'MaterialValue:=','"vacuum"','SolveInside:=',True])
        e.Subtract(['NAME:Selections','Blank Parts:=','Refletor_Al2mm','Tool Parts:=',n],['NAME:SubtractParameters','KeepOriginals:=',False])
    return yz
