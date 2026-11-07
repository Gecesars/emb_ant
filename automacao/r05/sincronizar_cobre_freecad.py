"""Incorporar os sólidos de cobre do HFSS à montagem FreeCAD existente."""
import FreeCAD as App

def apply(document, copper_file, destination):
    source = App.openDocument(str(copper_file))
    shapes = {o.Label:o.Shape.copy() for o in source.Objects if o.TypeId == 'Part::Feature'}
    App.closeDocument(source.Name)
    targets = {o.Label:o for o in document.Objects if getattr(o,'MaterialHFSS',None)=='folha_cu'}
    assert set(targets)==set(shapes) and len(shapes)==138
    assert all(s.isValid() and len(s.Solids)==1 for s in shapes.values())
    for name,obj in targets.items():
        obj.Shape = shapes[name]
        if 'EspessuraCobre' not in obj.PropertiesList:
            obj.addProperty('App::PropertyLength','EspessuraCobre','RF')
        obj.EspessuraCobre = .035
    document.recompute()
    assert all(o.Shape.isValid() for o in document.Objects if hasattr(o,'Shape'))
    document.saveAs(str(destination))
    App.setActiveDocument(document.Name)
    return {'solidos_impressos':len(shapes),'volume_cobre_mm3':sum(s.Volume for s in shapes.values())}
