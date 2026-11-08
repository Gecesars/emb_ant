# Conferência da malha refinada de 11 passes

**Estado em 8/11, 00:03:** a tentativa adicional com crescimento de 15% falhou por falta de memória. Foi iniciada a recuperação com 5%, descrita ao final. A solução de 21 passes continua sendo o último resultado válido; ainda não há aceite final.

Em 7/11 às 19:12, o HFSS concluiu a malha com refinamento local dos fragmentos de cobre e das soldas. Foram 11 passes, 1.580.950 tetraedros; os últimos ΔS foram 0,00740689 / 0,00680733 e as maiores mudanças de campo 0,0367667 / 0,0303877 dB. O setup cumpriu ΔS ≤ 0,008 e campo ≤ 0,05 dB por dois passes.

Com os mesmos divisores, bobinas e linhas de 290 / 132 / 133 mm, o circuito apresentou **17,3447 dBi, H = 94,3761°, V = 5,6193°**, VSWR ativo **1,22727 / 1,15010** e convencional **1,20474 / 1,23735**. Todos os valores atendem às metas, porém a mudança horizontal de **−0,82976°** em relação à malha inicial excedeu o limite interno de estabilidade de 0,5°. O ganho mudou −0,00304 dB e os VSWR menos de 0,012.

Por isso o resultado ainda não foi liberado. A continuação mantém a malha, o setup e a geometria, com critérios mais rigorosos: **ΔS ≤ 0,004, campo ≤ 0,02 dB, dois passes**, mínimo 13 e máximo 24. O solver retomou no passe 12. A comparação de estabilidade usará esta malha de 11 passes e a continuação, com os mesmos limites de 0,05 dB em ganho, 0,5° H, 0,1° V e 0,05 em ambos os VSWR; não houve relaxamento de tolerâncias.

## Histórico de reparos no g3derr

O arquivo nativo agrega 59 blocos de metadados de execuções diferentes. Os 18 avisos repetidos de Major no corpo 4550 têm **TimeStamp de 16:49:21**, anterior ao refinamento. A execução refinada começou às **18:36:29**; a malha superficial de **18:38:17** indica somente dois corpos Minor, 4550 e 7234. **Não há Major na execução refinada.**

O auditor passou a respeitar os TimeStamp de cada bloco, usando o início documentado em `malha_execucao.json`. Ele conserva a contagem histórica e não remove dados do solver. `antena_refinada1/malha.json` contém a auditoria filtrada, e `malha_agregada.json` preserva a contagem anterior sem filtro. O arquivo `circuito/comparacao_malha_inicial_refinada1.json` é o diagnóstico original, que ainda contém `reparo_major_final: 1`; esse campo foi posteriormente identificado como contagem histórica. A reprovação por diferença de H continua válida independentemente dessa correção.

Os dados convergidos, quarenta campos complexos e matrizes S desta etapa estão preservados. A ausência de Major, isoladamente, não aprova RF; falta confirmar a estabilidade com a continuação mais rigorosa, verificar o circuito Nexxim final e revisar o relatório.


## Solução rigorosa de 21 passes e verificação adicional

Às 22:14 de 7/11, a continuação convergiu em **21 passes e 5.547.337 tetraedros**, sem atingir o limite de 24. ΔS dos dois passes finais: **0,003906903 / 0,003699192**; variação máxima nas nove direções: **0,01746426 / 0,01185886 dB**. Assim, cumpriu ΔS ≤ 0,004 e campo ≤ 0,02 dB por dois passes. O resultado direto uniforme de 17,4447 dBi é distinto do ganho do painel com a rede.

No circuito completo sem atenuação dos cabos: **17,35987 dBi, H 95,94548°, V 5,61655°**, VSWR ativo **1,21237 / 1,13049**, e com outra entrada casada **1,22942 / 1,24633**. As metas de RF são atendidas. A diferença frente à malha de 11 passes foi +0,01519 dB no ganho, +1,56938° em H, −0,00279° em V e menos de 0,025 nos VSWR. H excedeu novamente a tolerância interna de estabilidade de 0,5°; não houve liberação final.

Os dados ficaram congelados em `antena_estrita21`. A verificação seguinte mantém ΔS 0,004, campo 0,02 dB, refinamento de 15%, geometria, portas e materiais. Apenas o mínimo de passes sobe a 23, com máximo 25, para confrontar a solução convergida de 21 passes com pelo menos dois passes adicionais. Os limites de comparação permanecem os mesmos. Os campos anteriores são recuperados pela referência com SHA-256, exigindo identidade dos tetraedros por passe.

A tentativa de editar o setup pelo serializador PyAEDT não aceitou o contexto do cache de campo nesta release. Foi encerrada sem modificar o nativo: o SHA-256 permaneceu idêntico ao arquivo de 21 passes. A sessão própria de inspeção foi fechada, e seu lock só foi removido após confirmar o PID encerrado. A execução seguinte usa a API nativa já validada para reconstruir as mesmas nove expressões; as mensagens informativas de que o novo cache não consegue avaliar o passe 21 decorrem da mudança de TraceID. Os campos preservados do passe 21 continuam disponíveis para a auditoria. Isso não é uma falha RF nem uma mudança do modelo.

## Falta de memória e recuperação de 8/11

Às **23:45 de 7/11**, o solver encerrou o passe adicional 22 com `SOLVER_OUT_OF_MEMORY`. Não houve novo S20 ou campo válido. A solução convergida de 21 passes, seus campos e resultados do circuito continuam preservados. O arquivo de paginação já estava disponível; não foram alteradas as opções globais de memória, licença ou programas do usuário.

Foi escolhido um crescimento de malha de **5% por passe**, em lugar de 15%, para reduzir o aumento de memória por etapa. Isso não reduz os critérios de erro: permanecem **ΔS ≤ 0,004, nove campos ≤ 0,02 dB por dois passes**, mínimo 23 / máximo 25. A comparação final continua exigindo variações de ganho ≤0,05 dB, H ≤0,5°, V ≤0,1° e ambos os VSWR ≤0,05, além de zero reparos Major. A alternativa ainda precisa concluir o cálculo e a auditoria.

Um teste em cópia sem solver demonstrou que `EditSetup` parcial altera somente mínimo/máximo de passes e percentual de refinamento. Todo o restante do bloco nativo é idêntico, incluindo os nove TraceID 672–680. Na retomada real, a mesma igualdade foi conferida após salvar e fechar o projeto. Uma primeira leitura antes do fechamento detectou conteúdo ainda não atualizado e interrompeu o script **antes de analisar**; o guard foi mantido, com a gravação confirmada após fechamento.

A recuperação iniciou em **8/11 às 00:03**, com pipeline 234268, AEDT 165852 e engine 240476, reutilizando a solução e malha de 21 passes. São identificadores históricos desta execução, a confirmar antes de qualquer intervenção. As evidências compactas estão em [recuperacao_memoria](recuperacao_memoria); os arquivos de malha continuam somente no diretório local de trabalho. O aceite final e o e-mail permanecem pendentes.

Atualização às **01:04 de 8/11**: o passe 22 concluiu às 00:39:59, com **6.357.446 tetraedros, ΔS 0,003155746 e mudança máxima de campo de 0,01008877 dB**. O passe 23 está em cálculo; a malha preparada contém **7.289.142 tetraedros**. Apesar do parâmetro nativo `PercentRefinement=5`, o crescimento efetivo foi de 14,60% e 14,66%, respectivamente. Esses números são observados nos arquivos do solver; a redução nominal não demonstra redução proporcional da malha ou do consumo de memória, e não é apresentada como causa comprovada da recuperação.

O metadado HFSS já indica `IsConverged=true` no passe 22, com três passes de ΔS atendido, mas o mínimo configurado continua sendo 23. O auditor agora exige explicitamente esse mínimo, além dos dois passes de S/campo; a solução intermediária de 22 não libera o painel. A comparação final de diagrama/VSWR e o Nexxim permanecem pendentes.
