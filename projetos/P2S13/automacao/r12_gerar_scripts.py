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
s=s.replace('solucao integral R11','solucao integral R12')
s=s.replace("residual_target=float(re.search(r'IterativeResidual=([\\d.eE+-]+)',native)[1])", """assert "DrivenSolverType='Direct Solver'" in native
assert int(re.search(r'BasisOrder=(\\d+)',native)[1])==cfg['basis_order']==1
curvilinear=re.search(r"\\$begin 'GlobalCurvilinear'(.*?)\\$end 'GlobalCurvilinear'",native,re.S)[1]
assert 'Apply=true' in curvilinear""")
s=s.replace('R11 — antena + divisor C08 + radome FR-4 2 mm','R12 curvilinear — antena + C08 + radome FR-4 2 mm')
s=s.replace('residuo_configurado=residual_target,',"residuo_configurado=None,tipo='Direct Solver',basis_order=cfg['basis_order'],")
s=s.replace('Iterative Solver failed to converge[^\\r\\n]+','Matrix solver warning: [^\\r\\n]+')
s=s.replace("    ax.set_title('%s: largura %.2f° | pico %+.2f°'%(axis,cuts[axis]['abertura_graus'],cuts[axis]['pico_graus']),pad=20)",
    "    peak=peak_interp if axis=='V' else cuts[axis]['pico_graus']\n    ax.set_title('%s: largura %.2f° | pico %+.3f°'%(axis,cuts[axis]['abertura_graus'],peak),pad=20)")
s=s.replace("    fig.text(.5,.84,'SOLUÇÃO INVÁLIDA — curvas apenas para diagnóstico',ha='center',color='firebrick',weight='bold')",
    "    fig.text(.5,.84,'SOLUÇÃO INVÁLIDA — curvas apenas para diagnóstico',ha='center',color='firebrick',weight='bold')\nelif not converged:\n    fig.text(.5,.84,'PRELIMINAR — malha não convergida',ha='center',color='darkorange',weight='bold')")
s=s.replace("    fig.suptitle('SOLUÇÃO INVÁLIDA — apenas diagnóstico',color='firebrick',weight='bold')",
    "    fig.suptitle('SOLUÇÃO INVÁLIDA — apenas diagnóstico',color='firebrick',weight='bold')\nelif not converged:\n    fig.suptitle('PRELIMINAR — 5,17 GHz | entradas 0,5 W / 0° | malha não convergida',color='darkorange')")
(here/'r12_analisar.py').write_text(s,encoding='utf-8')
print('R12 scripts gerados; criacao nao resolve, resolver confere Direct/curvilinear/max6.')
