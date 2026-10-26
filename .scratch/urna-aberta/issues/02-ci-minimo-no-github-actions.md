# 02: CI mínimo no GitHub Actions

**What to build:** Todo pull request roda lint e testes automaticamente e falha se algo quebrar.

**Blocked by:** 01 (Esqueleto do repositório)

**Status:** ready-for-agent

- [ ] Workflow de CI roda ruff, formatação e pytest em jobs paralelos
- [ ] PR com lint quebrado falha o CI
- [ ] CI termina em até 5 min com cache de dependências
- [ ] Dependabot semanal e secret scanning ativados
