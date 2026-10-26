# 19: Candidatos 2026

**What to build:** Ingerir o cadastro de candidatos de 2026 de forma segura e ligar cada candidato aos seus votos.

**Blocked by:** 06 (Auditoria de PII nos leiames), 13 (Fatos de votação e comparecimento)

**Status:** ready-for-agent

- [ ] Nenhuma coluna de dado pessoal crua na silver: CPF, título e e-mail hasheados com sal em segredo ou descartados, conforme a auditoria
- [ ] Dimensão de candidato por eleição com grão ano e `SQ_CANDIDATO`
- [ ] Fatos de votos passam a referenciar a dimensão de candidato (relacionamento testado)
- [ ] Bens de candidatos só entram se a auditoria de PII liberar
