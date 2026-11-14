# P2M19 R09 — simulação suspensa, rede e montagem preliminar

Em 14/11/2026, o usuário pediu parar as simulações, registrar e interromper qualquer esgotamento de memória, enviar o resumo para gecesars@gmail.com e desenvolver em paralelo a rede divisora e a montagem no FreeCAD.

## Estado da simulação

Nenhum solver P2M19 estava ativo na inspeção. Os passes 13/14 já haviam terminado normalmente; não foi registrado um novo erro de falta de memória nessa execução. A sessão AEDT alheia PID 341520 foi preservada. A memória disponível na conferência está em [memoria_na_suspensao.json](memoria_na_suspensao.json). Não foram iniciados novos solves, sweeps, circuitos ou análises estruturais nesta etapa.

A referência congelada é [R08, 14 passes](../continuacao_72mm_ref146_14passes/README.md): ganho frontal total 20,544 dBi, H/V 22,491°/3,783°, VSWR ativo máximo 1,182; ΔS=0,010484. A estabilidade completa das nove sondas continua pendente. Esses resultados não incluem a nova distribuição externa nem as novas peças mecânicas.

## Regra permanente de memória

[Política de execução](../politica_execucao.json) e [guarda](../automacao/guard_memoria.py):

- Simulações suspensas nesta etapa. Somente um novo pedido explícito de retomada pode atualizar esse estado.
- Parar imediatamente por erro explícito de memória do solver; salvar evidência antes de encerrar exclusivamente a árvore de processos criada pela tarefa, verificando PID e horário de criação.
- Parada preventiva com menos de 512 MiB de RAM disponível ou de margem de comprometimento; também com menos de 1 GiB de RAM disponível por duas amostras consecutivas de 5 segundos. São limiares preventivos de implementação, não valores impostos pelo usuário nem critérios RF.
- Salvar data, recursos, identidade dos processos, mensagens, script e último estado/passe disponível. Criar bloqueio persistente; não repetir automaticamente nem alterar paginação ou fechar aplicativos alheios.
- Preservar os últimos resultados válidos e a malha. Caso o próprio monitor falhe, interromper o processo que ele iniciou para não deixar um solve sem monitoramento.
- Executores PowerShell históricos do projeto foram bloqueados. Arquivos congelados dos ensaios anteriores permanecem intactos. Uma nova execução autorizada deve usar o guarda e um script nativo preparado para aquela execução.

[Testes do guarda](teste_guard_memoria.json): decisões de limiares, erro OOM e leitura UTF-16, bloqueio de início, identidade de PID, encerramento de uma árvore de dois processos Python inertes e preservação de outro processo. Nenhum HFSS foi executado nem houve esgotamento real de memória durante o teste. A integração com um futuro solve deverá ser conferida na retomada autorizada.

## Comunicação

Resumo enviado para **gecesars@gmail.com**, mensagem `1a1db636cf5f699f`, com link para o commit de resultados `043950a4be0cb407459c89d137b4e9b81b0f76de`.

[Conteúdo enviado](resumo_enviado.html) · [Comprovante da ferramenta Gmail](envio_email.json).

## Planejamento e montagem preliminar

Rede proposta: uma PCB duplo 1:2 central e duas PCBs duplo 1:4 distribuídas, formando duas distribuições independentes 1:8 para oito placas C12. São 22 cabos UT-141C, com 890 mm de eixo por caminho e 5,170 m de eixos no conjunto. Os percursos finais substituem os valores iniciais de planejamento e incluem arcos; não são comprimentos de corte liberados.

A montagem parte do refletor RF 146 × 776 × 2 mm e duas colunas a 72 mm. Base separada de alumínio 146 × 70 × 4 mm, dois reforços L20 × 20 × 2 mm de 780 mm, 32 grampos POM para as oito placas e suportes das três distribuidoras. Dois N Amphenol 082-6784 ficam voltados para baixo, separados por 48 mm, em recortes Ø16,5/14 mm entre planos e rebaixos internos Ø32 × 2 mm.

- [Montagem FreeCAD, BOM, furação, dimensões e nove imagens](../mecanica_R09_PRELIMINAR/README.md).
- [Rede: topologia, interfaces das PCBs, conexões e orçamento de perdas](../rede_R09_PLANEJAMENTO/README.md).

Os 328 corpos das PCBs foram preservados geometricamente. Foram verificadas as interfaces acrescentadas, com 744 pares sem interseção volumétrica e folga mínima exata de 1,15683 mm entre cabos. A base foi exercitada por mudança dimensional e o nativo reaberto. O STEP é derivado de intercâmbio mecânico, com diferenças de integração documentadas; o FCStd permanece como referência.

A referência RF de 20,544 dBi não demonstra o ganho final desta montagem. A estimativa típica de cabo é 0,820 dB por caminho, deixando cerca de 0,724 dB para a rede externa, conectores e demais perdas antes de atingir 19 dBi. Não se executou uma nova análise de casamento nas duas entradas N. O cobre dos divisores, preparos e soldas dos cabos permanecem por detalhar e validar.

O planejamento e a montagem são preliminares; não constituem validação de RF, estrutura, vedação ou liberação de fabricação.
