# -*- coding: utf-8 -*-
"""Aplicar Cu/NiP/Au orientado, conferindo a normal importada no AEDT."""
import json
import math
import os


def apply(project,design,cad,boundary_name):
    faces=json.load(open(os.path.join(cad,"enig_faces.json")))
    editor=design.SetActiveEditor("3D Modeler")
    boundaries=design.GetModule("BoundarySetup")
    assert set(faces).issubset(set(editor.GetObjectsInGroup("Sheets")))
    skin=math.sqrt(1/(math.pi*5.25e9*(4*math.pi*1e-7)*5.8e7))
    correction=1+math.exp(-(skin/(2*.5e-6))**1.6)
    conductivity=5.8e7/correction**2
    materials=[("NiP_estimado",1.5e6),("Ouro_nom",4.1e7),("Cobre_Groiss_equivalente",conductivity)]
    for name,value in materials:
        project.GetDefinitionManager().AddMaterial(["NAME:"+name,"CoordinateSystemType:=","Cartesian",
            "BulkOrSurfaceType:=",1,["NAME:PhysicsTypes","set:=",["Electromagnetic"]],
            "conductivity:=",str(value),"permeability:=","1"])
    groups={True:[],False:[]}
    for name,item in sorted(faces.items()):
        before=set(editor.GetObjectsInGroup("Sheets"))
        editor.DuplicateAlongLine(["NAME:Selections","Selections:=",name,"NewPartsModelFlag:=","Model"],
            ["NAME:DuplicateToAlongLineParameters","CreateNewObjects:=",True,
             "XComponent:=","0mm","YComponent:=","0mm","ZComponent:=","100mm","Numclones:=","2"],
            ["NAME:Options","DuplicateAssignments:=",False])
        copies=set(editor.GetObjectsInGroup("Sheets"))-before
        assert len(copies)==1,name
        probe=list(copies)[0]
        editor.ThickenSheet(["NAME:Selections","Selections:=",probe,"NewPartsModelFlag:=","Model"],
            ["NAME:SheetThickenParameters","Thickness:=","1mm","BothSides:=",False])
        bounds=[float(value) for value in editor.GetObjectBoundingBox(probe)]
        positions=[bounds[2],bounds[5]]
        assert abs(max(positions)-min(positions)-1)<1e-6,name
        normal=1 if max(positions)>item["z_mm"]+100.5 else -1
        editor.Delete(["NAME:Selections","Selections:=",probe])
        item["normal_hfss"]=normal
        groups[normal==item["exposto"]].append(name)
    boundaries.DeleteBoundaries([boundary_name])
    for first,objects in groups.items():
        if not objects:continue
        layers=[("Ouro_nom",".0254um"),("NiP_estimado","4.5um"),("Cobre_Groiss_equivalente","35um")]
        if not first:layers.reverse()
        data=["NAME:Layers"]+[["NAME:Layer%d"%(i+1),"Thickness:=",thick,"Material:=",mat]
            for i,(mat,thick) in enumerate(layers)]
        boundaries.AssignLayeredImp(["NAME:ENIG_"+("direto" if first else "inverso"),"Objects:=",objects,
            "Frequency:=","0GHz","Roughness:=","0um","IsTwoSided:=",True,"IsShellElement:=",True,
            data,"InfGroundPlane:=",False])
    with open(os.path.join(cad,"enig_hfss.json"),"w") as stream:
        json.dump(dict(faces=faces,materiais_condutividade_Sm=materials,ni_um=4.5,au_um=.0254,
            cobre_um=35,rugosidade_cobre_um=.5,groiss_frequencia_limite_GHz=5.25),stream,indent=2)
