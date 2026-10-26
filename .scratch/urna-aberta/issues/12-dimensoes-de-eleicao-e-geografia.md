# 12: Dimensões de eleição e geografia

**What to build:** As tabelas de referência que dão sentido aos números: eleição, cargo, partido e geografia (município, zona, seção), com o município do TSE ligado ao código IBGE.

**Blocked by:** 11 (Projeto dbt e staging de resultados)

**Status:** ready-for-agent

- [ ] O dataset de-para TSE↔IBGE é ingerido e usado na dimensão de município
- [ ] 100% dos municípios têm código IBGE (teste de cobertura)
- [ ] Dimensões de eleição, cargo, partido, zona e seção com chaves únicas
- [ ] Testes de relacionamento entre as dimensões e o staging passam
