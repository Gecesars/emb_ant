# -*- coding: utf-8 -*-
"""Aplicar Au/NiP sobre faces expostas de cobre volumétrico, sem shell elements."""
import json
import math
import os

def apply(project,design,records,output):
    editor=design.SetActiveEditor('3D Modeler')
    boundaries=design.GetModule('BoundarySetup')
    skin=math.sqrt(1/(math.pi*5.25e9*(4*math.pi*1e-7)*5.8e7))
    groiss=1+math.exp(-(skin/(2*.5e-6))**1.6)
    conductivity=5.8e7/groiss**2
    for name,sigma in [('NiP_vol_nominal',1.5e6),('Ouro_vol_nominal',4.1e7),('Cobre_vol_Groiss',conductivity)]:
        project.GetDefinitionManager().AddMaterial(['NAME:'+name,'CoordinateSystemType:=','Cartesian',
            'BulkOrSurfaceType:=',1,['NAME:PhysicsTypes','set:=',['Electromagnetic']],
            'conductivity:=',str(sigma),'permeability:=','1'])
    assert set(records).issubset(set(editor.GetObjectsInGroup('Solids')))
    editor.AssignMaterial(['NAME:Selections','Selections:=',','.join(sorted(records))],
        ['NAME:Attributes','MaterialValue:=','"Cobre_vol_Groiss"','SolveInside:=',False])
    exposed=[]
    base=[]
    for name,record in sorted(records.items()):
        coated=[]
        substrate=[]
        for face in editor.GetFaceIDs(name):
            vertices=list(editor.GetVertexIDsFromFace(face))
            if vertices:
                zs=[float(editor.GetVertexPosition(v)[2]) for v in vertices]
            else:
                zs=[float(editor.GetFaceCenter(face)[2])]
            if all(abs(z-record['base_z_mm'])<1e-6 for z in zs):
                substrate.append(int(face))
            else:
                coated.append(int(face))
        assert coated and substrate,name
        record['faces_ENIG']=coated
        record['faces_Cu_substrato']=substrate
        exposed.extend(coated)
        base.extend(substrate)
    boundaries.AssignLayeredImp(['NAME:ENIG_faces_expostas','Faces:=',exposed,
        'Frequency:=','0GHz','Roughness:=','0um','IsTwoSided:=',False,'IsShellElement:=',False,
        ['NAME:Layers',['NAME:Layer1','Thickness:=','.0254um','Material:=','Ouro_vol_nominal'],
         ['NAME:Layer2','Thickness:=','4.5um','Material:=','NiP_vol_nominal'],
         ['NAME:Layer3','LayerType:=','Infinite','Material:=','Cobre_vol_Groiss']],
        'InfGroundPlane:=',False])
    with open(output,'w') as stream:
        json.dump(dict(objetos=records,faces_ENIG=len(exposed),faces_Cu_substrato=len(base),
            condutividade_Cu_Sm=conductivity,Cu_um=35,NiP_um=4.5,Au_um=.0254,
            metodo='Cobre geometrico, solve inside falso; Au/NiP sobre superficie exposta. Base condutora semi-infinita pois 35um excede muitas profundidades de penetracao.'),stream,indent=2)
