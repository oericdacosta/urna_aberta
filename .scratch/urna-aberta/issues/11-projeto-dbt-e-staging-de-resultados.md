# 11: Projeto dbt e staging de resultados

**What to build:** Um projeto dbt conectado ao Databricks que transforma o bronze de resultados em tabelas tipadas e consistentes, tratando os nulos especiais do TSE sem perder informação.

**Blocked by:** 09 (Carga bronze genérica)

**Status:** ready-for-agent

- [ ] Conexão parametrizada por ambiente (dev, ci, prod) via variáveis
- [ ] Staging de votação por seção, por candidato/zona e de detalhe da apuração, com tipos corretos
- [ ] Valores especiais viram NULL e o código original fica numa coluna auxiliar
- [ ] Testes de unicidade e não-nulo nas chaves; chave de candidato inclui ano e turno
- [ ] CI roda `dbt parse` e `dbt build` incremental de PR em schema próprio, apagado ao fechar o PR
