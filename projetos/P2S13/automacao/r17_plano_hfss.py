# -*- coding: utf-8 -*-
"""Substituir somente refletor nativo por placa plana com os mesmos seis furos."""
import os,json,math,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P2S13_ROOT'];cfg=json.load(open(os.path.join(root,'configuracao.json')));native=os.path.join(root,cfg['native'])
def mm(v):return '%.15gmm'%v
def save(n,v):
    with open(os.path.join(root,n),'w') as f:json.dump(v,f,indent=2)
try:
    assert not os.path.exists(os.path.join(root,'geometria_plana.json'))
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign(cfg['design']);e=d.SetActiveEditor('3D Modeler')
    def sig(n):return dict(volume=float(e.GetObjectVolume(n)),bbox=list(e.GetObjectBoundingBox(n)),faces=list(e.GetFaceIDs(n)))
    before=dict((n,sig(n)) for n in e.GetObjectsInGroup('Solids') if n not in ['Refletor_Al2mm','RadiatingSurface'])
    old=sig('Refletor_Al2mm');e.Delete(['NAME:Selections','Selections:=','Refletor_Al2mm'])
    L=296.;W=90.;t=2.
    e.CreateBox(['NAME:BoxParameters','XPosition:=',mm(-L/2),'YPosition:=',mm(-W/2),'ZPosition:=',mm(-t),
        'XSize:=',mm(L),'YSize:=',mm(W),'ZSize:=',mm(t)],['NAME:Attributes','Name:=','Refletor_Al2mm','MaterialValue:=','"AL5052"','SolveInside:=',False])
    for i,pt in enumerate(cfg['portas']):
        name='Furo_'+str(i)
        e.CreateCylinder(['NAME:CylinderParameters','XCenter:=',mm(pt['x']),'YCenter:=',mm(pt['y']),'ZCenter:=','-3mm','Radius:=','2.1mm','Height:=','4mm','WhichAxis:=','Z','NumSides:=','0'],['NAME:Attributes','Name:=',name,'MaterialValue:=','"vacuum"','SolveInside:=',True])
        e.Subtract(['NAME:Selections','Blank Parts:=','Refletor_Al2mm','Tool Parts:=',name],['NAME:SubtractParameters','KeepOriginals:=',False])
    for n in before:assert sig(n)==before[n],n
    new=sig('Refletor_Al2mm');assert abs(new['volume']-(L*W*t-len(cfg['portas'])*math.pi*2.1**2*t))<1e-5
    reports=d.GetModule('ReportSetup');names=list(reports.GetAllReportNames())
    if names:reports.DeleteReports(names)
    a=d.GetModule('AnalysisSetup');assert not list(a.GetSweeps('Centro'))
    valid=d.ValidateDesign();errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2));assert valid==1 and not errors,(valid,errors)
    save('geometria_plana.json',dict(antes=old,depois=new,outros_solidos_e_faces_preservados=len(before),dimensoes_mm=[L,W,t],furos_diametro_mm=4.2,validacao=valid))
    p.SaveAs(native,True);oDesktop.CloseProject(p.GetName())
except:save('falha_geometria.json',dict(erro=traceback.format_exc()));raise
