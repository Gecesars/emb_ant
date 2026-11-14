# Execução de HFSS

Instrução do usuário em 14/11/2026: ao esgotar a memória do sistema ou ocorrer falta de memória no HFSS, registrar a ocorrência e parar a simulação. Nunca repetir, reiniciar, ampliar paginação ou mudar aplicativos alheios automaticamente para contornar essa parada.

Antes de qualquer solve, conferir o pedido vigente, os processos e a política de execução do projeto. Usar monitoramento ativo de memória, com evidência salva antes de encerrar apenas a árvore de processos identificada da tarefa. Registrar data, projeto/setup/passe disponível, memória física e comprometida, PIDs/identidade, mensagem do solver e ação tomada. Preservar a malha e os últimos resultados válidos. Não confundir ocupação alta de RAM com uma falha já ocorrida: distinguir parada preventiva de erro explícito de memória.

P2M19 está com novas simulações suspensas desde o pedido de 14/11/2026. A etapa corrente é documentação, planejamento da rede e CAD. Consultar `projetos/P2M19/politica_execucao.json` e `projetos/P2M19/gestao_R09/README.md`. Um pedido posterior explícito de retomar pode atualizar essa política, mantendo obrigatoriamente a parada por memória. Não executar scripts históricos para contornar a suspensão.
