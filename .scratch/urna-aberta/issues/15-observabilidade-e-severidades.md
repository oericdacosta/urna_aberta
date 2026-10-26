# 15: Observabilidade e severidades

**What to build:** Cada execução deixa rastro e as falhas chegam até você com a gravidade certa.

**Blocked by:** 10 (Workflow de ingestão), 14 (Reconciliação e golden do 1º turno)

**Status:** ready-for-agent

- [ ] Tabela de execuções registra workflow, arquivo, hash, linhas lidas/escritas/rejeitadas, versão do código e status
- [ ] Checks de volume: variação acima de ±5% em turno fechado alerta; zero linhas falha
- [ ] Severidades P1, P2 e P3 aplicadas nos testes do dbt (erro versus aviso) com falhas armazenadas
- [ ] Linhas rejeitadas vão para quarentena e nunca são descartadas
- [ ] Falha forçada de teste gera a issue de alerta
