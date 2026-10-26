# 13: Fatos de votação e comparecimento

**What to build:** As tabelas de fatos do 1º turno de 2026, no grão correto: votos por seção, votos por candidato e zona, detalhe da apuração e comparecimento/abstenção.

**Blocked by:** 12 (Dimensões de eleição e geografia)

**Status:** ready-for-agent

- [ ] Fato de votos por seção carrega de forma incremental por ano, reprocessável sem duplicar
- [ ] Fatos com grão documentado e teste de unicidade na combinação do grão
- [ ] Brancos, nulos e legenda aparecem num tipo de voto, não como candidatos
- [ ] Todas as chaves das dimensões resolvem (testes de relacionamento)
- [ ] Contratos de modelo exigidos nas tabelas finais
