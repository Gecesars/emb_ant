"""Adaptacoes rastreaveis dos scripts nativos testados para a revisao R11."""
from pathlib import Path
HERE=Path(__file__).parent
repo=HERE.parents[2]
s=(repo/'automacao/r05/enig_solido.py').read_text(encoding='utf-8-sig')
needle="            zs=[p[2] for p in coords]\n"
assert needle in s
s=s.replace(needle,needle+"            if any(all(abs(math.hypot(p[0]-q['x'],p[1]-q['y'])-q['r'])<1e-6 for p in coords) for q in record.get('skip_hole_cylinders',[])):\n                contacts.append(int(face))\n                continue\n")
(HERE/'r11_enig.py').write_text(s,encoding='utf-8')
s=(HERE/'divisor3_em_hfss.py').read_text(encoding='utf-8-sig')
s=s.replace("sys.path.insert(0,os.path.join(repo,'automacao','r05'));from enig_solido import apply", "sys.path.insert(0,os.path.join(repo,'projetos','P2S13','automacao'));from r11_enig import apply")
(HERE/'r11_divisor_hfss.py').write_text(s,encoding='utf-8')
s=(HERE/'criar_hfss.py').read_text(encoding='utf-8-sig')
s=s.replace("sys.path.insert(0,os.path.join(repo,'automacao','r05'))\nfrom enig_solido import apply", "sys.path.insert(0,os.path.join(repo,'projetos','P2S13','automacao'))\nfrom r11_enig import apply")
s=s.replace("'RO4350B_R01':(3.66,.0037)","'Isola_370HR_nominal':(cfg['radome']['er'],cfg['radome']['tand']),'RO4350B_R01':(3.66,.0037)")
s=s.replace('            criar(e,cfg)',"            reflector_cfg=dict(cfg);reflector_cfg['portas']=cfg['portas_coaxiais']\n            criar(e,reflector_cfg)")
s=s.replace("'BasisOrder:=',1", "'BasisOrder:=',cfg['basis_order']")
needle="        apply(p,d,records,os.path.join(cad,'enig_hfss.json'))"
s=s.replace(needle,"        geometry=read(os.path.join(cad,'geometria_esperada.json'));import_check={}\n        for n,geo in geometry.items():\n            bbox=[float(x) for x in e.GetObjectBoundingBox(n)];vol=float(e.GetObjectVolume(n))\n            err=max(abs(x-y) for x,y in zip(bbox,geo['bbox_mm']));ev=abs(vol-geo['volume_mm3'])/geo['volume_mm3']\n            import_check[n]=dict(bbox=bbox,volume=vol,erro_bbox_mm=err,erro_volume_rel=ev,limite_bbox_mm=.001,limite_volume_rel=.001,aprovado=err<.001 and ev<.001)\n        with open(os.path.join(root,'geometria_importada.json'),'w') as f:json.dump(import_check,f,indent=2)\n        bad_import=[n for n,q in import_check.items() if not q['aprovado']]\n        assert not bad_import,('Importacao geometria',bad_import)\n"+needle)
s=s.replace("simulado=False,modo='%d celulas PCB, %d niveis / 1 coluna; %d portas iguais, cabos50mm e refletor comum; sem rede externa'%(len(cfg['celulas']),cfg['niveis_radiadores'],len(ports))", "simulado=False,modo=cfg['escopo']")
needle="        mesh=d.GetModule('MeshSetup')"
s=s.replace(needle,"        d.GetModule('RadField').InsertInfiniteSphereSetup(['NAME:V_fino','UseCustomRadiationSurface:=',False,\n          'CSDefinition:=','Theta-Phi','Polarization:=','Linear','ThetaStart:=','-12deg','ThetaStop:=','12deg',\n          'ThetaStep:=','.01deg','PhiStart:=','0deg','PhiStop:=','0deg','PhiStep:=','1deg','UseLocalCS:=',False])\n"+needle)
s=s.replace(needle,"        d.GetModule('RadField').InsertInfiniteSphereSetup(['NAME:Potencia','UseCustomRadiationSurface:=',False,\n          'CSDefinition:=','Theta-Phi','Polarization:=','Linear','ThetaStart:=','0deg','ThetaStop:=','180deg',\n          'ThetaStep:=','2deg','PhiStart:=','0deg','PhiStop:=','360deg','PhiStep:=','2deg','UseLocalCS:=',False])\n"+needle)
(HERE/'r11_conjunto_criar_hfss.py').write_text(s,encoding='utf-8')
s=(HERE/'resolver.py').read_text(encoding='utf-8-sig').replace("'BasisOrder=1'","'BasisOrder=%s'%cfg['basis_order']")
needle="    sources(sol,ports);p.SaveAs(native,True);oDesktop.CloseProject(p.GetName())"
assert needle in s
s=s.replace(needle,"    sources(sol,ports)\n    reports.CreateReport('ALL_V_fino','Far Fields','Rectangular Plot','Centro : LastAdaptive',['Context:=','V_fino'],\n      ['Theta:=',['All'],'Phi:=',['0deg'],'Freq:=',['5170MHz']],\n      ['X Component:=','Theta','Y Component:=',['dB(RealizedGainTotal)','re(rETheta)','im(rETheta)','re(rEPhi)','im(rEPhi)']])\n    reports.ExportToFile('ALL_V_fino',os.path.join(root,'ALL_V_fino.csv'),False)\n"+needle)
s=s.replace(needle,"    try:\n        expressions=['RadiatedPower','AcceptedPower','IncidentPower','RadiationEfficiency','SystemEfficiency']\n        data=reports.GetSolutionDataPerVariation('Antenna Parameters','Centro : LastAdaptive',['Context:=','Potencia'],['Freq:=',['All']],expressions)\n        write('potencia.json',dict((q,dict(real=list(data[0].GetRealDataValues(q)),units=data[0].GetDataUnits(q))) for q in expressions))\n    except:\n        write('potencia_erro.json',dict(erro=traceback.format_exc()))\n"+needle)
(HERE/'r11_conjunto_resolver.py').write_text(s,encoding='utf-8')
print('Scripts R11 gerados')
