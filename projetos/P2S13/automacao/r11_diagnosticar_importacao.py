import ScriptEnv,os,json
ScriptEnv.Initialize('Ansoft.ElectronicsDesktop')
root=os.environ['P2S13_ROOT'];cfg=json.load(open(os.path.join(root,'configuracao.json')))
p=oDesktop.OpenProject(os.path.join(root,cfg['native']));d=p.SetActiveDesign(cfg['design']);e=d.SetActiveEditor('3D Modeler')
names=['D_Substrato','D_Pino_R1_A','D_PTFE_R1_A','D_Massa_R1_A','R1_PTFE_A','R1_Blindagem_A','R1_Vivo_A','R1_PCB_RO4350B','Radome_FR4_2mm']
out=dict((n,dict(bbox=list(e.GetObjectBoundingBox(n)),volume=e.GetObjectVolume(n))) for n in names)
with open(os.path.join(root,'diagnostico_importacao.json'),'w') as f:json.dump(out,f,indent=2)
oDesktop.CloseProject(p.GetName())
