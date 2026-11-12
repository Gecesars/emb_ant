# -*- coding: utf-8 -*-
"""AEDT nativo: acrescentar apenas um tubo cilindrico a uma copia sem resultados."""
import os,json,math,traceback
import ScriptEnv
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P2S13_ROOT'];cfg=json.load(open(os.path.join(root,'configuracao.json')))
t=cfg['radome'];native=os.path.join(root,cfg['native'])
def mm(v):return '%.12gmm'%v
def write(n,v):
    with open(os.path.join(root,n),'w') as f:json.dump(v,f,indent=2)
try:
    assert not os.path.exists(os.path.join(root,'tubo_criado.json'))
    p=oDesktop.OpenProject(native);d=p.SetActiveDesign(cfg['design']);e=d.SetActiveEditor('3D Modeler')
    names=list(e.GetObjectsInGroup('Solids'));assert 'Tubo_PVC' not in names
    def sig(n):return dict(volume=float(e.GetObjectVolume(n)),bbox=[float(x) for x in e.GetObjectBoundingBox(n)])
    before=dict((n,sig(n)) for n in names if n!='RadiatingSurface')
    reports=d.GetModule('ReportSetup');old=list(reports.GetAllReportNames())
    if old:reports.DeleteReports(old)
    p.GetDefinitionManager().AddMaterial(['NAME:'+t['material'],'CoordinateSystemType:=','Cartesian','BulkOrSurfaceType:=',1,
        ['NAME:PhysicsTypes','set:=',['Electromagnetic']],'permittivity:=',str(t['er']),'dielectric_loss_tangent:=',str(t['tand'])])
    for n,r in [('Tubo_PVC',t['De_mm']/2),('Vazio_Tubo',t['Di_mm']/2)]:
        e.CreateCylinder(['NAME:CylinderParameters','XCenter:=',mm(-t['comprimento_mm']/2),'YCenter:=','0mm',
            'ZCenter:=',mm(cfg['pipe_center_z_local_mm']),'Radius:=',mm(r),'Height:=',mm(t['comprimento_mm']),'WhichAxis:=','X','NumSides:=','0'],
            ['NAME:Attributes','Name:=',n,'MaterialValue:=','"'+t['material']+'"','SolveInside:=',True,'Color:=','(210 220 230)','Transparency:=',.65])
    e.Subtract(['NAME:Selections','Blank Parts:=','Tubo_PVC','Tool Parts:=','Vazio_Tubo'],['NAME:SubtractParameters','KeepOriginals:=',False])
    after=dict((n,sig(n)) for n in before)
    for n in before:
        assert abs(before[n]['volume']-after[n]['volume'])<1e-7,(n,'volume')
        assert max(abs(x-y) for x,y in zip(before[n]['bbox'],after[n]['bbox']))<1e-6,(n,'bbox')
    ts=sig('Tubo_PVC');vol=math.pi*((t['De_mm']/2)**2-(t['Di_mm']/2)**2)*t['comprimento_mm']
    assert abs(ts['volume']-vol)/vol<1e-8
    # Auto-open region must enclose the expanded model after cylinder creation.
    region=sig('RadiatingSurface')['bbox'];tb=ts['bbox']
    assert all(region[i]<tb[i] and region[i+3]>tb[i+3] for i in range(3)),(region,tb)
    a=d.GetModule('AnalysisSetup');assert list(a.GetSetups())==['Centro'] and not list(a.GetSweeps('Centro'))
    valid=d.ValidateDesign();errors=list(oDesktop.GetMessages(p.GetName(),d.GetName(),2));assert valid==1 and not errors,(valid,errors)
    write('tubo_criado.json',dict(objetos_anteriores=len(before),objetos_preservados=True,tubo=ts,volume_teorico_mm3=vol,
        bbox_regiao_mm=region,validacao=valid,erros=errors,material=t,sem_cabos_3D=True))
    p.SaveAs(native,True);oDesktop.CloseProject(p.GetName())
except:
    write('falha_tubo.json',dict(erro=traceback.format_exc()));raise
