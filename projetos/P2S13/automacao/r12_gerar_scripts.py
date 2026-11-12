"""Derivar scripts R12 da cadeia R11 auditada, com curvilineos e solver direto."""
from pathlib import Path
here=Path(__file__).parent
s=(here/'r11_conjunto_criar_hfss.py').read_text(encoding='utf-8-sig')
old="['NAME:GlobalCurvilinear','Apply:=',False]";assert old in s;s=s.replace(old,"['NAME:GlobalCurvilinear','Apply:=',True]")
old="'DrivenSolverType:=','Iterative Solver'";assert old in s;s=s.replace(old,"'DrivenSolverType:=','Direct Solver'")
s=s.replace("simulado=False,modo=cfg['escopo']","simulado=False,curvilinear=True,solver_type='Direct Solver',basis_order=cfg['basis_order'],modo=cfg['escopo']")
(here/'r12_criar_hfss.py').write_text(s,encoding='utf-8')
s=(here/'r11_conjunto_resolver.py').read_text(encoding='utf-8-sig')
needle="    assert 'UseAlternativeMeshMethodsAsFallBack=false' in raw"
assert needle in s
s=s.replace(needle,needle+"\n    assert \"DrivenSolverType='Direct Solver'\" in analysis\n    curv=raw.split(\"$begin 'GlobalCurvilinear'\",1)[1].split(\"$end 'GlobalCurvilinear'\",1)[0]\n    assert 'Apply=true' in curv")
(here/'r12_resolver.py').write_text(s,encoding='utf-8')
s=(here/'r11_analisar.py').read_text(encoding='utf-8-sig')
s=s.replace('R11 — antena + divisor C08 + radome FR-4 2 mm','R12 curvilinear — antena + C08 + radome FR-4 2 mm')
s=s.replace('residuo_configurado=residual_target,',"residuo_configurado=None,tipo='Direct Solver',basis_order=cfg['basis_order'],")
s=s.replace('Iterative Solver failed to converge[^\\r\\n]+','Matrix solver warning: [^\\r\\n]+')
(here/'r12_analisar.py').write_text(s,encoding='utf-8')
print('R12 scripts gerados; criacao nao resolve, resolver confere Direct/curvilinear/max6.')
