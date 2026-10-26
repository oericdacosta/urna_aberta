# 25: Runbook e rotação de token

**What to build:** O manual de operação que permite manter o projeto sem lembrar de tudo.

**Blocked by:** 16 (Deploy e dbt docs), 18 (2º turno de 2026)

**Status:** ready-for-agent

- [ ] Passo a passo para reprocessar uma partição e tratar uma republicação do TSE
- [ ] Procedimento de rotação do PAT, com data registrada no README
- [ ] Job semanal testa o token e abre issue se falhar
- [ ] Lista de falhas conhecidas (cota, warehouse parado, inatividade do cron) e a resposta a cada uma
