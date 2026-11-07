# Referência de conector N encontrada no Drive

Em 7 de novembro de 2026, foi localizado o arquivo [CONECTOR N ROSCADO.SLDPRT](https://drive.google.com/file/d/1lQ8pF3aVZ3N6o0UVY-zo1kpsPkWz5Ukj/view), na pasta `FILTRO 8P MASCARA CRITICA`. A pesquisa pela extensão do Chrome encontrou o CAD que a busca do conector Google Drive não retornava. Depois de identificar o arquivo, o conector conseguiu baixá-lo normalmente.

O SolidWorks abriu a peça sem erros ou avisos e exportou STEP sem erros ou avisos. A importação no FreeCAD e a reabertura do FCStd confirmaram um sólido válido, 55 faces e volume de 3615,177655 mm³. O comprimento é 30,30 mm; o envelope transversal mede aproximadamente 17,74 × 17,73 mm. O arquivo nativo mantém recursos de revolução, hélice e cortes; o FCStd convertido contém a geometria importada.

A seção axial mostra corpo e extensão central unidos. O arquivo não contém corpos distintos para contato central, isolante e carcaça, nem material especificado. Portanto, é uma referência mecânica de um N roscado; a compatibilidade com o cabo UT-141, a fixação e vedação na chapa de 2 mm e a equivalência ao Amphenol 082-6784 continuam sem comprovação. A geometria não deve ser atribuída integralmente a metal para representar um conector coaxial no HFSS.

Os arquivos foram organizados localmente em `D:/dev/EMBRAER/P1H/R05_Correcao/referencias_drive/`:

- `CONECTOR_N_ROSCADO.SLDPRT`: original preservado.
- `CONECTOR_N_ROSCADO.step` e `CONECTOR_N_ROSCADO.FCStd`: conversões verificadas.
- `inspecao_solidworks.json`, `inspecao_freecad.json`, `secao_conector.png`: evidências geométricas.
- `manifesto.json`: procedência e hashes dos arquivos selecionados.

Também foi inspecionado o desenho [10010152 — conector com cabo soldado](https://drive.google.com/file/d/1Q4SUPyAb3NSimNDCgWLzx2O1zeZSIaWy/view), referência Kathrein 169.3595. Ele apresenta a montagem e uma preparação de cabo de 6 mm, mas não fornece as cotas internas necessárias à simulação. O desenho [saída DP 4,9–6,1 GHz](https://drive.google.com/file/d/1YBow2k_jDv9tQDrGwtb2K48fuzK8EzsW/view) cita o N fêmea D0088, sem base, pino de 15 mm, DIV-C.47; isso identifica outra referência, sem demonstrar sua equivalência ao conector do painel.

Nenhum dos arquivos inspecionados fornece Touchstone ou perdas verificadas do conector na banda 5,09–5,25 GHz. O modelo integral R05 em execução conserva o conector nominal documentado anteriormente. Sua qualificação eletromagnética e a correlação com o componente comercial permanecem pendentes.
