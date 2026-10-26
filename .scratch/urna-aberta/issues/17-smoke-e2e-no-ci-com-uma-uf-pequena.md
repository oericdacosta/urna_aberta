# 17: Smoke E2E no CI com uma UF pequena

**What to build:** Cada PR relevante prova que o pipeline inteiro funciona, do download à tabela final, usando só o Acre.

**Blocked by:** 10 (Workflow de ingestão), 13 (Fatos de votação e comparecimento)

**Status:** ready-for-agent

- [ ] Teste ponta a ponta com o Acre roda no CI em menos de 15 min
- [ ] Falha em qualquer etapa (download, bronze, dbt) falha o CI
- [ ] Usa schema isolado por PR e limpa depois
- [ ] Não estoura a cota do Databricks nem dos runners
